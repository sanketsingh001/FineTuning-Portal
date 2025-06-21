import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import json
from datetime import datetime

import ffmpeg
import soundfile as sf
import numpy as np
from pydub import AudioSegment
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.base import SessionLocal
from app.models.models import Call, Chunk, CallStatus, ChunkStatus, SpeakerRole
from app.tasks.celery_app import celery_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Whisper model (lazy-loaded)
_whisper_model = None
def get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(
            settings.WHISPER_MODEL,
            device=settings.WHISPER_DEVICE,
            compute_type="float16"
        )
    return _whisper_model

# Initialize diarization pipeline (lazy-loaded)
_diarization_pipeline = None
def get_diarization_pipeline():
    global _diarization_pipeline
    if _diarization_pipeline is None:
        _diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=None  # Add your Hugging Face token if needed
        )
    return _diarization_pipeline

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def convert_audio(input_path: str, output_path: str) -> bool:
    """Convert audio to 16kHz mono WAV format."""
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Use ffmpeg to convert audio
        (
            ffmpeg
            .input(input_path)
            .output(
                output_path,
                ac=1,  # mono
                ar=settings.AUDIO_SAMPLE_RATE,
                acodec='pcm_s16le',
                loglevel='error'
            )
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        return True
    except ffmpeg.Error as e:
        logger.error(f"FFmpeg error: {e.stderr.decode()}")
        return False

def split_audio(
    input_path: str,
    output_dir: str,
    max_duration: int = 30,
    min_silence_len: int = 500,
    silence_thresh: int = -40
) -> List[Dict[str, Any]]:
    """Split audio into chunks of max_duration seconds at points of silence."""
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Load audio file
        audio = AudioSegment.from_file(input_path)
        
        # Normalize audio
        audio = audio.normalize()
        
        # Split on silence
        chunks = []
        chunk_start = 0
        chunk_num = 0
        
        while chunk_start < len(audio):
            # Calculate chunk end
            chunk_end = min(chunk_start + (max_duration * 1000), len(audio))
            
            # If this isn't the last chunk, try to split at silence
            if chunk_end < len(audio):
                # Find silence in the last 5 seconds of the chunk
                search_start = max(chunk_start, chunk_end - 5000)
                search_segment = audio[search_start:chunk_end]
                
                # Split at silence if found
                silence_ranges = detect_silence(
                    search_segment,
                    min_silence_len=min_silence_len,
                    silence_thresh=silence_thresh
                )
                
                if silence_ranges:
                    # Use the first silence gap found
                    silence_start = silence_ranges[0][0]
                    chunk_end = search_start + silence_start
            
            # Extract chunk
            chunk = audio[chunk_start:chunk_end]
            
            # Skip very short chunks
            if len(chunk) < 1000:  # Less than 1 second
                chunk_start = chunk_end
                continue
            
            # Save chunk
            chunk_path = os.path.join(output_dir, f"chunk_{chunk_num:04d}.wav")
            chunk.export(chunk_path, format="wav")
            
            chunks.append({
                'path': chunk_path,
                'start_time': chunk_start / 1000.0,  # Convert to seconds
                'end_time': chunk_end / 1000.0,      # Convert to seconds
                'duration': (chunk_end - chunk_start) / 1000.0  # in seconds
            })
            
            chunk_start = chunk_end
            chunk_num += 1
        
        return chunks
    except Exception as e:
        logger.error(f"Error splitting audio: {str(e)}")
        return []

def detect_silence(audio_segment, min_silence_len=500, silence_thresh=-40):
    """Detect silent chunks in audio segment."""
    # Convert to numpy array if needed
    if not isinstance(audio_segment, AudioSegment):
        samples = np.array(audio_segment.get_array_of_samples())
    else:
        samples = np.array(audio_segment.get_array_of_samples())
    
    # Normalize samples to -1.0 to 1.0
    if audio_segment.sample_width == 2:
        samples = samples.astype(np.float32) / 32768.0
    elif audio_segment.sample_width == 4:
        samples = samples.astype(np.float32) / 2147483648.0
    
    # Calculate dBFS
    dbfs = 20 * np.log10(np.abs(samples) + 1e-6)  # Add small value to avoid log(0)
    
    # Find silent regions
    silent_ranges = []
    in_silence = False
    silence_start = 0
    
    for i, db in enumerate(dbfs):
        if db < silence_thresh and not in_silence:
            in_silence = True
            silence_start = i
        elif db >= silence_thresh and in_silence:
            in_silence = False
            if (i - silence_start) >= min_silence_len * audio_segment.frame_rate / 1000.0:
                silent_ranges.append([silence_start, i])
    
    # Handle case where audio ends in silence
    if in_silence and (len(dbfs) - silence_start) >= min_silence_len * audio_segment.frame_rate / 1000.0:
        silent_ranges.append([silence_start, len(dbfs)])
    
    return silent_ranges

def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio using Whisper."""
    try:
        model = get_whisper_model()
        segments, _ = model.transcribe(
            audio_path,
            language="hi",  # Default to Hindi, can be made configurable
            beam_size=5,
            vad_filter=True
        )
        
        # Combine all segments into a single text
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    except Exception as e:
        logger.error(f"Error transcribing audio: {str(e)}")
        return ""

def process_call(call_id: int):
    """Process a call: split into chunks and transcribe each chunk."""
    db = next(get_db())
    
    try:
        # Get call from database
        call = db.query(Call).filter(Call.id == call_id).first()
        if not call:
            logger.error(f"Call with ID {call_id} not found")
            return False
        
        # Update call status
        call.status = CallStatus.PROCESSING
        db.commit()
        
        # Create processed directory
        processed_dir = os.path.join(settings.PROCESSED_DIR, str(call_id))
        os.makedirs(processed_dir, exist_ok=True)
        
        # Convert audio to WAV if needed
        input_path = call.file_path
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        wav_path = os.path.join(processed_dir, f"{base_name}.wav")
        
        if not convert_audio(input_path, wav_path):
            raise Exception("Failed to convert audio file")
        
        # Split audio into chunks
        chunks_dir = os.path.join(settings.CHUNKS_DIR, str(call_id))
        chunks = split_audio(wav_path, chunks_dir)
        
        # Process each chunk
        for chunk_info in chunks:
            # Transcribe chunk
            transcription = transcribe_audio(chunk_info['path'])
            
            # Create chunk record
            chunk = Chunk(
                call_id=call.id,
                file_path=chunk_info['path'],
                start_time=chunk_info['start_time'],
                end_time=chunk_info['end_time'],
                duration=chunk_info['duration'],
                original_text=transcription,
                status=ChunkStatus.PENDING,
                speaker_role=SpeakerRole.UNKNOWN
            )
            db.add(chunk)
        
        # Update call status
        call.status = CallStatus.PROCESSED
        db.commit()
        return True
        
    except Exception as e:
        logger.error(f"Error processing call {call_id}: {str(e)}")
        if 'call' in locals():
            call.status = CallStatus.FAILED
            db.commit()
        return False
    finally:
        db.close()

@celery_app.task(bind=True, name="process_call_task")
def process_call_task(self, call_id: int):
    """Celery task to process a call."""
    return process_call(call_id)

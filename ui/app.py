import os
import gradio as gr
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# API configuration
API_BASE_URL = "http://localhost:8000/api/v1"

# Cache for storing call and chunk data
calls_cache = {}
current_call_id = None
current_chunk_index = 0

# Helper functions
def get_auth_headers():
    # In a real app, get this from login
    return {"Authorization": "Bearer your_jwt_token_here"}

def fetch_calls() -> List[Dict]:
    """Fetch list of calls from the API."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/uploads/",
            headers=get_auth_headers()
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def fetch_call_chunks(call_id: int) -> List[Dict]:
    """Fetch chunks for a specific call."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/chunks/",
            params={"call_id": call_id},
            headers=get_auth_headers()
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching chunks: {e}")
        return []

def update_chunk(chunk_id: int, corrected_text: str, speaker_role: str, status: str) -> bool:
    """Update a chunk with corrected text and metadata."""
    try:
        response = requests.patch(
            f"{API_BASE_URL}/chunks/{chunk_id}",
            json={
                "corrected_text": corrected_text,
                "speaker_role": speaker_role,
                "status": status
            },
            headers=get_auth_headers()
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"Error updating chunk: {e}")
        return False

def upload_audio(file_path: str) -> Optional[Dict]:
    """Upload an audio file for processing."""
    try:
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "audio/wav")}
            response = requests.post(
                f"{API_BASE_URL}/uploads/",
                files=files,
                headers=get_auth_headers()
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error uploading file: {e}")
        return None

# UI Components
def create_upload_tab():
    """Create the upload tab UI."""
    with gr.Blocks() as upload_tab:
        gr.Markdown("## Upload Call Recordings")
        
        with gr.Row():
            audio_input = gr.Audio(
                label="Upload Audio File",
                type="filepath",
                interactive=True
            )
        
        with gr.Row():
            upload_btn = gr.Button("Process Audio", variant="primary")
        
        status_output = gr.Textbox(
            label="Status",
            interactive=False,
            placeholder="Upload and processing status will appear here..."
        )
        
        def process_audio(audio_path):
            if not audio_path:
                return "Error: No audio file provided"
            
            try:
                result = upload_audio(audio_path)
                if result:
                    return f"Success! Call ID: {result.get('id')} - {result.get('status')}"
                else:
                    return "Error processing audio"
            except Exception as e:
                return f"Error: {str(e)}"
        
        upload_btn.click(
            fn=process_audio,
            inputs=audio_input,
            outputs=status_output
        )
    
    return upload_tab

def create_review_tab():
    """Create the review tab UI."""
    with gr.Blocks() as review_tab:
        gr.Markdown("## Review Transcripts")
        
        with gr.Row():
            # Call selection
            call_dropdown = gr.Dropdown(
                label="Select Call",
                choices=[],
                interactive=True
            )
            
            refresh_btn = gr.Button("🔄", variant="secondary")
        
        with gr.Row():
            # Audio player and transcript
            with gr.Column(scale=2):
                audio_player = gr.Audio(
                    label="Audio Chunk",
                    interactive=False,
                    type="filepath"
                )
                
                with gr.Row():
                    prev_btn = gr.Button("⬅ Previous")
                    next_btn = gr.Button("Next ➡")
                    
                chunk_info = gr.Textbox(
                    label="Chunk Info",
                    interactive=False,
                    max_lines=2
                )
            
            with gr.Column(scale=3):
                original_text = gr.Textbox(
                    label="Original Transcription",
                    interactive=False,
                    lines=5
                )
                
                corrected_text = gr.Textbox(
                    label="Corrected Text",
                    interactive=True,
                    lines=5,
                    placeholder="Make corrections here..."
                )
                
                speaker_radio = gr.Radio(
                    label="Speaker Role",
                    choices=["agent", "customer", "unknown"],
                    value="unknown"
                )
                
                status_radio = gr.Radio(
                    label="Status",
                    choices=["pending", "reviewed", "approved"],
                    value="pending"
                )
                
                save_btn = gr.Button("Save Changes", variant="primary")
        
        # State variables
        current_chunk = gr.State(None)
        chunks_list = gr.State([])
        
        # Event handlers
        def refresh_calls():
            calls = fetch_calls()
            choices = [(f"{c['id']}: {c['original_filename']}", c['id']) for c in calls]
            return gr.Dropdown(choices=choices)
        
        def load_chunks(call_id):
            if not call_id:
                return [], [], "", "", "unknown", "pending", None
                
            chunks = fetch_call_chunks(call_id)
            if not chunks:
                return [], [], "", "", "unknown", "pending", None
                
            chunk = chunks[0]
            return (
                chunks,
                chunks[0]["file_path"],
                chunk["original_text"] or "",
                chunk["corrected_text"] or "",
                chunk["speaker_role"].lower(),
                chunk["status"].lower(),
                chunk
            )
        
        def update_chunk_display(chunks, index):
            if not chunks or index < 0 or index >= len(chunks):
                return "", "", "unknown", "pending", None, "No more chunks"
                
            chunk = chunks[index]
            return (
                chunk["file_path"],
                chunk["original_text"] or "",
                chunk["speaker_role"].lower(),
                chunk["status"].lower(),
                chunk,
                f"Chunk {index + 1} of {len(chunks)}"
            )
        
        def save_changes(chunk_data, corrected, speaker, status):
            if not chunk_data:
                return "No active chunk to save"
                
            success = update_chunk(
                chunk_data["id"],
                corrected,
                speaker,
                status
            )
            return "Changes saved successfully!" if success else "Error saving changes"
        
        # Wire up the UI
        refresh_btn.click(
            fn=refresh_calls,
            outputs=call_dropdown
        )
        
        call_dropdown.change(
            fn=load_chunks,
            inputs=call_dropdown,
            outputs=[
                chunks_list,
                audio_player,
                original_text,
                corrected_text,
                speaker_radio,
                status_radio,
                current_chunk
            ]
        )
        
        next_btn.click(
            fn=lambda idx, chunks: update_chunk_display(chunks, idx + 1),
            inputs=[current_chunk_index, chunks_list],
            outputs=[
                audio_player,
                original_text,
                speaker_radio,
                status_radio,
                current_chunk,
                chunk_info
            ]
        )
        
        prev_btn.click(
            fn=lambda idx, chunks: update_chunk_display(chunks, idx - 1),
            inputs=[current_chunk_index, chunks_list],
            outputs=[
                audio_player,
                original_text,
                speaker_radio,
                status_radio,
                current_chunk,
                chunk_info
            ]
        )
        
        save_btn.click(
            fn=save_changes,
            inputs=[current_chunk, corrected_text, speaker_radio, status_radio],
            outputs=chunk_info
        )
        
        # Initial load
        refresh_btn.click(
            fn=refresh_calls,
            outputs=call_dropdown
        )
    
    return review_tab

def create_export_tab():
    """Create the export tab UI."""
    with gr.Blocks() as export_tab:
        gr.Markdown("## Export Dataset")
        
        with gr.Row():
            train_split = gr.Slider(
                label="Train/Validation Split (%)",
                minimum=50,
                maximum=100,
                value=80,
                step=5
            )
        
        with gr.Row():
            export_btn = gr.Button("Export Dataset", variant="primary")
        
        export_status = gr.Textbox(
            label="Export Status",
            interactive=False,
            placeholder="Export status will appear here..."
        )
        
        def export_dataset(split):
            try:
                # In a real implementation, this would call your export API
                return f"Exporting dataset with {split}% training data..."
            except Exception as e:
                return f"Error exporting dataset: {str(e)}"
        
        export_btn.click(
            fn=export_dataset,
            inputs=train_split,
            outputs=export_status
        )
    
    return export_tab

def create_ui():
    """Create the main Gradio UI with tabs."""
    with gr.Blocks(title="Whisper Fine-Tuning Data Prep") as demo:
        gr.Markdown("# Whisper Fine-Tuning Data Preparation")
        
        with gr.Tabs() as tabs:
            with gr.TabItem("Upload"):
                upload_tab = create_upload_tab()
            
            with gr.TabItem("Review"):
                review_tab = create_review_tab()
            
            with gr.TabItem("Export"):
                export_tab = create_export_tab()
    
    return demo

# For testing
if __name__ == "__main__":
    demo = create_ui()
    demo.launch(server_name="0.0.0.0", server_port=7860)

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from app.db.base import get_db
from app.models.models import Chunk, ChunkStatus, SpeakerRole, Call, User

router = APIRouter()

class ChunkResponse(BaseModel):
    id: int
    call_id: int
    start_time: float
    end_time: float
    duration: float
    original_text: Optional[str]
    corrected_text: Optional[str]
    speaker_role: str
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UpdateChunkRequest(BaseModel):
    corrected_text: Optional[str] = None
    speaker_role: Optional[SpeakerRole] = None
    status: Optional[ChunkStatus] = None

@router.get("/", response_model=List[ChunkResponse])
async def list_chunks(
    call_id: Optional[int] = None,
    status: Optional[ChunkStatus] = None,
    speaker_role: Optional[SpeakerRole] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List chunks with optional filtering.
    """
    query = db.query(Chunk)
    
    if call_id is not None:
        query = query.filter(Chunk.call_id == call_id)
    
    if status is not None:
        query = query.filter(Chunk.status == status)
    
    if speaker_role is not None:
        query = query.filter(Chunk.speaker_role == speaker_role)
    
    chunks = query.offset(skip).limit(limit).all()
    return chunks

@router.get("/{chunk_id}", response_model=ChunkResponse)
async def get_chunk(
    chunk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific chunk by ID.
    """
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found"
        )
    return chunk

@router.patch("/{chunk_id}", response_model=ChunkResponse)
async def update_chunk(
    chunk_id: int,
    update_data: UpdateChunkRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a chunk's transcription, speaker role, or status.
    """
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if not chunk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk not found"
        )
    
    # Update fields if provided
    if update_data.corrected_text is not None:
        chunk.corrected_text = update_data.corrected_text
    
    if update_data.speaker_role is not None:
        chunk.speaker_role = update_data.speaker_role
    
    if update_data.status is not None:
        chunk.status = update_data.status
    
    db.commit()
    db.refresh(chunk)
    
    return chunk

@router.get("/{chunk_id}/audio")
async def get_chunk_audio(
    chunk_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the audio file for a specific chunk.
    """
    chunk = db.query(Chunk).filter(Chunk.id == chunk_id).first()
    if not chunk or not os.path.exists(chunk.file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chunk audio not found"
        )
    
    return FileResponse(
        chunk.file_path,
        media_type="audio/wav",
        filename=f"chunk_{chunk_id}.wav"
    )

# Helper function for auth (to be implemented in auth.py)
def get_current_user():
    # This is a placeholder - implement proper authentication
    return User(id=1, email="admin@example.com", role="admin")

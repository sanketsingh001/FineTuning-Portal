import os
import shutil
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.config import settings
from app.db.base import get_db
from app.models.models import Call, CallStatus, User
from app.tasks.audio_processing import process_call_task

router = APIRouter()

class CallResponse(BaseModel):
    id: int
    original_filename: str
    status: str
    created_at: datetime

@router.post("/", response_model=CallResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Assuming you have auth set up
):
    """
    Upload a call audio file for processing.
    """
    # Validate file type
    allowed_extensions = {'.wav', '.mp3', '.m4a', '.ogg', '.flac'}
    file_ext = os.path.splitext(file.filename)[1].lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file_ext} not allowed. Allowed types: {', '.join(allowed_extensions)}"
        )
    
    # Create upload directory if it doesn't exist
    upload_dir = settings.UPLOAD_DIR
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    file_uuid = str(uuid.uuid4())
    file_path = os.path.join(upload_dir, f"{file_uuid}{file_ext}")
    
    try:
        # Save the uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Create call record in database
        call = Call(
            original_filename=file.filename,
            file_path=file_path,
            file_size=file_size,
            uploaded_by_id=current_user.id,
            status=CallStatus.UPLOADED
        )
        db.add(call)
        db.commit()
        db.refresh(call)
        
        # Start background task to process the call
        process_call_task.delay(call.id)
        
        return call
        
    except Exception as e:
        # Clean up file if something went wrong
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading file: {str(e)}"
        )

@router.get("/", response_model=List[CallResponse])
async def list_calls(
    skip: int = 0, 
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all calls with pagination.
    """
    calls = db.query(Call).offset(skip).limit(limit).all()
    return calls

@router.get("/{call_id}", response_model=CallResponse)
async def get_call(
    call_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a specific call.
    """
    call = db.query(Call).filter(Call.id == call_id).first()
    if not call:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Call not found"
        )
    return call

# Helper function for auth (to be implemented in auth.py)
def get_current_user():
    # This is a placeholder - implement proper authentication
    return User(id=1, email="admin@example.com", role="admin")

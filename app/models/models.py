from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from .base import Base, TimestampMixin

class UserRole(str, PyEnum):
    ADMIN = "admin"
    REVIEWER = "reviewer"

class CallStatus(str, PyEnum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"

class ChunkStatus(str, PyEnum):
    PENDING = "pending"
    REVIEWED = "reviewed"
    APPROVED = "approved"

class SpeakerRole(str, PyEnum):
    AGENT = "agent"
    CUSTOMER = "customer"
    UNKNOWN = "unknown"

class User(Base, TimestampMixin):
    __tablename__ = "users"
    
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    role = Column(Enum(UserRole), default=UserRole.REVIEWER)
    
    # Relationships
    calls = relationship("Call", back_populates="uploaded_by")
    reviews = relationship("Review", back_populates="reviewer")

class Call(Base, TimestampMixin):
    __tablename__ = "calls"
    
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)  # in bytes
    duration = Column(Float)  # in seconds
    language = Column(String, default="hi")  # ISO 639-1 language code
    status = Column(Enum(CallStatus), default=CallStatus.UPLOADED)
    metadata = Column(JSON, default=dict)
    
    # Foreign keys
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    
    # Relationships
    uploaded_by = relationship("User", back_populates="calls")
    chunks = relationship("Chunk", back_populates="call", cascade="all, delete-orphan")

class Chunk(Base, TimestampMixin):
    __tablename__ = "chunks"
    
    file_path = Column(String, nullable=False)
    start_time = Column(Float, nullable=False)  # in seconds
    end_time = Column(Float, nullable=False)  # in seconds
    duration = Column(Float, nullable=False)  # in seconds
    original_text = Column(String)  # Auto-generated transcription
    corrected_text = Column(String)  # After human review
    speaker_role = Column(Enum(SpeakerRole), default=SpeakerRole.UNKNOWN)
    status = Column(Enum(ChunkStatus), default=ChunkStatus.PENDING)
    metadata = Column(JSON, default=dict)  # For storing diarization info, confidence scores, etc.
    
    # Foreign keys
    call_id = Column(Integer, ForeignKey("calls.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    call = relationship("Call", back_populates="chunks")
    reviews = relationship("Review", back_populates="chunk", cascade="all, delete-orphan")

class Review(Base, TimestampMixin):
    __tablename__ = "reviews"
    
    notes = Column(String)
    changes = Column(JSON)  # Track what was changed
    
    # Foreign keys
    chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    chunk = relationship("Chunk", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")

class Export(Base, TimestampMixin):
    __tablename__ = "exports"
    
    name = Column(String, nullable=False)
    description = Column(String)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer)  # in bytes
    metadata = Column(JSON, default=dict)  # Export settings, filters, etc.
    
    # Foreign keys
    created_by_id = Column(Integer, ForeignKey("users.id"))

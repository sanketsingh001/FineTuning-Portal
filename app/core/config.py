from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # API
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Whisper Fine-Tuning Data Prep"
    
    # Security
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/whisper_prep"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # MinIO
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "whisper-audio"
    MINIO_SECURE: bool = False
    
    # Audio Processing
    AUDIO_SAMPLE_RATE: int = 16000
    MAX_AUDIO_DURATION: int = 30  # seconds
    
    # Whisper Model
    WHISPER_MODEL: str = "large-v3"
    WHISPER_DEVICE: str = "cuda"  # or "cpu"
    
    # File Storage
    BASE_DIR: Path = Path(__file__).parent.parent.parent
    UPLOAD_DIR: Path = BASE_DIR / "data" / "uploads"
    PROCESSED_DIR: Path = BASE_DIR / "data" / "processed"
    CHUNKS_DIR: Path = BASE_DIR / "data" / "chunks"
    EXPORTS_DIR: Path = BASE_DIR / "data" / "exports"
    
    class Config:
        case_sensitive = True
        env_file = ".env"

# Create data directories if they don't exist
settings = Settings()
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
os.makedirs(settings.PROCESSED_DIR, exist_ok=True)
os.makedirs(settings.CHUNKS_DIR, exist_ok=True)
os.makedirs(settings.EXPORTS_DIR, exist_ok=True)

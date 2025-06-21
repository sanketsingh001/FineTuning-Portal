from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os
import sys

from app.core.config import settings
from app.db.base import Base, engine, get_db
from app.api.v1.endpoints import upload, chunks, auth
from app.ui.app import create_ui_app

# Create database tables
Base.metadata.create_all(bind=engine)

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Whisper Fine-Tuning Data Preparation API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Set up CORS - more permissive in Colab
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include API routes
app.include_router(auth.router, prefix="/api/v1", tags=["auth"])
app.include_router(upload.router, prefix="/api/v1", tags=["upload"])
app.include_router(chunks.router, prefix="/api/v1", tags=["chunks"])

# Mount Gradio app
gradio_app = create_ui_app()
app.mount("/gradio", gradio_app)

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "environment": "colab" if 'COLAB_JUPYTER_TOKEN' in os.environ else "local"}

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Whisper Fine-Tuning API",
        "docs": "/api/docs",
        "gradio_ui": "/gradio"
    }

# Colab specific setup
if 'COLAB_JUPYTER_TOKEN' in os.environ:
    # Ensure data directories exist
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/chunks", exist_ok=True)
    os.makedirs("data/exports", exist_ok=True)
    
    print("Running in Google Colab environment")
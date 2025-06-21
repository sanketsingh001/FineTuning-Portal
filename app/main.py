from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import os

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

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["auth"]
)

app.include_router(
    upload.router,
    prefix="/api/v1/uploads",
    tags=["uploads"]
)

app.include_router(
    chunks.router,
    prefix="/api/v1/chunks",
    tags=["chunks"]
)

# Mount static files for serving audio chunks
app.mount("/static", StaticFiles(directory=settings.BASE_DIR / "data"), name="static")

# Create and mount Gradio UI
gradio_app = create_ui_app()
app.mount("/gradio", gradio_app, name="gradio")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}

# Root endpoint redirects to Gradio UI
@app.get("/")
async def root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

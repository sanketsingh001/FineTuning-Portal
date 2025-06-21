# Whisper Fine-Tuning Data Preparation Portal

A web-based platform for preparing audio data for fine-tuning OpenAI's Whisper ASR models, specifically designed for Indian call-center data (Hindi, Marathi, etc.).

## Features

- **Audio Upload**: Upload call recordings in various formats (WAV, MP3, etc.)
- **Automatic Processing**:
  - Audio resampling to 16kHz mono
  - Voice activity detection and chunking (≤30s)
  - Automatic transcription using Whisper
  - Speaker diarization (basic)
- **Review Interface**:
  - Listen to audio chunks
  - Edit transcriptions
  - Tag speaker roles (agent/customer)
  - Track review status
- **Dataset Export**:
  - Export in Hugging Face compatible format
  - Train/validation splits
  - Complete metadata

## Prerequisites

- Docker and Docker Compose
- Python 3.10+
- (Optional) NVIDIA GPU with CUDA for faster processing

## Quick Start

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd whisper-prep
   ```

2. Create a `.env` file with your configuration (a template is provided):
   ```bash
   cp .env.example .env
   # Edit .env as needed
   ```

3. Build and start the services:
   ```bash
   docker-compose up --build -d
   ```

4. Access the application:
   - Web UI: http://localhost:8000/gradio
   - API Docs: http://localhost:8000/api/docs
   - MinIO Console: http://localhost:9001 (admin/minioadmin)
   - pgAdmin: http://localhost:5050 (admin@example.com/admin)

## Project Structure

```
whisper-prep/
├── app/                      # Backend application
│   ├── api/                  # API endpoints
│   ├── core/                 # Core configurations
│   ├── db/                   # Database models and migrations
│   ├── models/               # SQLAlchemy models
│   ├── tasks/                # Background tasks
│   └── main.py               # FastAPI application
├── ui/                       # Gradio frontend
├── data/                     # Uploaded and processed files
│   ├── uploads/              # Original uploads
│   ├── processed/            # Processed audio files
│   ├── chunks/               # Audio chunks
│   └── exports/              # Exported datasets
├── .env                      # Environment variables
├── docker-compose.yml        # Docker Compose configuration
├── Dockerfile               # Backend Dockerfile
└── requirements.txt         # Python dependencies
```

## API Endpoints

- `POST /api/v1/uploads/` - Upload audio files
- `GET /api/v1/chunks/` - List chunks with filters
- `PATCH /api/v1/chunks/{id}` - Update chunk (transcript, speaker, status)
- `GET /api/v1/chunks/{id}/audio` - Get chunk audio

## Development

1. Set up a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Start the development server:
   ```bash
   uvicorn app.main:app --reload
   ```

3. Start Celery worker:
   ```bash
   celery -A app.tasks.worker worker --loglevel=info
   ```

## Testing

Run the test suite:
```bash
pytest
```

## Deployment

For production deployment:

1. Set up a proper database (PostgreSQL)
2. Configure Redis for task queue
3. Set up MinIO or another S3-compatible storage
4. Update `.env` with production values
5. Use a production ASGI server like Uvicorn with Gunicorn

## License

MIT

## Acknowledgments

- [OpenAI Whisper](https://openai.com/research/whisper)
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper)
- [FastAPI](https://fastapi.tiangolo.com/)
- [Gradio](https://gradio.app/)

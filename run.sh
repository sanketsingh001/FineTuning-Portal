#!/bin/bash

# Create necessary directories
mkdir -p data/uploads data/processed data/chunks data/exports

# Install Python dependencies
pip install -r requirements.txt

# Initialize the database
echo "Initializing database..."
python init_db.py

# Start the application using Docker Compose
echo "Starting services with Docker Compose..."
docker-compose up --build -d

echo ""
echo "=========================================="
echo "Whisper Fine-Tuning Data Preparation Portal"
echo "=========================================="
echo ""
echo "Application is starting up..."
echo "- Web UI: http://localhost:8000/gradio"
echo "- API Docs: http://localhost:8000/api/docs"
echo "- MinIO Console: http://localhost:9001 (admin/minioadmin)"
echo "- pgAdmin: http://localhost:5050 (admin@example.com/admin)"
echo ""
echo "Use 'docker-compose logs -f' to view logs"
echo "Use 'docker-compose down' to stop the application"
echo ""

# Follow the logs
docker-compose logs -f

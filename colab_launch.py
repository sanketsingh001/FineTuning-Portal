import os
import subprocess
import threading
import time
from pyngrok import ngrok

def start_fastapi():
    # Set environment variables for Colab
    os.environ["DATABASE_URL"] = "sqlite:///whisper.db"
    os.environ["WHISPER_DEVICE"] = "cpu"
    os.environ["PYTHONUNBUFFERED"] = "1"
    
    # Start the FastAPI server
    subprocess.run([
        "uvicorn", 
        "app.main:app", 
        "--host", "0.0.0.0", 
        "--port", "8000",
        "--reload"
    ])

def print_urls(public_url):
    print("\n" + "="*60)
    print("WHISPER FINE-TUNING PORTAL - COLAB EDITION")
    print("="*60)
    print(f"• API Documentation: {public_url}/api/docs")
    print(f"• Gradio Interface: {public_url}/gradio")
    print("="*60 + "\n")
    print("Note: The app will automatically stay alive for up to 12 hours")
    print("="*60 + "\n")

if __name__ == "__main__":
    # Create necessary directories
    os.makedirs("data/uploads", exist_ok=True)
    os.makedirs("data/chunks", exist_ok=True)
    os.makedirs("data/exports", exist_ok=True)
    
    # Start FastAPI in a separate thread
    print("Starting FastAPI server...")
    fastapi_thread = threading.Thread(target=start_fastapi)
    fastapi_thread.daemon = True
    fastapi_thread.start()
    
    # Wait for FastAPI to start
    time.sleep(5)
    
    try:
        # Start ngrok tunnel
        print("Setting up ngrok tunnel...")
        public_url = ngrok.connect(8000)
        print_urls(public_url)
        
        # Keep the script running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"Error: {e}")
        print("\nShutting down...")
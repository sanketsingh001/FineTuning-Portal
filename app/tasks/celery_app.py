from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "whisper_tasks",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.audio_processing"]
)

# Using the settings module
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 60,  # 1 hour
    task_soft_time_limit=55 * 60  # 55 minutes
)

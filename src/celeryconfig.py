"""
Celery configuration for async task processing
"""

import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

# Create Celery app
app = Celery(
    "video_processor",
    broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1"),
)

# Task configuration
app.conf.update(
    task_serializer="json",     
    accept_content=["json"],    # Accept JSON messages
    result_serializer="json",   
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,       # Hard limit: 1h per task (kill if exceeds)
    task_soft_time_limit=3000,  # Soft limit: 50m (raise exception)
    imports=["src.services.tasks"],
)
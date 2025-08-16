# main/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from django.conf import settings
import os

scheduler = BackgroundScheduler(timezone=settings.TIME_ZONE)

def start_scheduler():
    """
    Start the APScheduler once when Django boots.
    """
    if not scheduler.running:
        # Prevent double-start with runserver autoreload
        if os.environ.get("RUN_MAIN", None) == "true":
            scheduler.start()
            print("✅ APScheduler started")

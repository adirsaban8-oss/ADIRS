"""
Appointment Reminder Scheduler for LISHAI SIMANI
Runs background jobs to send email reminders to customers
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from reminder_service import send_day_before_reminders, send_morning_reminders
from datetime import datetime
import atexit


def create_scheduler():
    """Create and configure the reminder scheduler."""
    scheduler = BackgroundScheduler()

    # Send day-before reminders at 6:00 PM every day
    scheduler.add_job(
        func=send_day_before_reminders,
        trigger=CronTrigger(hour=18, minute=0),
        id='day_before_reminders',
        name='Send day-before appointment reminders',
        replace_existing=True
    )

    # Send morning reminders at 9:00 AM every day
    scheduler.add_job(
        func=send_morning_reminders,
        trigger=CronTrigger(hour=9, minute=0),
        id='morning_reminders',
        name='Send morning appointment reminders',
        replace_existing=True
    )

    return scheduler


def start_scheduler():
    """Start the reminder scheduler."""
    scheduler = create_scheduler()
    scheduler.start()
    print(f"[{datetime.now()}] Reminder scheduler started")
    print("  - Day-before reminders: 18:00 daily")
    print("  - Morning reminders: 09:00 daily")

    # Shut down the scheduler when exiting the app
    atexit.register(lambda: scheduler.shutdown())

    return scheduler


if __name__ == '__main__':
    # For testing - run scheduler standalone
    import time

    print("Starting reminder scheduler (standalone mode)...")
    scheduler = start_scheduler()

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        print("Scheduler stopped")

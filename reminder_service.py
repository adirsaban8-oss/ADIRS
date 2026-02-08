"""
Email Reminder Service for LISHAI SIMANI Booking System
Sends automatic reminders to customers before their appointments
"""

import os
import json
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # Use App Password for Gmail

# Email feature flag
EMAIL_ENABLED = os.getenv('EMAIL_ENABLED', 'false').lower() == 'true'

# Google Calendar configuration
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', '')


def get_calendar_service():
    """
    Create and return a Google Calendar service instance.
    Uses GOOGLE_CREDENTIALS_JSON environment variable only (no file operations).
    """
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON', '')

    if not credentials_json:
        raise Exception("GOOGLE_CREDENTIALS_JSON environment variable is not set")

    try:
        credentials_info = json.loads(credentials_json)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info, scopes=SCOPES
        )
        return build('calendar', 'v3', credentials=credentials)
    except json.JSONDecodeError as e:
        raise Exception(f"Invalid JSON in GOOGLE_CREDENTIALS_JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to create calendar service: {str(e)}")


def get_upcoming_appointments(hours_ahead=24):
    """
    Get appointments happening within the specified hours.

    Args:
        hours_ahead: Number of hours to look ahead

    Returns:
        List of appointment events
    """
    try:
        service = get_calendar_service()

        now = datetime.now()
        time_min = now.isoformat() + 'Z'
        time_max = (now + timedelta(hours=hours_ahead)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        return events_result.get('items', [])

    except HttpError as e:
        if e.resp.status == 403:
            logger.error(
                "403 Forbidden – service account cannot access calendar '%s'. "
                "Share the calendar with the service account email and grant "
                "'See all event details' permission.",
                CALENDAR_ID,
            )
        else:
            logger.error("Google Calendar API error: %s", e)
        return []
    except Exception as e:
        logger.error("Error fetching appointments: %s", e)
        return []


def parse_appointment_details(event):
    """
    Parse appointment details from a calendar event.

    Returns:
        Dictionary with name, phone, email, service, date, time
    """
    description = event.get('description', '')
    summary = event.get('summary', '')

    # Parse description (format: service\n\nname\nphone\nemail\n\nnotes)
    lines = [line.strip() for line in description.strip().split('\n') if line.strip()]

    details = {
        'name': '',
        'phone': '',
        'email': '',
        'service': lines[0] if lines else '',
        'summary': summary,
    }

    # Extract name, phone and email from description
    if len(lines) >= 2:
        details['name'] = lines[1] if len(lines) > 1 else ''
    if len(lines) >= 3:
        details['phone'] = lines[2] if len(lines) > 2 else ''
    if len(lines) >= 4:
        # Check if line looks like an email
        potential_email = lines[3] if len(lines) > 3 else ''
        if '@' in potential_email:
            details['email'] = potential_email

    # Parse start time
    start = event['start'].get('dateTime', event['start'].get('date'))
    if 'T' in start:
        dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
        details['date'] = dt.strftime('%d/%m/%Y')
        details['time'] = dt.strftime('%H:%M')
        details['datetime'] = dt

    return details


def send_email_reminder(to_email, customer_name, service, date, time, reminder_type='day_before'):
    """
    Send an email reminder to the customer.

    Args:
        to_email: Customer's email address
        customer_name: Customer's name
        service: Service name
        date: Appointment date
        time: Appointment time
        reminder_type: 'day_before' or 'morning_of'
    """
    if not EMAIL_ENABLED:
        return False

    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        logger.warning("Email credentials not configured")
        return False

    if not to_email:
        logger.debug("No email address for customer: %s", customer_name)
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = to_email

        if reminder_type == 'day_before':
            msg['Subject'] = f'תזכורת: יש לך תור מחר אצל LISHAI SIMANI'
            reminder_text = 'מחר'
        else:
            msg['Subject'] = f'תזכורת: יש לך תור היום אצל LISHAI SIMANI'
            reminder_text = 'היום'

        # HTML email content
        html_content = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="he">
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; direction: rtl; }}
                .container {{ max-width: 500px; margin: 0 auto; padding: 20px; }}
                .header {{ text-align: center; color: #b8860b; margin-bottom: 20px; }}
                .details {{ background: #f9f9f9; padding: 20px; border-radius: 10px; }}
                .detail-row {{ margin: 10px 0; }}
                .label {{ font-weight: bold; color: #333; }}
                .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>LISHAI SIMANI</h1>
                    <p>תזכורת לתור</p>
                </div>

                <p>שלום {customer_name},</p>
                <p>רצינו להזכיר לך שיש לך תור {reminder_text}:</p>

                <div class="details">
                    <div class="detail-row">
                        <span class="label">שירות:</span> {service}
                    </div>
                    <div class="detail-row">
                        <span class="label">תאריך:</span> {date}
                    </div>
                    <div class="detail-row">
                        <span class="label">שעה:</span> {time}
                    </div>
                    <div class="detail-row">
                        <span class="label">כתובת:</span> משעול הרקפת 3, קרני שומרון
                    </div>
                </div>

                <p>לביטול או שינוי תור, נא ליצור קשר בהקדם:</p>
                <p>📞 051-5656295</p>

                <div class="footer">
                    <p>נשמח לראותך!</p>
                    <p>LISHAI SIMANI - מניקוריסטית מקצועית</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Plain text version
        text_content = f"""
        שלום {customer_name},

        תזכורת: יש לך תור {reminder_text}

        שירות: {service}
        תאריך: {date}
        שעה: {time}
        כתובת: משעול הרקפת 3, קרני שומרון

        לביטול או שינוי תור: 051-5656295

        נשמח לראותך!
        LISHAI SIMANI
        """

        msg.attach(MIMEText(text_content, 'plain', 'utf-8'))
        msg.attach(MIMEText(html_content, 'html', 'utf-8'))

        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Reminder sent to {to_email} for appointment on {date} at {time}")
        return True

    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        return False


def send_day_before_reminders():
    """Send reminders for appointments happening tomorrow."""
    print(f"[{datetime.now()}] Checking for day-before reminders...")

    # Get appointments 24-48 hours ahead
    tomorrow_start = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
    tomorrow_end = tomorrow_start + timedelta(days=1)

    appointments = get_upcoming_appointments(hours_ahead=48)

    for event in appointments:
        details = parse_appointment_details(event)
        if details.get('datetime'):
            apt_date = details['datetime'].replace(tzinfo=None)
            if tomorrow_start <= apt_date < tomorrow_end:
                # This appointment is tomorrow
                send_email_reminder(
                    to_email=details.get('email'),
                    customer_name=details['name'],
                    service=details['service'],
                    date=details['date'],
                    time=details['time'],
                    reminder_type='day_before'
                )


def send_morning_reminders():
    """Send reminders for appointments happening today."""
    print(f"[{datetime.now()}] Checking for morning reminders...")

    today_start = datetime.now().replace(hour=0, minute=0, second=0)
    today_end = today_start + timedelta(days=1)

    appointments = get_upcoming_appointments(hours_ahead=24)

    for event in appointments:
        details = parse_appointment_details(event)
        if details.get('datetime'):
            apt_date = details['datetime'].replace(tzinfo=None)
            if today_start <= apt_date < today_end:
                send_email_reminder(
                    to_email=details.get('email'),
                    customer_name=details['name'],
                    service=details['service'],
                    date=details['date'],
                    time=details['time'],
                    reminder_type='morning_of'
                )


if __name__ == '__main__':
    # Test the reminder system
    print("Testing reminder service...")
    print("Upcoming appointments:")
    appointments = get_upcoming_appointments(hours_ahead=72)
    for apt in appointments:
        details = parse_appointment_details(apt)
        print(f"  - {details['name']}: {details['service']} on {details['date']} at {details['time']}")

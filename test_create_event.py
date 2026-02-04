"""
Test: Create a calendar event using Service Account
"""
import os
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'cred.json')
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID')

print("=" * 50)
print("Creating Test Event")
print("=" * 50)
print(f"Calendar: {CALENDAR_ID}")
print()

# Connect
credentials = service_account.Credentials.from_service_account_file(
    CREDENTIALS_FILE, scopes=SCOPES
)
service = build('calendar', 'v3', credentials=credentials)

# Create event for tomorrow at 14:00
tomorrow = datetime.now() + timedelta(days=1)
start_time = tomorrow.replace(hour=14, minute=0, second=0, microsecond=0)
end_time = start_time + timedelta(hours=1)

event = {
    'summary': '🧪 אירוע בדיקה - LISHAI',
    'description': 'אירוע בדיקה שנוצר אוטומטית מהקוד.\nאפשר למחוק אותו.',
    'start': {
        'dateTime': start_time.isoformat(),
        'timeZone': 'Asia/Jerusalem',
    },
    'end': {
        'dateTime': end_time.isoformat(),
        'timeZone': 'Asia/Jerusalem',
    },
}

print(f"Creating event: {event['summary']}")
print(f"Time: {start_time.strftime('%Y-%m-%d %H:%M')}")
print()

try:
    created_event = service.events().insert(
        calendarId=CALENDAR_ID,
        body=event
    ).execute()

    print("✅ Event created successfully!")
    print(f"   Event ID: {created_event.get('id')}")
    print(f"   Link: {created_event.get('htmlLink')}")
    print()
    print("👉 Check your Google Calendar - you should see the event!")

except Exception as e:
    print(f"❌ Error: {e}")

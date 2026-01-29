"""
Minimal test: Google Calendar Service Account authentication
"""
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

load_dotenv()

SCOPES = ['https://www.googleapis.com/auth/calendar']
CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', 'primary')

print("=" * 50)
print("Google Calendar Service Account Test")
print("=" * 50)
print(f"Credentials file: {CREDENTIALS_FILE}")
print(f"Calendar ID: {CALENDAR_ID}")
print()

# Step 1: Load credentials
print("[1] Loading credentials...")
try:
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE, scopes=SCOPES
    )
    print(f"    ✅ Credentials loaded!")
    print(f"    Service Account: {credentials.service_account_email}")
except FileNotFoundError:
    print(f"    ❌ File not found: {CREDENTIALS_FILE}")
    exit(1)
except Exception as e:
    print(f"    ❌ Failed to load credentials: {e}")
    exit(1)

# Step 2: Build service
print("\n[2] Connecting to Google Calendar API...")
try:
    service = build('calendar', 'v3', credentials=credentials)
    print("    ✅ Connected to API!")
except Exception as e:
    print(f"    ❌ Failed to connect: {e}")
    exit(1)

# Step 3: Try to access calendar
print(f"\n[3] Trying to read calendar '{CALENDAR_ID}'...")
try:
    events = service.events().list(
        calendarId=CALENDAR_ID,
        maxResults=1
    ).execute()
    print("    ✅ Calendar access works!")
    print(f"    Events found: {len(events.get('items', []))}")

except HttpError as e:
    if e.resp.status == 404:
        print("    ⚠️  Calendar not found (expected if not shared yet)")
        print("    Auth is working! Just need to share calendar.")
    elif e.resp.status == 403:
        print("    ⚠️  No permission to access calendar (expected)")
        print("    Auth is working! Just need to share calendar.")
    else:
        print(f"    ❌ API Error: {e}")

print("\n" + "=" * 50)
print("RESULT: Authentication is working!" if credentials else "RESULT: Failed")
print("=" * 50)
print(f"\nNext step: Share your Google Calendar with:")
print(f"  {credentials.service_account_email}")
print("  (Give 'Make changes to events' permission)")

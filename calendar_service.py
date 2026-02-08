"""
Google Calendar Service Module for LISHAI Booking System
Handles all interactions with Google Calendar API
"""

import os
import json
import logging
from datetime import datetime, timedelta
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# No load_dotenv() here – app.py loads env vars before importing this module.

logger = logging.getLogger(__name__)

# Google Calendar API scopes
SCOPES = ['https://www.googleapis.com/auth/calendar']

# Load configuration from environment variables
CALENDAR_ID = os.getenv('GOOGLE_CALENDAR_ID', '')
if not CALENDAR_ID or CALENDAR_ID == 'primary':
    logger.warning(
        "GOOGLE_CALENDAR_ID is %s. Service accounts cannot access 'primary'. "
        "Set GOOGLE_CALENDAR_ID to the target calendar's email address.",
        repr(CALENDAR_ID) if CALENDAR_ID else 'missing'
    )

# Cached service instance
_calendar_service = None

# 403 error message used across this module
_PERMISSION_MSG = (
    "403 Forbidden – the service account does not have access to calendar '%s'. "
    "Fix: open Google Calendar > Settings for '%s' > Share with specific people > "
    "add the service account email with 'Make changes to events' permission."
)


def get_calendar_service():
    """
    Create and return a Google Calendar service instance.
    Uses service account credentials from GOOGLE_CREDENTIALS_JSON environment variable.
    NO FILE OPERATIONS - production safe for Railway.
    """
    global _calendar_service

    # Return cached service if available
    if _calendar_service is not None:
        return _calendar_service

    # Get credentials JSON from environment variable
    credentials_json = os.getenv('GOOGLE_CREDENTIALS_JSON', '')

    if not credentials_json:
        raise Exception(
            "GOOGLE_CREDENTIALS_JSON environment variable is not set. "
            "In Railway: Go to Variables and add GOOGLE_CREDENTIALS_JSON with "
            "the FULL content of your service account JSON file."
        )

    # Log for debugging (first 50 chars only for security)
    logger.info("GOOGLE_CREDENTIALS_JSON found, length: %d", len(credentials_json))

    try:
        # Parse JSON string to dictionary
        credentials_info = json.loads(credentials_json)

        # Validate required fields
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        missing = [f for f in required_fields if f not in credentials_info]
        if missing:
            raise Exception(f"Missing required fields in credentials: {missing}")

        logger.info("Service account: %s", credentials_info.get('client_email'))

        # Create credentials object from dictionary (NOT from file!)
        credentials = service_account.Credentials.from_service_account_info(
            credentials_info,
            scopes=SCOPES
        )

        # Build the calendar service
        service = build('calendar', 'v3', credentials=credentials)

        # Verify we can actually access the target calendar
        _verify_calendar_access(service)

        _calendar_service = service
        logger.info("Google Calendar service created and verified successfully!")
        return _calendar_service

    except json.JSONDecodeError as e:
        raise Exception(
            f"GOOGLE_CREDENTIALS_JSON is not valid JSON: {str(e)}. "
            "Make sure you copied the ENTIRE content of the JSON file, "
            "including the curly braces {{ }}."
        )
    except Exception as e:
        raise Exception(f"Failed to create calendar service: {str(e)}")


def _verify_calendar_access(service):
    """
    Verify that the service account can access CALENDAR_ID.
    Raises a clear error when permissions are missing.
    """
    if not CALENDAR_ID:
        raise Exception(
            "GOOGLE_CALENDAR_ID is not set. "
            "Set it to the calendar owner's email address (e.g. user@gmail.com)."
        )
    try:
        service.calendars().get(calendarId=CALENDAR_ID).execute()
    except HttpError as e:
        if e.resp.status == 403:
            logger.error(_PERMISSION_MSG, CALENDAR_ID, CALENDAR_ID)
            raise Exception(_PERMISSION_MSG % (CALENDAR_ID, CALENDAR_ID))
        if e.resp.status == 404:
            raise Exception(
                f"Calendar '{CALENDAR_ID}' not found. "
                "Check that GOOGLE_CALENDAR_ID is correct."
            )
        raise


def get_busy_slots(date_str):
    """
    Get all busy time slots for a specific date.

    Args:
        date_str: Date in 'YYYY-MM-DD' format

    Returns:
        List of tuples with (start_time, end_time) in 'HH:MM' format
    """
    try:
        service = get_calendar_service()

        # Parse date and create time boundaries
        date = datetime.strptime(date_str, '%Y-%m-%d')
        time_min = date.replace(hour=0, minute=0, second=0).isoformat() + 'Z'
        time_max = date.replace(hour=23, minute=59, second=59).isoformat() + 'Z'

        # Query calendar for events
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        busy_slots = []

        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            end = event['end'].get('dateTime', event['end'].get('date'))

            # Parse datetime and extract time
            if 'T' in start:  # DateTime format
                start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end.replace('Z', '+00:00'))
                busy_slots.append((
                    start_time.strftime('%H:%M'),
                    end_time.strftime('%H:%M')
                ))

        return busy_slots

    except HttpError as e:
        if e.resp.status == 403:
            logger.error(_PERMISSION_MSG, CALENDAR_ID, CALENDAR_ID)
            raise Exception(_PERMISSION_MSG % (CALENDAR_ID, CALENDAR_ID))
        raise Exception(f"Google Calendar API error: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to get busy slots: {str(e)}")


def check_availability(date_str, time_str, duration_minutes):
    """
    Check if a specific time slot is available.

    Args:
        date_str: Date in 'YYYY-MM-DD' format
        time_str: Time in 'HH:MM' format
        duration_minutes: Duration of the appointment in minutes

    Returns:
        True if slot is available, False otherwise
    """
    try:
        busy_slots = get_busy_slots(date_str)

        # Parse requested time
        requested_start = datetime.strptime(time_str, '%H:%M')
        requested_end = requested_start + timedelta(minutes=duration_minutes)

        # Check for conflicts with existing events
        for busy_start_str, busy_end_str in busy_slots:
            busy_start = datetime.strptime(busy_start_str, '%H:%M')
            busy_end = datetime.strptime(busy_end_str, '%H:%M')

            # Check if there's any overlap
            if not (requested_end <= busy_start or requested_start >= busy_end):
                return False

        return True

    except Exception as e:
        raise Exception(f"Failed to check availability: {str(e)}")


def create_event(booking_data):
    """
    Create a new calendar event for a booking.

    Args:
        booking_data: Dictionary containing:
            - name: Customer name
            - phone: Customer phone
            - service: Service name
            - service_he: Service name in Hebrew
            - date: Date in 'YYYY-MM-DD' format
            - time: Time in 'HH:MM' format
            - duration: Duration in minutes
            - notes: Optional notes

    Returns:
        Created event object from Google Calendar API
    """
    try:
        service = get_calendar_service()

        # Parse date and time
        start_datetime = datetime.strptime(
            f"{booking_data['date']} {booking_data['time']}",
            '%Y-%m-%d %H:%M'
        )
        end_datetime = start_datetime + timedelta(minutes=booking_data.get('duration', 60))

        # Build event description
        description = f"""
{booking_data.get('service_he', booking_data['service'])}

{booking_data['name']}
{booking_data['phone']}
{booking_data.get('email', '')}
""".strip()

        if booking_data.get('notes'):
            description += f"\n\n{booking_data['notes']}"

        # Create event object
        event = {
            'summary': f"{booking_data['name']} - {booking_data.get('service_he', booking_data['service'])}",
            'description': description,
            'start': {
                'dateTime': start_datetime.isoformat(),
                'timeZone': 'Asia/Jerusalem',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Asia/Jerusalem',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'popup', 'minutes': 60},
                    {'method': 'popup', 'minutes': 1440},  # 24 hours
                ],
            },
        }

        # Insert event to calendar
        created_event = service.events().insert(
            calendarId=CALENDAR_ID,
            body=event
        ).execute()

        return created_event

    except HttpError as e:
        if e.resp.status == 403:
            logger.error(_PERMISSION_MSG, CALENDAR_ID, CALENDAR_ID)
            raise Exception(_PERMISSION_MSG % (CALENDAR_ID, CALENDAR_ID))
        raise Exception(f"Google Calendar API error: {str(e)}")
    except Exception as e:
        raise Exception(f"Failed to create event: {str(e)}")


def filter_available_slots(date_str, all_slots, service_duration=30):
    """
    Filter out busy slots from a list of available time slots.

    This function checks each potential slot against existing calendar events
    and ensures there's no overlap for the FULL duration of the requested service.

    Args:
        date_str: Date in 'YYYY-MM-DD' format
        all_slots: List of time slots in 'HH:MM' format
        service_duration: Duration of the service in minutes (default 30)
                         This is the FULL duration the customer's appointment will take

    Returns:
        List of available time slots where the full service can be performed
        without overlapping any existing appointments
    """
    try:
        busy_slots = get_busy_slots(date_str)
        available_slots = []

        for slot in all_slots:
            slot_start = datetime.strptime(slot, '%H:%M')
            # Calculate when this service would END based on its full duration
            slot_end = slot_start + timedelta(minutes=service_duration)

            is_available = True
            for busy_start_str, busy_end_str in busy_slots:
                busy_start = datetime.strptime(busy_start_str, '%H:%M')
                busy_end = datetime.strptime(busy_end_str, '%H:%M')

                # Check if there's ANY overlap between the requested appointment
                # (slot_start to slot_end) and an existing appointment (busy_start to busy_end)
                # Overlap occurs when: NOT (new_end <= existing_start OR new_start >= existing_end)
                if not (slot_end <= busy_start or slot_start >= busy_end):
                    is_available = False
                    break

            if is_available:
                available_slots.append(slot)

        return available_slots

    except Exception as e:
        # If calendar service fails, return all slots (graceful degradation)
        logger.warning("Could not filter busy slots: %s", e)
        return all_slots


def cancel_event(event_id):
    """
    Cancel/delete a calendar event by its ID.

    Args:
        event_id: The Google Calendar event ID

    Returns:
        True if successfully cancelled, False otherwise
    """
    try:
        service = get_calendar_service()
        service.events().delete(
            calendarId=CALENDAR_ID,
            eventId=event_id
        ).execute()
        logger.info("Event %s cancelled successfully", event_id)
        return True

    except HttpError as e:
        if e.resp.status == 404:
            logger.info("Event %s not found (may already be cancelled)", event_id)
            return True  # Treat as success if already gone
        if e.resp.status == 403:
            logger.error(_PERMISSION_MSG, CALENDAR_ID, CALENDAR_ID)
        else:
            logger.error("Google Calendar API error cancelling event: %s", e)
        return False
    except Exception as e:
        logger.error("Failed to cancel event: %s", e)
        return False

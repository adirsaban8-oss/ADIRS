"""
ActiveTrail SMS Service - LISHAI SIMANI Beauty Studio
Handles sending booking confirmations, reminders, and OTP via ActiveTrail SMS API.

NOTE: All phone numbers use format 972XXXXXXXXX (no + prefix) for ActiveTrail API.
Internally the system uses E.164 (+972XXXXXXXXX) via phone_utils.
"""

import os
import logging
import sys
import requests
from datetime import datetime
from phone_utils import normalize_israeli_phone

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

# ============== CONFIGURATION ==============

SMS_ENABLED = os.getenv("SMS_ENABLED", "false").lower() == "true"
ACTIVETRAIL_API_KEY = os.getenv("ACTIVETRAIL_API_KEY", "")
SMS_SENDER_NAME = os.getenv("SMS_SENDER_NAME", "LISHAI SIM")  # max 11 chars

ACTIVETRAIL_SMS_URL = "http://webapi.mymarketing.co.il/api/smscampaign/OperationalMessage"


def _to_activetrail_phone(phone):
    """
    Convert any Israeli phone to ActiveTrail format: 972XXXXXXXXX (no + prefix).
    Returns None if invalid.
    """
    normalized = normalize_israeli_phone(phone)
    if not normalized:
        return None
    # Strip the leading '+' for ActiveTrail
    return normalized.lstrip('+')


def send_sms(phone, message):
    """
    Send a single SMS via ActiveTrail OperationalMessage API.

    Args:
        phone: Phone number (any Israeli format)
        message: SMS message text

    Returns:
        True if sent successfully, False otherwise
    """
    phone_at = _to_activetrail_phone(phone)

    if not SMS_ENABLED:
        logger.info("[SMS] MOCK MODE - Would send to %s: %s", phone, message[:60])
        return False

    if not ACTIVETRAIL_API_KEY:
        logger.info("[SMS] MOCK MODE - API key missing. To %s: %s", phone, message[:60])
        return False

    if not phone_at:
        logger.error("[SMS] Invalid phone format: %s", phone)
        return False

    payload = {
        "details": {
            "name": "LISHAI SMS",
            "from_name": SMS_SENDER_NAME[:11],
            "content": message,
            "can_unsubscribe": False,
        },
        "scheduling": {
            "send_now": True
        },
        "mobiles": [
            {"phone_number": phone_at}
        ]
    }

    headers = {
        "Authorization": ACTIVETRAIL_API_KEY,
        "Content-Type": "application/json"
    }

    try:
        logger.info("[SMS] Sending to %s via ActiveTrail...", phone_at)

        response = requests.post(
            ACTIVETRAIL_SMS_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code in (200, 201, 202):
            logger.info("[SMS] Sent successfully to %s (status %d)", phone_at, response.status_code)
            return True
        else:
            logger.error("[SMS] ActiveTrail error: status=%d body=%s", response.status_code, response.text[:200])
            return False

    except requests.exceptions.Timeout:
        logger.error("[SMS] ActiveTrail request timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        logger.error("[SMS] ActiveTrail connection error: %s", e)
        return False
    except Exception as e:
        logger.error("[SMS] Unexpected error: %s", e)
        return False


# ============== BOOKING CONFIRMATION ==============

def send_booking_confirmation(booking_data):
    """
    Send booking confirmation SMS.

    Args:
        booking_data: dict with keys: name, phone, service_he, date, time

    Returns:
        True if sent, False otherwise
    """
    try:
        phone = booking_data.get('phone', '')
        date = booking_data.get('date', '')
        time = booking_data.get('time', '')

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d/%m/%Y')
        except Exception:
            date_formatted = date

        message = f"התור נקבע ✔️\n{date_formatted} {time}\nLISHAI"

        logger.info("[SMS][Booking] Sending confirmation for %s at %s", date, time)
        return send_sms(phone, message)

    except Exception as e:
        logger.error("[SMS][Booking] Error sending confirmation: %s", e)
        return False


# ============== REMINDERS ==============

def send_reminder_day_before(booking_data):
    """
    Send reminder SMS the day before appointment (at 20:00).

    Args:
        booking_data: dict with keys: name, phone, service_he, date, time

    Returns:
        True if sent, False otherwise
    """
    try:
        phone = booking_data.get('phone', '')
        date = booking_data.get('date', '')
        time = booking_data.get('time', '')

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d/%m/%Y')
        except Exception:
            date_formatted = date

        message = f"תזכורת 📅\nמחר {date_formatted} {time}\nLISHAI"

        logger.info("[SMS][Reminder] Sending day-before reminder for %s", date)
        return send_sms(phone, message)

    except Exception as e:
        logger.error("[SMS][Reminder] Error sending day-before: %s", e)
        return False


def send_reminder_morning(booking_data):
    """
    Send reminder SMS the morning of appointment (at 08:00).

    Args:
        booking_data: dict with keys: name, phone, service_he, time

    Returns:
        True if sent, False otherwise
    """
    try:
        phone = booking_data.get('phone', '')
        date = booking_data.get('date', '')
        time = booking_data.get('time', '')

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d/%m/%Y')
        except Exception:
            date_formatted = date

        message = f"תזכורת 📅\nמחר {date_formatted} {time}\nLISHAI"

        logger.info("[SMS][Reminder] Sending morning reminder for %s", date)
        return send_sms(phone, message)

    except Exception as e:
        logger.error("[SMS][Reminder] Error sending morning reminder: %s", e)
        return False


# ============== CANCELLATION ==============

def send_cancellation_confirmation(booking_data):
    """
    Send cancellation confirmation SMS.

    Args:
        booking_data: dict with keys: name, phone, date, time

    Returns:
        True if sent, False otherwise
    """
    try:
        phone = booking_data.get('phone', '')

        message = "התור בוטל ✔️\nLISHAI"

        logger.info("[SMS][Cancel] Sending cancellation")
        return send_sms(phone, message)

    except Exception as e:
        logger.error("[SMS][Cancel] Error sending cancellation: %s", e)
        return False

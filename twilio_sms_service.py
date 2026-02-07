"""
Twilio SMS Notification Service - LISHAI SIMANI Beauty Studio
Handles sending booking confirmations and reminders via Twilio SMS.
"""

import os
import logging
import sys
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

# ============== CONFIGURATION ==============

TWILIO_ENABLED = os.getenv("TWILIO_ENABLED", "false").lower() == "true"
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER", "")

BUSINESS_NAME = "LISHAI SIMANI Beauty Studio"
BUSINESS_ADDRESS = "משעול הרקפת 3, קרני שומרון"
BUSINESS_PHONE = "051-5656295"


def normalize_phone_for_sms(phone):
    """
    Normalize Israeli phone to international format (+972XXXXXXXXX).
    """
    if not phone:
        return None
    clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    if clean.startswith("+"):
        clean = clean[1:]

    if clean.startswith("972"):
        if len(clean) == 12:
            return "+" + clean
        return None

    if clean.startswith("0") and len(clean) == 10:
        return "+972" + clean[1:]

    return None


def _send_sms(phone, message_body):
    """
    Internal function to send SMS via Twilio.

    Args:
        phone: Phone number (any format)
        message_body: SMS message text

    Returns:
        True if sent successfully, False otherwise
    """
    phone_intl = normalize_phone_for_sms(phone)

    if not TWILIO_ENABLED:
        logger.info("[Twilio][SMS] MOCK MODE - Would send to %s: %s", phone, message_body[:50])
        return False

    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not TWILIO_PHONE_NUMBER:
        logger.info("[Twilio][SMS] MOCK MODE - Credentials missing. To %s: %s", phone, message_body[:50])
        return False

    if not phone_intl:
        logger.error("[Twilio][SMS] Invalid phone format: %s", phone)
        return False

    try:
        from twilio.rest import Client

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

        logger.info("[Twilio][SMS] Sending to %s...", phone_intl)

        message = client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=phone_intl
        )

        logger.info("[Twilio][SMS] Sent successfully. SID: %s", message.sid)
        return True

    except Exception as e:
        logger.error("[Twilio][SMS] Send failed: %s", str(e))
        return False


# ============== BOOKING CONFIRMATION ==============

def send_booking_confirmation(booking_data):
    """
    Send booking confirmation SMS.

    Args:
        booking_data: dict with keys:
            - name: Customer name
            - phone: Customer phone
            - service_he: Service name in Hebrew
            - date: Date (YYYY-MM-DD)
            - time: Time (HH:MM)

    Returns:
        True if sent, False otherwise
    """
    try:
        name = booking_data.get('name', '')
        phone = booking_data.get('phone', '')
        service = booking_data.get('service_he', '')
        date = booking_data.get('date', '')
        time = booking_data.get('time', '')

        # Format date nicely
        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d/%m/%Y')
        except:
            date_formatted = date

        message = f"""שלום {name}!

התור שלך אושר בהצלחה ב-{BUSINESS_NAME}

📅 תאריך: {date_formatted}
🕐 שעה: {time}
💅 שירות: {service}

📍 כתובת: {BUSINESS_ADDRESS}
📞 טלפון: {BUSINESS_PHONE}

לביטול תור, התקשרי אלינו.

תודה שבחרת בנו! 💖"""

        logger.info("[Twilio][Booking] Sending confirmation to %s for %s at %s", name, date, time)
        return _send_sms(phone, message)

    except Exception as e:
        logger.error(f"[Twilio][Booking] Error sending confirmation: {str(e)}")
        return False


# ============== REMINDERS ==============

def send_reminder_day_before(booking_data):
    """
    Send reminder SMS the day before appointment (at 20:00).

    Args:
        booking_data: dict with same structure as send_booking_confirmation

    Returns:
        True if sent, False otherwise
    """
    try:
        name = booking_data.get('name', '')
        phone = booking_data.get('phone', '')
        service = booking_data.get('service_he', '')
        date = booking_data.get('date', '')
        time = booking_data.get('time', '')

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d/%m/%Y')
        except:
            date_formatted = date

        message = f"""שלום {name}!

תזכורת: מחר יש לך תור ב-{BUSINESS_NAME}

📅 {date_formatted} בשעה {time}
💅 {service}

📍 {BUSINESS_ADDRESS}

מצפים לראותך! 💖

לביטול - התקשרי ל-{BUSINESS_PHONE}"""

        logger.info("[Twilio][Reminder] Sending day-before reminder to %s", name)
        return _send_sms(phone, message)

    except Exception as e:
        logger.error(f"[Twilio][Reminder] Error sending day-before: {str(e)}")
        return False


def send_reminder_morning(booking_data):
    """
    Send reminder SMS the morning of appointment (at 08:00).

    Args:
        booking_data: dict with same structure as send_booking_confirmation

    Returns:
        True if sent, False otherwise
    """
    try:
        name = booking_data.get('name', '')
        phone = booking_data.get('phone', '')
        service = booking_data.get('service_he', '')
        time = booking_data.get('time', '')

        message = f"""בוקר טוב {name}!

תזכורת: היום יש לך תור ב-{BUSINESS_NAME}

🕐 בשעה {time}
💅 {service}

📍 {BUSINESS_ADDRESS}

נתראה בקרוב! 💖"""

        logger.info("[Twilio][Reminder] Sending morning reminder to %s", name)
        return _send_sms(phone, message)

    except Exception as e:
        logger.error(f"[Twilio][Reminder] Error sending morning reminder: {str(e)}")
        return False


# ============== CANCELLATION ==============

def send_cancellation_confirmation(booking_data):
    """
    Send cancellation confirmation SMS.

    Args:
        booking_data: dict with keys:
            - name: Customer name
            - phone: Customer phone
            - date: Date (YYYY-MM-DD)
            - time: Time (HH:MM)

    Returns:
        True if sent, False otherwise
    """
    try:
        name = booking_data.get('name', '')
        phone = booking_data.get('phone', '')
        date = booking_data.get('date', '')
        time = booking_data.get('time', '')

        try:
            date_obj = datetime.strptime(date, '%Y-%m-%d')
            date_formatted = date_obj.strftime('%d/%m/%Y')
        except:
            date_formatted = date

        message = f"""שלום {name},

התור שלך ל-{date_formatted} בשעה {time} בוטל בהצלחה.

להזמנת תור חדש:
📞 {BUSINESS_PHONE}

{BUSINESS_NAME}"""

        logger.info("[Twilio][Cancel] Sending cancellation to %s", name)
        return _send_sms(phone, message)

    except Exception as e:
        logger.error(f"[Twilio][Cancel] Error sending cancellation: {str(e)}")
        return False

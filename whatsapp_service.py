"""
WhatsApp Cloud API Service - LISHAY SIMANI Beauty Studio
Sends automatic booking confirmations via Meta WhatsApp Cloud API.
"""

import os
import logging
import sys
import requests

# Configure logging for Railway
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s [WhatsApp] %(levelname)s: %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

# Meta WhatsApp Cloud API config
WHATSAPP_API_URL = "https://graph.facebook.com/v19.0"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_TEMPLATE_NAME = os.getenv("WHATSAPP_TEMPLATE_NAME", "booking_confirmation")
WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"


def format_phone_for_whatsapp(phone):
    """
    Format Israeli phone number to international WhatsApp format (972XXXXXXXXX).
    Accepts: 0501234567, 050-1234567, 050 123 4567, +972501234567, 972501234567
    Returns: 972XXXXXXXXX (no + prefix, as required by Meta API)
    """
    if not phone:
        return None

    # Remove spaces, dashes, parentheses
    clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")

    # Remove + prefix if present
    if clean.startswith("+"):
        clean = clean[1:]

    # If starts with 972, validate length
    if clean.startswith("972"):
        if len(clean) == 12:
            return clean
        return None

    # If starts with 0, replace with 972
    if clean.startswith("0") and len(clean) == 10:
        return "972" + clean[1:]

    return None


def send_whatsapp_booking_confirmation(booking_data):
    """
    Send booking confirmation via WhatsApp Cloud API using a pre-approved template.

    Args:
        booking_data: dict with keys: name, phone, service_he, date, time

    Returns:
        True if sent successfully, False otherwise
    """
    if not WHATSAPP_ENABLED:
        logger.info("WhatsApp is disabled (WHATSAPP_ENABLED != true). Skipping.")
        return False

    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("WhatsApp credentials not configured. Skipping.")
        return False

    # Format phone number
    phone = format_phone_for_whatsapp(booking_data.get("phone", ""))
    if not phone:
        logger.warning(f"Invalid phone number for WhatsApp: {booking_data.get('phone')}")
        return False

    # Build Hebrew day name
    days_hebrew = ['שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת', 'ראשון']
    try:
        from datetime import datetime
        date_obj = datetime.strptime(booking_data["date"], "%Y-%m-%d")
        day_name = days_hebrew[date_obj.weekday()]
        formatted_date = f"יום {day_name}, {date_obj.strftime('%d/%m/%Y')}"
    except (ValueError, KeyError):
        formatted_date = booking_data.get("date", "")

    service_name = booking_data.get("service_he", booking_data.get("service", ""))
    customer_name = booking_data.get("name", "")
    time_str = booking_data.get("time", "")

    # Meta Cloud API payload - template message
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "template",
        "template": {
            "name": WHATSAPP_TEMPLATE_NAME,
            "language": {"code": "he"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": customer_name},
                        {"type": "text", "text": service_name},
                        {"type": "text", "text": formatted_date},
                        {"type": "text", "text": time_str},
                    ]
                }
            ]
        }
    }

    try:
        logger.info(f"Sending WhatsApp to {phone} for {customer_name}...")
        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code in (200, 201):
            result = response.json()
            msg_id = result.get("messages", [{}])[0].get("id", "unknown")
            logger.info(f"WhatsApp sent successfully. Message ID: {msg_id}")
            sys.stdout.flush()
            return True
        else:
            error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
            logger.error(f"WhatsApp API error {response.status_code}: {error_data}")
            sys.stdout.flush()
            return False

    except requests.exceptions.Timeout:
        logger.error("WhatsApp API request timed out (15s)")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("WhatsApp API connection error")
        return False
    except Exception as e:
        logger.error(f"WhatsApp send failed: {str(e)}")
        return False


def send_whatsapp_text_message(phone_raw, message):
    """
    Send a free-form text message via WhatsApp (for use within 24h conversation window).

    Args:
        phone_raw: Phone number in any Israeli format
        message: Text message to send

    Returns:
        True if sent successfully, False otherwise
    """
    if not WHATSAPP_ENABLED:
        return False

    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("WhatsApp credentials not configured.")
        return False

    phone = format_phone_for_whatsapp(phone_raw)
    if not phone:
        logger.warning(f"Invalid phone number: {phone_raw}")
        return False

    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code in (200, 201):
            logger.info(f"WhatsApp text sent to {phone}")
            return True
        else:
            logger.error(f"WhatsApp text error {response.status_code}: {response.text}")
            return False

    except Exception as e:
        logger.error(f"WhatsApp text failed: {str(e)}")
        return False

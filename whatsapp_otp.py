"""
WhatsApp OTP Service - LISHAI SIMANI Beauty Studio
Handles OTP generation, storage, verification, and sending via WhatsApp.
When WHATSAPP_ENABLED=false or credentials missing, operates in mock mode (logs only).
"""

import os
import random
import string
import time
import logging
import sys
import requests

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

# ============== CONFIGURATION ==============

WHATSAPP_API_URL = "https://graph.facebook.com/v19.0"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
WHATSAPP_OTP_TEMPLATE = os.getenv("WHATSAPP_OTP_TEMPLATE", "otp_verification")
WHATSAPP_ENABLED = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"

OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300       # 5 minutes
OTP_MAX_ATTEMPTS = 3
OTP_COOLDOWN_SECONDS = 900     # 15 minutes after max attempts

# ============== IN-MEMORY OTP STORE ==============
# Structure: { normalized_phone: { code, created_at, attempts, cooldown_until } }
_otp_store = {}


def _cleanup_expired():
    """Remove expired OTP entries to prevent memory leak."""
    now = time.time()
    expired = [
        phone for phone, data in _otp_store.items()
        if now - data['created_at'] > OTP_EXPIRY_SECONDS * 3  # Keep for 3x TTL then clean
    ]
    for phone in expired:
        del _otp_store[phone]


def normalize_phone_for_whatsapp(phone):
    """
    Normalize Israeli phone to WhatsApp format (972XXXXXXXXX, no +).
    Accepts: 0501234567, 050-1234567, +972501234567, 972501234567
    """
    if not phone:
        return None
    clean = phone.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if clean.startswith("+"):
        clean = clean[1:]
    if clean.startswith("972"):
        if len(clean) == 12:
            return clean
        return None
    if clean.startswith("0") and len(clean) == 10:
        return "972" + clean[1:]
    return None


# ============== OTP GENERATION & STORAGE ==============

def generate_otp():
    """Generate a secure 6-digit OTP code."""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def request_otp(phone):
    """
    Generate and send OTP for a phone number.

    Returns:
        dict with keys: success (bool), error (str or None), mock (bool)
    """
    _cleanup_expired()

    phone_norm = normalize_phone_for_whatsapp(phone)
    if not phone_norm:
        logger.warning("[WhatsApp][OTP] Invalid phone number: %s", phone)
        return {"success": False, "error": "מספר טלפון לא תקין"}

    now = time.time()

    # Check cooldown
    existing = _otp_store.get(phone_norm)
    if existing and existing.get('cooldown_until') and now < existing['cooldown_until']:
        remaining = int(existing['cooldown_until'] - now)
        minutes = remaining // 60 + 1
        logger.warning("[WhatsApp][OTP] Phone %s in cooldown for %d more minutes", phone_norm, minutes)
        return {
            "success": False,
            "error": f"יותר מדי ניסיונות. נסי שוב בעוד {minutes} דקות"
        }

    # Generate new OTP
    code = generate_otp()
    _otp_store[phone_norm] = {
        'code': code,
        'created_at': now,
        'attempts': 0,
        'cooldown_until': None,
    }

    logger.info("[WhatsApp][OTP] Generated OTP for %s: %s", phone_norm, code)

    # Send via WhatsApp (or mock)
    sent = _send_otp_whatsapp(phone_norm, code)

    return {
        "success": True,
        "mock": not sent,  # True if we couldn't send via WhatsApp
    }


def verify_otp(phone, code):
    """
    Verify an OTP code for a phone number.

    Returns:
        dict with keys: verified (bool), error (str or None)
    """
    phone_norm = normalize_phone_for_whatsapp(phone)
    if not phone_norm:
        return {"verified": False, "error": "מספר טלפון לא תקין"}

    stored = _otp_store.get(phone_norm)
    if not stored:
        logger.warning("[WhatsApp][OTP] No OTP found for %s", phone_norm)
        return {"verified": False, "error": "לא נשלח קוד למספר זה. שלחי קוד חדש"}

    now = time.time()

    # Check cooldown
    if stored.get('cooldown_until') and now < stored['cooldown_until']:
        remaining = int(stored['cooldown_until'] - now)
        minutes = remaining // 60 + 1
        return {"verified": False, "error": f"יותר מדי ניסיונות. נסי שוב בעוד {minutes} דקות"}

    # Check expiry
    if now - stored['created_at'] > OTP_EXPIRY_SECONDS:
        logger.info("[WhatsApp][OTP] OTP expired for %s", phone_norm)
        del _otp_store[phone_norm]
        return {"verified": False, "error": "הקוד פג תוקף. שלחי קוד חדש"}

    # Check code
    if stored['code'] != code.strip():
        stored['attempts'] += 1
        logger.warning("[WhatsApp][OTP] Wrong code for %s (attempt %d/%d)",
                       phone_norm, stored['attempts'], OTP_MAX_ATTEMPTS)

        if stored['attempts'] >= OTP_MAX_ATTEMPTS:
            stored['cooldown_until'] = now + OTP_COOLDOWN_SECONDS
            logger.warning("[WhatsApp][OTP] Max attempts reached for %s, cooldown set", phone_norm)
            return {
                "verified": False,
                "error": "יותר מדי ניסיונות שגויים. נסי שוב בעוד 15 דקות"
            }

        remaining = OTP_MAX_ATTEMPTS - stored['attempts']
        return {"verified": False, "error": f"קוד שגוי. נותרו {remaining} ניסיונות"}

    # Success
    logger.info("[WhatsApp][OTP] OTP verified successfully for %s", phone_norm)
    del _otp_store[phone_norm]
    return {"verified": True}


# ============== WHATSAPP SENDING (MOCK-READY) ==============

def _send_otp_whatsapp(phone_norm, code):
    """
    Send OTP via WhatsApp Cloud API.
    If WHATSAPP_ENABLED=false or credentials missing, logs the code (mock mode).

    Returns:
        True if sent via WhatsApp, False if mocked.
    """
    if not WHATSAPP_ENABLED:
        logger.info("[WhatsApp][OTP] MOCK MODE - Code for %s: %s (WhatsApp disabled)", phone_norm, code)
        sys.stdout.flush()
        return False

    if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
        logger.info("[WhatsApp][OTP] MOCK MODE - Code for %s: %s (credentials missing)", phone_norm, code)
        sys.stdout.flush()
        return False

    # ===== REAL WHATSAPP SEND =====
    # This is where Meta Cloud API sends the OTP template message.
    # When you have approved templates, this will work as-is.

    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone_norm,
        "type": "template",
        "template": {
            "name": WHATSAPP_OTP_TEMPLATE,
            "language": {"code": "he"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": code},
                    ]
                }
            ]
        }
    }

    try:
        logger.info("[WhatsApp][OTP] Sending OTP to %s via WhatsApp...", phone_norm)
        response = requests.post(url, json=payload, headers=headers, timeout=15)

        if response.status_code in (200, 201):
            result = response.json()
            msg_id = result.get("messages", [{}])[0].get("id", "unknown")
            logger.info("[WhatsApp][OTP] OTP sent successfully. Message ID: %s", msg_id)
            sys.stdout.flush()
            return True
        else:
            error_data = response.text
            logger.error("[WhatsApp][OTP] API error %d: %s", response.status_code, error_data)
            # Fall back to mock mode - still log the code for development
            logger.info("[WhatsApp][OTP] FALLBACK MOCK - Code for %s: %s", phone_norm, code)
            sys.stdout.flush()
            return False

    except requests.exceptions.Timeout:
        logger.error("[WhatsApp][OTP] Request timed out")
        logger.info("[WhatsApp][OTP] FALLBACK MOCK - Code for %s: %s", phone_norm, code)
        return False
    except Exception as e:
        logger.error("[WhatsApp][OTP] Send failed: %s", str(e))
        logger.info("[WhatsApp][OTP] FALLBACK MOCK - Code for %s: %s", phone_norm, code)
        return False

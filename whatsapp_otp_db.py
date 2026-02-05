"""
WhatsApp OTP Service - DATABASE VERSION - LISHAI SIMANI Beauty Studio
Handles OTP generation, storage in PostgreSQL, verification, and sending via WhatsApp.
When WHATSAPP_ENABLED=false or credentials missing, operates in mock mode (logs only).
"""

import os
import random
import string
import logging
import sys
import requests
from datetime import datetime, timedelta
from db_service import execute_query

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
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 3
OTP_COOLDOWN_MINUTES = 15


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
    Stores OTP in PostgreSQL database.

    Returns:
        dict with keys: success (bool), error (str or None), mock (bool)
    """
    phone_norm = normalize_phone_for_whatsapp(phone)
    if not phone_norm:
        logger.warning("[WhatsApp][OTP] Invalid phone number: %s", phone)
        return {"success": False, "error": "מספר טלפון לא תקין"}

    try:
        # Check for existing cooldown
        existing = execute_query(
            """
            SELECT cooldown_until FROM otp_codes
            WHERE phone = %s
            AND cooldown_until IS NOT NULL
            AND cooldown_until > NOW()
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (phone_norm,),
            fetch_one=True
        )

        if existing:
            cooldown_until = existing['cooldown_until']
            remaining_seconds = (cooldown_until - datetime.now()).total_seconds()
            minutes = int(remaining_seconds // 60) + 1
            logger.warning("[WhatsApp][OTP] Phone %s in cooldown for %d more minutes", phone_norm, minutes)
            return {
                "success": False,
                "error": f"יותר מדי ניסיונות. נסי שוב בעוד {minutes} דקות"
            }

        # Clean up any old codes for this phone
        execute_query("DELETE FROM otp_codes WHERE phone = %s", (phone_norm,))

        # Generate new OTP
        code = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        # Insert into database
        execute_query(
            """
            INSERT INTO otp_codes (phone, code, expires_at, attempts, verified, cooldown_until)
            VALUES (%s, %s, %s, 0, FALSE, NULL)
            """,
            (phone_norm, code, expires_at)
        )

        logger.info("[WhatsApp][OTP] Generated OTP for %s: %s", phone_norm, code)

        # Send via WhatsApp (or mock)
        sent = _send_otp_whatsapp(phone_norm, code)

        return {
            "success": True,
            "mock": not sent,  # True if we couldn't send via WhatsApp
        }

    except Exception as e:
        logger.error(f"[WhatsApp][OTP] Error generating OTP: {str(e)}")
        return {"success": False, "error": "שגיאה טכנית. נסי שוב"}


def verify_otp(phone, code):
    """
    Verify an OTP code for a phone number.
    Updates attempts counter and handles cooldown in database.

    Returns:
        dict with keys: verified (bool), error (str or None)
    """
    phone_norm = normalize_phone_for_whatsapp(phone)
    if not phone_norm:
        return {"verified": False, "error": "מספר טלפון לא תקין"}

    try:
        # Get the most recent OTP for this phone
        stored = execute_query(
            """
            SELECT id, code, expires_at, attempts, cooldown_until
            FROM otp_codes
            WHERE phone = %s
            AND verified = FALSE
            ORDER BY created_at DESC
            LIMIT 1
            """,
            (phone_norm,),
            fetch_one=True
        )

        if not stored:
            logger.warning("[WhatsApp][OTP] No OTP found for %s", phone_norm)
            return {"verified": False, "error": "לא נשלח קוד למספר זה. שלחי קוד חדש"}

        # Check cooldown
        if stored['cooldown_until'] and stored['cooldown_until'] > datetime.now():
            remaining_seconds = (stored['cooldown_until'] - datetime.now()).total_seconds()
            minutes = int(remaining_seconds // 60) + 1
            return {"verified": False, "error": f"יותר מדי ניסיונות. נסי שוב בעוד {minutes} דקות"}

        # Check expiry
        if stored['expires_at'] < datetime.now():
            logger.info("[WhatsApp][OTP] OTP expired for %s", phone_norm)
            execute_query("DELETE FROM otp_codes WHERE id = %s", (stored['id'],))
            return {"verified": False, "error": "הקוד פג תוקף. שלחי קוד חדש"}

        # Check code
        if stored['code'] != code.strip():
            new_attempts = stored['attempts'] + 1
            logger.warning("[WhatsApp][OTP] Wrong code for %s (attempt %d/%d)",
                           phone_norm, new_attempts, OTP_MAX_ATTEMPTS)

            if new_attempts >= OTP_MAX_ATTEMPTS:
                # Set cooldown
                cooldown_until = datetime.now() + timedelta(minutes=OTP_COOLDOWN_MINUTES)
                execute_query(
                    "UPDATE otp_codes SET attempts = %s, cooldown_until = %s WHERE id = %s",
                    (new_attempts, cooldown_until, stored['id'])
                )
                logger.warning("[WhatsApp][OTP] Max attempts reached for %s, cooldown set", phone_norm)
                return {
                    "verified": False,
                    "error": "יותר מדי ניסיונות שגויים. נסי שוב בעוד 15 דקות"
                }

            # Increment attempts
            execute_query(
                "UPDATE otp_codes SET attempts = %s WHERE id = %s",
                (new_attempts, stored['id'])
            )

            remaining = OTP_MAX_ATTEMPTS - new_attempts
            return {"verified": False, "error": f"קוד שגוי. נותרו {remaining} ניסיונות"}

        # Success - mark as verified and delete
        logger.info("[WhatsApp][OTP] OTP verified successfully for %s", phone_norm)
        execute_query("DELETE FROM otp_codes WHERE id = %s", (stored['id'],))
        return {"verified": True}

    except Exception as e:
        logger.error(f"[WhatsApp][OTP] Verification error: {str(e)}")
        return {"verified": False, "error": "שגיאה טכנית. נסי שוב"}


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

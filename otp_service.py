"""
OTP Service - LISHAI SIMANI Beauty Studio
Handles OTP generation, storage in PostgreSQL, verification,
and sending via ActiveTrail SMS (through sms_service.send_sms).

When SMS_ENABLED=false or API key missing, operates in mock mode (logs code to stdout).

NOTE: All phone numbers are stored in E.164 format (+972XXXXXXXXX)
"""

import os
import random
import string
import logging
import sys
from datetime import datetime, timedelta
from db_service import execute_query
from phone_utils import normalize_israeli_phone
from sms_service import send_sms

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
if not logger.handlers:
    logger.addHandler(handler)

# ============== CONFIGURATION ==============

OTP_LENGTH = 6
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 3
OTP_COOLDOWN_MINUTES = 15


def normalize_phone(phone):
    """
    Normalize phone to E.164 format (+972XXXXXXXXX).
    Used for both storage and SMS sending.
    """
    return normalize_israeli_phone(phone)


# ============== OTP GENERATION & STORAGE ==============

def generate_otp():
    """Generate a secure 6-digit OTP code."""
    return ''.join(random.choices(string.digits, k=OTP_LENGTH))


def request_otp(phone):
    """
    Generate and send OTP for a phone number via ActiveTrail SMS.
    Stores OTP in PostgreSQL database.

    Returns:
        dict with keys: success (bool), error (str or None), mock (bool)
    """
    phone_storage = normalize_phone(phone)
    if not phone_storage:
        logger.warning("[OTP] Invalid phone number: %s", phone)
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
            (phone_storage,),
            fetch_one=True
        )

        if existing:
            cooldown_until = existing['cooldown_until']
            remaining_seconds = (cooldown_until - datetime.now()).total_seconds()
            minutes = int(remaining_seconds // 60) + 1
            logger.warning("[OTP] Phone %s in cooldown for %d more minutes", phone_storage, minutes)
            return {
                "success": False,
                "error": f"יותר מדי ניסיונות. נסי שוב בעוד {minutes} דקות"
            }

        # Clean up any old codes for this phone
        execute_query("DELETE FROM otp_codes WHERE phone = %s", (phone_storage,))

        # Generate new OTP
        code = generate_otp()
        expires_at = datetime.now() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        # Insert into database
        execute_query(
            """
            INSERT INTO otp_codes (phone, code, expires_at, attempts, verified, cooldown_until)
            VALUES (%s, %s, %s, 0, FALSE, NULL)
            """,
            (phone_storage, code, expires_at)
        )

        logger.info("[OTP] Generated OTP for %s: %s", phone_storage, code)

        # Send via ActiveTrail SMS (or mock)
        message = f"קוד האימות שלך ב-LISHAI SIMANI: {code}\nתוקף: 5 דקות."
        sent = send_sms(phone_storage, message)

        if not sent:
            logger.info("[OTP] MOCK/FALLBACK - Code for %s: %s", phone_storage, code)
            sys.stdout.flush()

        return {
            "success": True,
            "mock": not sent,  # True if SMS was not actually sent
        }

    except Exception as e:
        logger.error("[OTP] Error generating OTP: %s", e)
        return {"success": False, "error": "שגיאה טכנית. נסי שוב"}


def verify_otp(phone, code):
    """
    Verify an OTP code for a phone number.
    Updates attempts counter and handles cooldown in database.

    Returns:
        dict with keys: verified (bool), error (str or None)
    """
    phone_storage = normalize_phone(phone)
    if not phone_storage:
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
            (phone_storage,),
            fetch_one=True
        )

        if not stored:
            logger.warning("[OTP] No OTP found for %s", phone_storage)
            return {"verified": False, "error": "לא נשלח קוד למספר זה. שלחי קוד חדש"}

        # Check cooldown
        if stored['cooldown_until'] and stored['cooldown_until'] > datetime.now():
            remaining_seconds = (stored['cooldown_until'] - datetime.now()).total_seconds()
            minutes = int(remaining_seconds // 60) + 1
            return {"verified": False, "error": f"יותר מדי ניסיונות. נסי שוב בעוד {minutes} דקות"}

        # Check expiry
        if stored['expires_at'] < datetime.now():
            logger.info("[OTP] OTP expired for %s", phone_storage)
            execute_query("DELETE FROM otp_codes WHERE id = %s", (stored['id'],))
            return {"verified": False, "error": "הקוד פג תוקף. שלחי קוד חדש"}

        # Check code
        if stored['code'] != code.strip():
            new_attempts = stored['attempts'] + 1
            logger.warning("[OTP] Wrong code for %s (attempt %d/%d)",
                           phone_storage, new_attempts, OTP_MAX_ATTEMPTS)

            if new_attempts >= OTP_MAX_ATTEMPTS:
                # Set cooldown
                cooldown_until = datetime.now() + timedelta(minutes=OTP_COOLDOWN_MINUTES)
                execute_query(
                    "UPDATE otp_codes SET attempts = %s, cooldown_until = %s WHERE id = %s",
                    (new_attempts, cooldown_until, stored['id'])
                )
                logger.warning("[OTP] Max attempts reached for %s, cooldown set", phone_storage)
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
        logger.info("[OTP] OTP verified successfully for %s", phone_storage)
        execute_query("DELETE FROM otp_codes WHERE id = %s", (stored['id'],))
        return {"verified": True}

    except Exception as e:
        logger.error("[OTP] Verification error: %s", e)
        return {"verified": False, "error": "שגיאה טכנית. נסי שוב"}

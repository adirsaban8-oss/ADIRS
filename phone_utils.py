"""
Phone Utilities - LISHAI SIMANI Beauty Studio
Centralized phone number normalization for Israeli numbers.

ALL phone numbers in the system use E.164 format: +972XXXXXXXXX
This ensures consistency across OTP, SMS, database storage, and API calls.
"""

import re
import logging

logger = logging.getLogger(__name__)


def normalize_israeli_phone(phone):
    """
    Normalize any Israeli phone number to E.164 format (+972XXXXXXXXX).

    Accepts:
        - 0501234567      -> +972501234567
        - 050-123-4567    -> +972501234567
        - 050 123 4567    -> +972501234567
        - 972501234567    -> +972501234567
        - +972501234567   -> +972501234567
        - +972-50-123-4567 -> +972501234567

    Returns:
        str: Phone in +972XXXXXXXXX format, or None if invalid.
    """
    if not phone:
        return None

    # Remove all non-digit characters except leading +
    clean = re.sub(r'[^\d+]', '', str(phone))

    # Remove leading + for processing
    if clean.startswith('+'):
        clean = clean[1:]

    # Case 1: Already has 972 prefix (12 digits after removing +)
    if clean.startswith('972'):
        if len(clean) == 12:
            return '+' + clean
        else:
            logger.warning(f"[Phone] Invalid 972 format (wrong length): {phone}")
            return None

    # Case 2: Israeli local format (starts with 0, 10 digits)
    if clean.startswith('0') and len(clean) == 10:
        return '+972' + clean[1:]

    # Case 3: Israeli format without leading 0 (9 digits, starts with 5)
    if clean.startswith('5') and len(clean) == 9:
        return '+972' + clean

    logger.warning(f"[Phone] Could not normalize phone: {phone}")
    return None


def format_phone_display(phone):
    """
    Format E.164 phone for display: +972-50-123-4567

    Args:
        phone: Phone in any format

    Returns:
        str: Formatted display string, or original if can't normalize
    """
    normalized = normalize_israeli_phone(phone)
    if not normalized:
        return phone or ''

    # +972501234567 -> +972-50-123-4567
    digits = normalized[4:]  # Remove +972
    if len(digits) == 9:
        return f"+972-{digits[:2]}-{digits[2:5]}-{digits[5:]}"

    return normalized


def format_phone_local(phone):
    """
    Format phone for local Israeli display: 050-123-4567

    Args:
        phone: Phone in any format

    Returns:
        str: Local format string, or original if can't normalize
    """
    normalized = normalize_israeli_phone(phone)
    if not normalized:
        return phone or ''

    # +972501234567 -> 050-123-4567
    digits = normalized[4:]  # Remove +972
    if len(digits) == 9:
        return f"0{digits[:2]}-{digits[2:5]}-{digits[5:]}"

    return normalized


def is_valid_israeli_phone(phone):
    """
    Check if a phone number is a valid Israeli mobile number.

    Returns:
        bool: True if valid Israeli mobile number
    """
    normalized = normalize_israeli_phone(phone)
    if not normalized:
        return False

    # Israeli mobile prefixes: 050, 051, 052, 053, 054, 055, 058
    mobile_prefixes = ['50', '51', '52', '53', '54', '55', '58']
    prefix = normalized[4:6]  # After +972

    return prefix in mobile_prefixes

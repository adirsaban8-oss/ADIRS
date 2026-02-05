"""
Appointment Service - LISHAI SIMANI Beauty Studio
Handles appointments in PostgreSQL with Google Calendar sync
"""

import logging
from datetime import datetime, timedelta
from db_service import execute_query
import pytz

logger = logging.getLogger(__name__)

ISRAEL_TZ = pytz.timezone('Asia/Jerusalem')


def create_appointment(customer_id, service_name, service_name_he, datetime_str, time_str, duration, notes='', google_event_id=None):
    """
    Create a new appointment.

    Args:
        customer_id: Customer UUID
        service_name: Service name in English
        service_name_he: Service name in Hebrew
        datetime_str: Date string (YYYY-MM-DD)
        time_str: Time string (HH:MM)
        duration: Duration in minutes
        notes: Optional notes
        google_event_id: Google Calendar event ID (if created)

    Returns:
        Appointment dict or None
    """
    try:
        # Parse datetime
        appointment_datetime = datetime.strptime(f"{datetime_str} {time_str}", "%Y-%m-%d %H:%M")

        # Validate: must be in the future
        now = datetime.now()
        if appointment_datetime <= now:
            logger.error("Appointment datetime must be in the future")
            return None

        # Validate: max 30 days in advance
        max_date = now + timedelta(days=30)
        if appointment_datetime > max_date:
            logger.error("Appointment cannot be more than 30 days in advance")
            return None

        # Insert appointment
        appointment = execute_query(
            """
            INSERT INTO appointments
            (customer_id, service_name, service_name_he, datetime, duration, status, google_event_id, notes)
            VALUES (%s, %s, %s, %s, %s, 'active', %s, %s)
            RETURNING id, customer_id, service_name, service_name_he, datetime, duration,
                      status, google_event_id, notes, created_at
            """,
            (customer_id, service_name, service_name_he, appointment_datetime, duration, google_event_id, notes),
            fetch_one=True
        )

        logger.info(f"Created appointment: {appointment['id']} for customer {customer_id}")
        return appointment

    except Exception as e:
        logger.error(f"Error creating appointment: {str(e)}")
        return None


def get_customer_future_appointments(customer_id):
    """
    Get all future active appointments for a customer.

    Args:
        customer_id: Customer UUID

    Returns:
        List of appointment dicts
    """
    try:
        appointments = execute_query(
            """
            SELECT id, customer_id, service_name, service_name_he, datetime, duration,
                   status, google_event_id, notes, created_at
            FROM appointments
            WHERE customer_id = %s
            AND status = 'active'
            AND datetime > NOW()
            ORDER BY datetime ASC
            """,
            (customer_id,),
            fetch_all=True
        )
        return appointments or []
    except Exception as e:
        logger.error(f"Error fetching customer appointments: {str(e)}")
        return []


def get_customer_past_appointments(customer_id, limit=10):
    """
    Get past appointments for a customer.

    Args:
        customer_id: Customer UUID
        limit: Maximum number to return

    Returns:
        List of appointment dicts
    """
    try:
        appointments = execute_query(
            """
            SELECT id, customer_id, service_name, service_name_he, datetime, duration,
                   status, google_event_id, notes, created_at
            FROM appointments
            WHERE customer_id = %s
            AND datetime <= NOW()
            ORDER BY datetime DESC
            LIMIT %s
            """,
            (customer_id, limit),
            fetch_all=True
        )
        return appointments or []
    except Exception as e:
        logger.error(f"Error fetching past appointments: {str(e)}")
        return []


def has_active_future_appointment(customer_id):
    """
    Check if customer has an active future appointment.
    Business rule: only one active future appointment allowed.

    Args:
        customer_id: Customer UUID

    Returns:
        Appointment dict if exists, None otherwise
    """
    try:
        appointment = execute_query(
            """
            SELECT id, customer_id, service_name, service_name_he, datetime, duration,
                   status, google_event_id, notes
            FROM appointments
            WHERE customer_id = %s
            AND status = 'active'
            AND datetime > NOW()
            ORDER BY datetime ASC
            LIMIT 1
            """,
            (customer_id,),
            fetch_one=True
        )
        return appointment
    except Exception as e:
        logger.error(f"Error checking active appointments: {str(e)}")
        return None


def cancel_appointment(appointment_id):
    """
    Cancel an appointment by setting status to 'cancelled'.

    Args:
        appointment_id: Appointment UUID

    Returns:
        Updated appointment dict or None
    """
    try:
        appointment = execute_query(
            """
            UPDATE appointments
            SET status = 'cancelled', updated_at = NOW()
            WHERE id = %s
            RETURNING id, customer_id, service_name, service_name_he, datetime, duration,
                      status, google_event_id, notes
            """,
            (appointment_id,),
            fetch_one=True
        )

        if appointment:
            logger.info(f"Cancelled appointment: {appointment_id}")

        return appointment

    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        return None


def complete_appointment(appointment_id):
    """
    Mark an appointment as completed.

    Args:
        appointment_id: Appointment UUID

    Returns:
        Updated appointment dict or None
    """
    try:
        appointment = execute_query(
            """
            UPDATE appointments
            SET status = 'completed', updated_at = NOW()
            WHERE id = %s
            RETURNING id, customer_id, service_name, service_name_he, datetime, duration,
                      status, google_event_id, notes
            """,
            (appointment_id,),
            fetch_one=True
        )

        if appointment:
            logger.info(f"Completed appointment: {appointment_id}")

        return appointment

    except Exception as e:
        logger.error(f"Error completing appointment: {str(e)}")
        return None


def get_appointment_by_id(appointment_id):
    """
    Get appointment details by ID.

    Args:
        appointment_id: Appointment UUID

    Returns:
        Appointment dict or None
    """
    try:
        appointment = execute_query(
            """
            SELECT a.id, a.customer_id, a.service_name, a.service_name_he, a.datetime,
                   a.duration, a.status, a.google_event_id, a.notes, a.created_at,
                   c.name as customer_name, c.phone as customer_phone, c.email as customer_email
            FROM appointments a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.id = %s
            """,
            (appointment_id,),
            fetch_one=True
        )
        return appointment
    except Exception as e:
        logger.error(f"Error fetching appointment: {str(e)}")
        return None


def get_appointments_for_date(date_str):
    """
    Get all appointments for a specific date.
    Used for checking availability and admin views.

    Args:
        date_str: Date string (YYYY-MM-DD)

    Returns:
        List of appointment dicts
    """
    try:
        start_datetime = datetime.strptime(date_str, "%Y-%m-%d")
        end_datetime = start_datetime + timedelta(days=1)

        appointments = execute_query(
            """
            SELECT a.id, a.customer_id, a.service_name, a.service_name_he, a.datetime,
                   a.duration, a.status, a.google_event_id, a.notes,
                   c.name as customer_name, c.phone as customer_phone
            FROM appointments a
            JOIN customers c ON a.customer_id = c.id
            WHERE a.datetime >= %s AND a.datetime < %s
            AND a.status = 'active'
            ORDER BY a.datetime ASC
            """,
            (start_datetime, end_datetime),
            fetch_all=True
        )
        return appointments or []
    except Exception as e:
        logger.error(f"Error fetching appointments for date: {str(e)}")
        return []


def get_appointments_needing_reminders():
    """
    Get appointments that need reminders sent.
    - Day before reminder: appointments tomorrow at 20:00
    - Morning reminder: appointments today at 08:00

    Returns:
        Dict with 'day_before' and 'morning' lists
    """
    try:
        now = datetime.now(ISRAEL_TZ)
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # Day before reminders (for tomorrow)
        day_before = execute_query(
            """
            SELECT a.id, a.datetime, a.service_name_he, a.google_event_id,
                   c.name as customer_name, c.phone as customer_phone, c.email as customer_email
            FROM appointments a
            JOIN customers c ON a.customer_id = c.id
            WHERE DATE(a.datetime) = %s
            AND a.status = 'active'
            ORDER BY a.datetime ASC
            """,
            (tomorrow,),
            fetch_all=True
        )

        # Morning reminders (for today)
        morning = execute_query(
            """
            SELECT a.id, a.datetime, a.service_name_he, a.google_event_id,
                   c.name as customer_name, c.phone as customer_phone, c.email as customer_email
            FROM appointments a
            JOIN customers c ON a.customer_id = c.id
            WHERE DATE(a.datetime) = %s
            AND a.status = 'active'
            ORDER BY a.datetime ASC
            """,
            (today,),
            fetch_all=True
        )

        return {
            'day_before': day_before or [],
            'morning': morning or []
        }

    except Exception as e:
        logger.error(f"Error fetching reminders: {str(e)}")
        return {'day_before': [], 'morning': []}


def update_google_event_id(appointment_id, google_event_id):
    """
    Update the Google Calendar event ID for an appointment.

    Args:
        appointment_id: Appointment UUID
        google_event_id: Google Calendar event ID

    Returns:
        True if updated, False otherwise
    """
    try:
        execute_query(
            "UPDATE appointments SET google_event_id = %s WHERE id = %s",
            (google_event_id, appointment_id)
        )
        logger.info(f"Updated Google event ID for appointment {appointment_id}")
        return True
    except Exception as e:
        logger.error(f"Error updating Google event ID: {str(e)}")
        return False


def get_all_appointments(limit=100, offset=0, status=None):
    """
    Get all appointments with optional status filter.
    Used for admin views.

    Args:
        limit: Maximum number to return
        offset: Number to skip
        status: Filter by status ('active', 'cancelled', 'completed')

    Returns:
        List of appointment dicts with customer info
    """
    try:
        if status:
            query = """
                SELECT a.id, a.customer_id, a.service_name, a.service_name_he, a.datetime,
                       a.duration, a.status, a.google_event_id, a.notes, a.created_at,
                       c.name as customer_name, c.phone as customer_phone, c.email as customer_email
                FROM appointments a
                JOIN customers c ON a.customer_id = c.id
                WHERE a.status = %s
                ORDER BY a.datetime DESC
                LIMIT %s OFFSET %s
            """
            params = (status, limit, offset)
        else:
            query = """
                SELECT a.id, a.customer_id, a.service_name, a.service_name_he, a.datetime,
                       a.duration, a.status, a.google_event_id, a.notes, a.created_at,
                       c.name as customer_name, c.phone as customer_phone, c.email as customer_email
                FROM appointments a
                JOIN customers c ON a.customer_id = c.id
                ORDER BY a.datetime DESC
                LIMIT %s OFFSET %s
            """
            params = (limit, offset)

        appointments = execute_query(query, params, fetch_all=True)
        return appointments or []

    except Exception as e:
        logger.error(f"Error fetching all appointments: {str(e)}")
        return []

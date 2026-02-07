"""
Customer Service - LISHAI SIMANI Beauty Studio
Handles customer registration, lookup, and management in PostgreSQL

NOTE: All phone numbers are stored in E.164 format (+972XXXXXXXXX)
"""

import logging
from db_service import execute_query
from phone_utils import normalize_israeli_phone

logger = logging.getLogger(__name__)


def normalize_phone(phone):
    """
    Normalize phone number to E.164 format (+972XXXXXXXXX).
    Wrapper for centralized phone_utils.normalize_israeli_phone.
    """
    return normalize_israeli_phone(phone)


def customer_exists(phone):
    """
    Check if a customer exists by phone number.

    Args:
        phone: Phone number (any format)

    Returns:
        True if customer exists, False otherwise
    """
    phone_norm = normalize_phone(phone)
    if not phone_norm:
        return False

    try:
        result = execute_query(
            "SELECT id FROM customers WHERE phone = %s",
            (phone_norm,),
            fetch_one=True
        )
        return result is not None
    except Exception as e:
        logger.error(f"Error checking customer existence: {str(e)}")
        return False


def get_customer_by_phone(phone):
    """
    Get customer details by phone number.

    Args:
        phone: Phone number (any format)

    Returns:
        Customer dict with keys: id, name, phone, email, created_at
        or None if not found
    """
    phone_norm = normalize_phone(phone)
    if not phone_norm:
        return None

    try:
        customer = execute_query(
            """
            SELECT id, name, phone, email, created_at, updated_at
            FROM customers
            WHERE phone = %s
            """,
            (phone_norm,),
            fetch_one=True
        )
        return customer
    except Exception as e:
        logger.error(f"Error fetching customer: {str(e)}")
        return None


def create_customer(name, phone, email):
    """
    Create a new customer.

    Args:
        name: Customer full name
        phone: Phone number (any format, will be normalized)
        email: Email address

    Returns:
        Customer dict with keys: id, name, phone, email, created_at
        or None if creation failed
    """
    phone_norm = normalize_phone(phone)
    if not phone_norm:
        logger.error(f"Invalid phone format: {phone}")
        return None

    # Validate inputs
    if not name or len(name.strip()) < 2:
        logger.error("Invalid name")
        return None

    if not email or '@' not in email:
        logger.error("Invalid email")
        return None

    try:
        # Check if customer already exists
        existing = get_customer_by_phone(phone_norm)
        if existing:
            logger.warning(f"Customer already exists with phone {phone_norm}")
            return existing

        # Insert new customer
        customer = execute_query(
            """
            INSERT INTO customers (name, phone, email)
            VALUES (%s, %s, %s)
            RETURNING id, name, phone, email, created_at
            """,
            (name.strip(), phone_norm, email.strip().lower()),
            fetch_one=True
        )

        logger.info(f"Created new customer: {customer['id']} - {customer['name']}")
        return customer

    except Exception as e:
        logger.error(f"Error creating customer: {str(e)}")
        return None


def update_customer(customer_id, name=None, email=None):
    """
    Update customer details.
    Phone cannot be updated (use it as unique identifier).

    Args:
        customer_id: Customer UUID
        name: New name (optional)
        email: New email (optional)

    Returns:
        Updated customer dict or None
    """
    if not customer_id:
        return None

    updates = []
    params = []

    if name and len(name.strip()) >= 2:
        updates.append("name = %s")
        params.append(name.strip())

    if email and '@' in email:
        updates.append("email = %s")
        params.append(email.strip().lower())

    if not updates:
        logger.warning("No valid fields to update")
        return None

    updates.append("updated_at = NOW()")
    params.append(customer_id)

    try:
        query = f"""
            UPDATE customers
            SET {', '.join(updates)}
            WHERE id = %s
            RETURNING id, name, phone, email, created_at, updated_at
        """

        customer = execute_query(query, tuple(params), fetch_one=True)

        if customer:
            logger.info(f"Updated customer: {customer_id}")

        return customer

    except Exception as e:
        logger.error(f"Error updating customer: {str(e)}")
        return None


def get_all_customers(limit=100, offset=0):
    """
    Get all customers with pagination.

    Args:
        limit: Maximum number of customers to return
        offset: Number of customers to skip

    Returns:
        List of customer dicts
    """
    try:
        customers = execute_query(
            """
            SELECT id, name, phone, email, created_at
            FROM customers
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            (limit, offset),
            fetch_all=True
        )
        return customers or []
    except Exception as e:
        logger.error(f"Error fetching customers: {str(e)}")
        return []


def search_customers(search_term):
    """
    Search customers by name or phone.

    Args:
        search_term: Text to search for

    Returns:
        List of matching customer dicts
    """
    if not search_term or len(search_term.strip()) < 2:
        return []

    search = f"%{search_term.strip()}%"

    try:
        customers = execute_query(
            """
            SELECT id, name, phone, email, created_at
            FROM customers
            WHERE name ILIKE %s OR phone LIKE %s
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (search, search),
            fetch_all=True
        )
        return customers or []
    except Exception as e:
        logger.error(f"Error searching customers: {str(e)}")
        return []


def get_customer_count():
    """
    Get total number of customers.

    Returns:
        Integer count
    """
    try:
        result = execute_query(
            "SELECT COUNT(*) as count FROM customers",
            fetch_one=True
        )
        return result['count'] if result else 0
    except Exception as e:
        logger.error(f"Error counting customers: {str(e)}")
        return 0

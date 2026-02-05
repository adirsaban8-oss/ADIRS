"""
Database Service - LISHAI SIMANI Beauty Studio
PostgreSQL connection handling and common database operations
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Connection pool
_connection_pool = None


def init_db_pool():
    """Initialize the database connection pool."""
    global _connection_pool

    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        logger.warning("DATABASE_URL not set. Database features will be disabled.")
        return False

    try:
        # Railway and some providers use postgres:// but psycopg2 needs postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)

        _connection_pool = SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=database_url
        )
        logger.info("Database connection pool initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database pool: {str(e)}")
        return False


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Automatically returns connection to pool when done.
    """
    if not _connection_pool:
        raise Exception("Database pool not initialized. Call init_db_pool() first.")

    conn = _connection_pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        _connection_pool.putconn(conn)


@contextmanager
def get_db_cursor(cursor_factory=RealDictCursor):
    """
    Context manager for database cursor.
    Returns dict-like rows by default.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        finally:
            cursor.close()


def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    """
    Execute a database query with automatic connection handling.

    Args:
        query: SQL query string
        params: Query parameters (tuple or dict)
        fetch_one: Return single row
        fetch_all: Return all rows

    Returns:
        Query results or None
    """
    try:
        with get_db_cursor() as cursor:
            cursor.execute(query, params or ())

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()

            return None
    except Exception as e:
        logger.error(f"Query execution error: {str(e)}")
        raise


def is_db_available():
    """Check if database is available and connected."""
    if not _connection_pool:
        return False

    try:
        with get_db_cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception:
        return False


def run_migrations():
    """
    Run database migrations to set up schema.
    Safe to run multiple times (uses CREATE TABLE IF NOT EXISTS).
    """
    migrations = [
        # Customers table
        """
        CREATE TABLE IF NOT EXISTS customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL UNIQUE,
            email VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # Appointments table
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
            service_name VARCHAR(50) NOT NULL,
            service_name_he VARCHAR(50) NOT NULL,
            datetime TIMESTAMP NOT NULL,
            duration INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'cancelled', 'completed')),
            google_event_id VARCHAR(255),
            notes TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # OTP codes table
        """
        CREATE TABLE IF NOT EXISTS otp_codes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            phone VARCHAR(20) NOT NULL,
            code VARCHAR(6) NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            verified BOOLEAN DEFAULT FALSE,
            attempts INTEGER DEFAULT 0,
            cooldown_until TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """,

        # Indexes
        """
        CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_appointments_customer ON appointments(customer_id)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_appointments_datetime ON appointments(datetime)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_otp_phone ON otp_codes(phone)
        """,
        """
        CREATE INDEX IF NOT EXISTS idx_otp_expires ON otp_codes(expires_at)
        """
    ]

    try:
        with get_db_cursor() as cursor:
            for migration in migrations:
                cursor.execute(migration)

        logger.info("Database migrations completed successfully")
        return True
    except Exception as e:
        logger.error(f"Migration error: {str(e)}")
        return False


def cleanup_expired_otp():
    """Remove expired OTP codes from the database."""
    query = "DELETE FROM otp_codes WHERE expires_at < NOW()"
    try:
        execute_query(query)
        logger.info("Cleaned up expired OTP codes")
    except Exception as e:
        logger.error(f"OTP cleanup error: {str(e)}")

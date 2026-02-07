"""
Database Service - LISHAI SIMANI Beauty Studio
PostgreSQL connection handling and common database operations

IMPORTANT: Database pool initialization MUST happen at module-level (global scope)
in app.py, NOT inside `if __name__ == "__main__"`. This is required because:
- Gunicorn imports the app module but doesn't execute __main__ blocks
- Railway runs the app via Gunicorn in production
- Each Gunicorn worker process needs its own connection pool
- The pool must be ready BEFORE any route or service tries to use the database
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool
import logging
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

# Connection pool - initialized once per process
_connection_pool = None
_pool_lock = threading.Lock()
_pool_initialized = False


def init_db_pool():
    """
    Initialize the database connection pool.

    This function is IDEMPOTENT - safe to call multiple times.
    Uses a lock to prevent race conditions in multi-threaded environments.
    Must be called at module-level in app.py for Gunicorn compatibility.
    """
    global _connection_pool, _pool_initialized

    # Fast path: already initialized
    if _pool_initialized and _connection_pool is not None:
        return True

    with _pool_lock:
        # Double-check after acquiring lock
        if _pool_initialized and _connection_pool is not None:
            return True

        database_url = os.getenv('DATABASE_URL')

        if not database_url:
            logger.warning("DATABASE_URL not set. Database features will be disabled.")
            print("[Database] WARNING: DATABASE_URL not set", file=sys.stderr)
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
            _pool_initialized = True
            logger.info("Database connection pool initialized successfully")
            print("[Database] Connection pool initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {str(e)}")
            print(f"[Database] ERROR: Failed to initialize pool: {str(e)}", file=sys.stderr)
            return False


def ensure_pool_initialized():
    """
    Ensure the database pool is initialized.
    Called automatically by get_db_connection if pool is not ready.
    """
    global _connection_pool, _pool_initialized

    if _pool_initialized and _connection_pool is not None:
        return True

    # Attempt to initialize if not done yet
    return init_db_pool()


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Automatically returns connection to pool when done.
    Will attempt to initialize pool if not already done.
    """
    # Ensure pool is ready before attempting to get connection
    if not _connection_pool:
        if not ensure_pool_initialized():
            raise Exception(
                "Database pool not initialized and auto-initialization failed. "
                "Check DATABASE_URL environment variable."
            )

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


def _get_raw_connection():
    """
    Get a raw database connection for migrations.
    Used before the pool might be fully ready or for special operations.
    """
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        return None

    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    return psycopg2.connect(database_url)


def _ensure_migrations_lock_table(conn):
    """
    Create the migrations lock table if it doesn't exist.
    This table is used to coordinate migrations across multiple Gunicorn workers.

    IMPORTANT FOR GUNICORN/RAILWAY:
    When Gunicorn spawns multiple workers, each worker imports app.py and tries
    to run migrations. Without a database-level lock, this causes race conditions
    and "duplicate key" errors. This lock table ensures only ONE worker runs
    migrations while others wait or skip.
    """
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS _schema_migrations_lock (
                id INTEGER PRIMARY KEY DEFAULT 1,
                locked BOOLEAN DEFAULT FALSE,
                locked_at TIMESTAMP,
                locked_by VARCHAR(255),
                migrations_completed BOOLEAN DEFAULT FALSE,
                completed_at TIMESTAMP,
                CONSTRAINT single_row CHECK (id = 1)
            )
        """)
        conn.commit()
    finally:
        cursor.close()


def _try_acquire_migration_lock(conn, worker_id):
    """
    Try to acquire the migration lock using PostgreSQL row-level locking.
    Returns: (lock_acquired, migrations_already_done)

    Uses SELECT FOR UPDATE NOWAIT to avoid blocking - if another worker
    has the lock, we immediately know and can skip migrations.
    """
    cursor = conn.cursor()
    try:
        # Insert the lock row if it doesn't exist
        cursor.execute("""
            INSERT INTO _schema_migrations_lock (id, locked, migrations_completed)
            VALUES (1, FALSE, FALSE)
            ON CONFLICT (id) DO NOTHING
        """)
        conn.commit()

        # Try to acquire lock with NOWAIT - fails immediately if locked
        cursor.execute("""
            SELECT locked, migrations_completed
            FROM _schema_migrations_lock
            WHERE id = 1
            FOR UPDATE NOWAIT
        """)
        row = cursor.fetchone()

        if row is None:
            return False, False

        locked, migrations_completed = row

        # If migrations already completed by another worker, skip
        if migrations_completed:
            conn.commit()
            return False, True

        # If already locked by another worker (shouldn't happen with NOWAIT, but safety check)
        if locked:
            conn.commit()
            return False, False

        # Acquire the lock
        cursor.execute("""
            UPDATE _schema_migrations_lock
            SET locked = TRUE, locked_at = NOW(), locked_by = %s
            WHERE id = 1
        """, (worker_id,))
        conn.commit()
        return True, False

    except psycopg2.errors.LockNotAvailable:
        # Another worker has the lock - skip migrations
        conn.rollback()
        return False, False
    except Exception as e:
        conn.rollback()
        logger.error(f"Error acquiring migration lock: {str(e)}")
        return False, False
    finally:
        cursor.close()


def _release_migration_lock(conn, success):
    """
    Release the migration lock and mark migrations as completed if successful.
    """
    cursor = conn.cursor()
    try:
        if success:
            cursor.execute("""
                UPDATE _schema_migrations_lock
                SET locked = FALSE, locked_at = NULL, locked_by = NULL,
                    migrations_completed = TRUE, completed_at = NOW()
                WHERE id = 1
            """)
        else:
            cursor.execute("""
                UPDATE _schema_migrations_lock
                SET locked = FALSE, locked_at = NULL, locked_by = NULL
                WHERE id = 1
            """)
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Error releasing migration lock: {str(e)}")
    finally:
        cursor.close()


def run_migrations():
    """
    Run database migrations to set up schema.

    GUNICORN/RAILWAY SAFE:
    This function uses PostgreSQL-based locking to ensure migrations run
    exactly ONCE across all Gunicorn workers. When multiple workers start
    simultaneously:
    1. First worker acquires the DB lock and runs migrations
    2. Other workers see the lock and skip migrations
    3. After migrations complete, lock is released and marked as done
    4. Future deployments check "migrations_completed" flag and skip

    This prevents "duplicate key" errors from concurrent CREATE INDEX/TABLE.
    """
    import uuid
    worker_id = f"worker-{uuid.uuid4().hex[:8]}-pid-{os.getpid()}"

    # Get a dedicated connection for migrations (not from pool)
    conn = _get_raw_connection()
    if not conn:
        logger.error("Cannot run migrations: no database connection")
        return False

    try:
        # Step 1: Ensure lock table exists
        _ensure_migrations_lock_table(conn)

        # Step 2: Try to acquire migration lock
        lock_acquired, already_done = _try_acquire_migration_lock(conn, worker_id)

        if already_done:
            print(f"[Database] Migrations already completed by another worker, skipping")
            logger.info("Migrations already completed, skipping")
            conn.close()
            return True

        if not lock_acquired:
            print(f"[Database] Another worker is running migrations, skipping")
            logger.info("Migration lock held by another worker, skipping")
            conn.close()
            return True

        # Step 3: We have the lock - run migrations
        print(f"[Database] Worker {worker_id} acquired migration lock, running migrations...")
        logger.info(f"Worker {worker_id} running migrations")

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

            # Indexes - wrapped in DO block to handle "already exists" gracefully
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

        cursor = conn.cursor()
        try:
            for migration in migrations:
                cursor.execute(migration)
            conn.commit()
            success = True
            print(f"[Database] Migrations completed successfully by {worker_id}")
            logger.info("Database migrations completed successfully")
        except Exception as e:
            conn.rollback()
            success = False
            logger.error(f"Migration error: {str(e)}")
            print(f"[Database] Migration error: {str(e)}", file=sys.stderr)
        finally:
            cursor.close()

        # Step 4: Release lock and mark completion
        _release_migration_lock(conn, success)
        conn.close()
        return success

    except Exception as e:
        logger.error(f"Migration process error: {str(e)}")
        print(f"[Database] Migration process error: {str(e)}", file=sys.stderr)
        try:
            conn.close()
        except:
            pass
        return False


def cleanup_expired_otp():
    """Remove expired OTP codes from the database."""
    query = "DELETE FROM otp_codes WHERE expires_at < NOW()"
    try:
        execute_query(query)
        logger.info("Cleaned up expired OTP codes")
    except Exception as e:
        logger.error(f"OTP cleanup error: {str(e)}")

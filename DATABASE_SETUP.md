# Database Setup Guide - LISHAI SIMANI Beauty Studio

## Overview

The application has been upgraded to use **PostgreSQL** as the primary database, with Google Calendar as a synchronized secondary system. This provides:

- ✅ Customer registration with phone number uniqueness
- ✅ Appointment management with business rules enforcement
- ✅ OTP authentication with rate limiting
- ✅ Admin customer management
- ✅ Automatic database migrations

---

## Environment Variables

### Required for Database Functionality

Add these to your `.env` file or Railway environment variables:

```env
# PostgreSQL Database (Railway auto-provisions this)
DATABASE_URL=postgresql://user:password@host:port/dbname

# Flask Configuration
FLASK_SECRET_KEY=your-random-secret-key-here

# Admin Password
ADMIN_PASSWORD=your-admin-password

# Google Calendar (existing)
GOOGLE_CREDENTIALS_JSON=<your-google-credentials-json>
CALENDAR_ID=<your-calendar-id>

# Email (existing)
SENDGRID_API_KEY=<your-sendgrid-key>
FROM_EMAIL=<your-from-email>

# WhatsApp (existing)
WHATSAPP_ENABLED=true
WHATSAPP_ACCESS_TOKEN=<your-whatsapp-token>
WHATSAPP_PHONE_NUMBER_ID=<your-phone-number-id>
WHATSAPP_OTP_TEMPLATE=otp_verification
```

---

## Database Schema

The application uses 3 main tables:

### 1. `customers`
Stores registered customers with unique phone numbers.

```sql
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL UNIQUE,
    email VARCHAR(100),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 2. `appointments`
Stores all appointments with status tracking and Google Calendar sync.

```sql
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    service_name VARCHAR(50) NOT NULL,
    service_name_he VARCHAR(50) NOT NULL,
    datetime TIMESTAMP NOT NULL,
    duration INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active'
        CHECK (status IN ('active', 'cancelled', 'completed')),
    google_event_id VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

### 3. `otp_codes`
Stores OTP verification codes with expiration and rate limiting.

```sql
CREATE TABLE otp_codes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    phone VARCHAR(20) NOT NULL,
    code VARCHAR(6) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    attempts INTEGER DEFAULT 0,
    cooldown_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

## Setup Instructions

### Option 1: Railway Automatic Setup (Recommended)

1. **Add PostgreSQL Plugin** in Railway:
   - Go to your project → "New" → "Database" → "Add PostgreSQL"
   - Railway will automatically set `DATABASE_URL`

2. **Deploy Application**:
   - The app automatically runs migrations on startup
   - Check logs for: `[Database] Migrations completed successfully`

3. **Verify Setup**:
   ```bash
   curl https://your-app.railway.app/health
   ```
   Should return database status as available.

### Option 2: Local Development

1. **Install PostgreSQL locally**:
   ```bash
   # Windows
   choco install postgresql

   # Mac
   brew install postgresql

   # Linux
   sudo apt install postgresql
   ```

2. **Create Database**:
   ```bash
   createdb lishay_beauty
   ```

3. **Set Environment Variable**:
   ```env
   DATABASE_URL=postgresql://localhost/lishay_beauty
   ```

4. **Run Application**:
   ```bash
   python app.py
   ```
   Migrations run automatically on startup.

---

## Migration Process

### Automatic Migrations

Migrations run automatically when the app starts. The system:

1. Checks if `DATABASE_URL` is set
2. Initializes connection pool
3. Creates tables if they don't exist (idempotent)
4. Creates indexes for performance

### Manual Migration (if needed)

```python
from db_service import init_db_pool, run_migrations

init_db_pool()
run_migrations()
```

---

## Business Rules Enforced

The database implements the following business rules:

### 1. Phone Number Uniqueness
- Each phone number can only register once
- Duplicate registration attempts return existing customer

### 2. One Active Appointment Per Customer
- Customers can have only ONE active future appointment
- Enforced in: `has_active_future_appointment()` function
- Prevents booking conflicts

### 3. Appointment Date Range
- Appointments must be 1-30 days in the future
- Enforced in: `create_appointment()` function

### 4. OTP Security
- OTP expires after 5 minutes
- Max 3 verification attempts
- 15-minute cooldown after max attempts
- Rate limiting prevents brute force

---

## Database Fallback Mode

If PostgreSQL is unavailable, the app runs in **legacy mode**:

- ✅ Google Calendar still works
- ✅ Existing bookings function normally
- ⚠️ No customer registration
- ⚠️ OTP uses in-memory storage (resets on restart)
- ⚠️ Admin customer tab unavailable

Check logs for: `[Database] Using PostgreSQL database` or `[Database] PostgreSQL not available, using legacy mode`

---

## API Endpoints Added

### Customer Management

#### `POST /api/user/register`
Register a new customer after OTP verification.

**Request:**
```json
{
  "name": "Full Name",
  "phone": "050-1234567",
  "email": "user@example.com"
}
```

**Response:**
```json
{
  "success": true,
  "customer": {
    "name": "Full Name",
    "phone": "0501234567",
    "email": "user@example.com"
  }
}
```

#### `GET /api/user/lookup?phone=050-1234567`
Look up customer details by phone.

**Response:**
```json
{
  "found": true,
  "name": "Full Name",
  "email": "user@example.com"
}
```

#### `GET /api/admin/customers` (Admin only)
Get all customers with search and pagination.

**Query Parameters:**
- `limit` (default: 50)
- `offset` (default: 0)
- `search` (optional search term)

**Response:**
```json
{
  "customers": [
    {
      "id": "uuid",
      "name": "Customer Name",
      "phone": "0501234567",
      "email": "email@example.com",
      "created_at_formatted": "01/01/2026"
    }
  ],
  "total": 100,
  "limit": 50,
  "offset": 0
}
```

---

## Monitoring & Troubleshooting

### Health Check

```bash
curl https://your-app.railway.app/health
```

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2026-02-05T12:00:00+02:00",
  "email": true,
  "calendar": true,
  "whatsapp": true
}
```

### Common Issues

#### 1. Database Connection Fails

**Symptoms:** `[Database] WARNING: Failed to initialize database pool`

**Solutions:**
- Verify `DATABASE_URL` is set correctly
- Check Railway PostgreSQL plugin is provisioned
- Ensure database is running

#### 2. Migrations Don't Run

**Symptoms:** Tables don't exist, queries fail

**Solutions:**
- Check logs for migration errors
- Manually run migrations (see above)
- Verify database user has CREATE TABLE permissions

#### 3. Duplicate Customer Error

**Symptoms:** `409 Conflict` when creating customer

**Solutions:**
- This is expected behavior (phone uniqueness)
- Frontend should handle by logging in instead of registering

---

## Data Migration from Calendar

If you have existing appointments in Google Calendar:

1. They continue to work normally
2. New bookings create both database + calendar entries
3. Old bookings are read from calendar only
4. Gradually, all data moves to database

No manual migration required - the system handles this transparently.

---

## Security Notes

### Password Hashing
- Customer passwords are NOT stored (OTP-only authentication)
- Admin password is stored as plain text in env var (consider hashing for production)

### Phone Number Handling
- Phone numbers are normalized to Israeli format: `0XXXXXXXXX`
- WhatsApp uses international format: `972XXXXXXXXX`

### SQL Injection Prevention
- All queries use parameterized statements
- No string concatenation for SQL

### Rate Limiting
- OTP requests limited per phone number
- Consider adding IP-based rate limiting for production

---

## Backup & Recovery

### Backup Strategy

1. **Railway Automatic Backups:**
   - Railway PostgreSQL includes automatic backups
   - Configured in Railway dashboard

2. **Manual Backup:**
   ```bash
   pg_dump $DATABASE_URL > backup.sql
   ```

3. **Restore:**
   ```bash
   psql $DATABASE_URL < backup.sql
   ```

### Disaster Recovery

If database is lost:
1. Google Calendar still has appointment data
2. Customers can re-register (same phone)
3. System rebuilds database from calendar events

---

## Performance Considerations

### Indexes Created

- `idx_customers_phone` - Fast customer lookup
- `idx_appointments_customer` - Fast customer appointments
- `idx_appointments_datetime` - Date range queries
- `idx_appointments_status` - Active appointment filtering
- `idx_otp_phone` - OTP lookup
- `idx_otp_expires` - Cleanup expired OTPs

### Connection Pooling

- Min connections: 1
- Max connections: 10
- Automatic connection management

### Query Optimization

- Use `LIMIT` for large result sets
- Pagination for admin views
- Expired OTP cleanup runs periodically

---

## Support

For issues or questions:
1. Check Railway logs
2. Review this documentation
3. Contact development team

---

**Last Updated:** 2026-02-05
**Version:** 1.0.0

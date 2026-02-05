# Environment Variables Reference

## Complete Environment Variable List

This document lists ALL environment variables required for the LISHAI SIMANI Beauty Studio application.

---

## 🔧 Core Application

### `FLASK_SECRET_KEY` (Required)
Secret key for Flask session management.

**Example:**
```env
FLASK_SECRET_KEY=your-random-64-character-string-here-make-it-secure
```

**How to Generate:**
```python
import secrets
print(secrets.token_hex(32))
```

---

## 🗄️ Database (PostgreSQL)

### `DATABASE_URL` (Required for database features)
PostgreSQL connection string.

**Format:**
```env
DATABASE_URL=postgresql://user:password@host:port/database
```

**Railway:** Auto-provisioned when you add PostgreSQL plugin

**Local Development:**
```env
DATABASE_URL=postgresql://localhost/lishay_beauty
```

---

## 🔐 Admin Access

### `ADMIN_PASSWORD` (Required)
Password for admin panel access.

**Example:**
```env
ADMIN_PASSWORD=SecureAdminPass123!
```

**Default:** `admin123` (⚠️ Change this!)

---

## 📅 Google Calendar Integration

### `GOOGLE_CREDENTIALS_JSON` (Required)
Google Service Account credentials as JSON string.

**Example:**
```env
GOOGLE_CREDENTIALS_JSON={"type":"service_account","project_id":"..."}
```

**How to Get:**
1. Go to Google Cloud Console
2. Create Service Account
3. Download JSON key
4. Copy entire JSON content as one line

### `CALENDAR_ID` (Required)
Google Calendar ID to sync appointments.

**Example:**
```env
CALENDAR_ID=your-calendar-id@group.calendar.google.com
```

**How to Find:**
1. Open Google Calendar
2. Settings → Calendar settings
3. Integrate calendar → Calendar ID

---

## 📧 Email (SendGrid)

### `SENDGRID_API_KEY` (Required for email)
SendGrid API key for sending emails.

**Example:**
```env
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**How to Get:**
1. Sign up at sendgrid.com
2. Settings → API Keys → Create API Key

### `FROM_EMAIL` (Required for email)
Sender email address (must be verified in SendGrid).

**Example:**
```env
FROM_EMAIL=noreply@yoursite.com
```

---

## 💬 WhatsApp Integration

### `WHATSAPP_ENABLED` (Optional)
Enable/disable WhatsApp notifications.

**Values:** `true` or `false`

**Example:**
```env
WHATSAPP_ENABLED=true
```

**Default:** `false`

### `WHATSAPP_ACCESS_TOKEN` (Required if enabled)
Meta (Facebook) WhatsApp Business API access token.

**Example:**
```env
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**How to Get:**
1. Go to Meta Business Suite (business.facebook.com)
2. WhatsApp → API Setup
3. Copy Temporary Access Token (or create Permanent Token)

### `WHATSAPP_PHONE_NUMBER_ID` (Required if enabled)
WhatsApp Phone Number ID from Meta Business.

**Example:**
```env
WHATSAPP_PHONE_NUMBER_ID=123456789012345
```

**How to Get:**
1. Meta Business Suite → WhatsApp
2. API Setup → Phone Number ID (long numeric string)

### `WHATSAPP_OTP_TEMPLATE` (Optional)
Name of approved WhatsApp message template for OTP.

**Example:**
```env
WHATSAPP_OTP_TEMPLATE=otp_verification
```

**Default:** `otp_verification`

**Note:** Template must be approved by Meta.

**Template Format:**
```
Your verification code is: {{1}}
Valid for 5 minutes.
```

---

## 🌍 Application Settings

### `PORT` (Optional)
Port for the Flask server.

**Example:**
```env
PORT=5000
```

**Default:** `5000`

**Railway:** Auto-set by Railway

### `NODE_ENV` (Optional)
Environment mode.

**Values:** `production`, `development`

**Example:**
```env
NODE_ENV=production
```

---

## 📋 Full .env Template

Copy this template and fill in your values:

```env
# ============== CORE ==============
FLASK_SECRET_KEY=your-random-64-character-string

# ============== DATABASE ==============
DATABASE_URL=postgresql://user:password@host:port/database

# ============== ADMIN ==============
ADMIN_PASSWORD=your-secure-admin-password

# ============== GOOGLE CALENDAR ==============
GOOGLE_CREDENTIALS_JSON={"type":"service_account",...}
CALENDAR_ID=your-calendar@group.calendar.google.com

# ============== EMAIL ==============
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxx
FROM_EMAIL=noreply@yoursite.com

# ============== WHATSAPP ==============
WHATSAPP_ENABLED=true
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxxxxx
WHATSAPP_PHONE_NUMBER_ID=123456789012345
WHATSAPP_OTP_TEMPLATE=otp_verification

# ============== APP SETTINGS ==============
PORT=5000
NODE_ENV=production
```

---

## 🚀 Railway Deployment

### Setting Environment Variables in Railway

1. **Dashboard Method:**
   - Go to your project → "Variables" tab
   - Click "New Variable"
   - Add each variable one by one

2. **CLI Method:**
   ```bash
   railway variables set FLASK_SECRET_KEY=your-value
   railway variables set DATABASE_URL=your-value
   ```

3. **Bulk Import:**
   - Create `.env` file locally (DON'T commit to Git!)
   - Railway CLI: `railway run` (reads local .env)

### Auto-Provisioned Variables

Railway automatically sets:
- `DATABASE_URL` (when you add PostgreSQL plugin)
- `PORT` (Railway assigns this)

---

## 🔒 Security Best Practices

### DO:
✅ Use strong, random secrets (64+ characters)
✅ Rotate credentials regularly
✅ Use different passwords for dev/staging/production
✅ Store secrets in Railway dashboard (not in code)
✅ Use environment-specific configurations

### DON'T:
❌ Commit `.env` file to Git
❌ Share credentials in chat/email
❌ Use default passwords in production
❌ Hardcode secrets in source code
❌ Reuse passwords across services

---

## 🧪 Testing Environment Variables

### Check if variables are set:

```python
import os
print("DATABASE_URL:", "✓" if os.getenv('DATABASE_URL') else "✗")
print("SENDGRID_API_KEY:", "✓" if os.getenv('SENDGRID_API_KEY') else "✗")
print("WHATSAPP_ENABLED:", os.getenv('WHATSAPP_ENABLED', 'false'))
```

### Health Check Endpoint:

```bash
curl https://your-app.railway.app/health
```

**Response:**
```json
{
  "status": "ok",
  "email": true,
  "calendar": true,
  "whatsapp": true
}
```

- `true` = configured and working
- `false` = not configured or not working

---

## 📞 Support

If environment variables aren't working:

1. **Check Railway Logs:**
   ```bash
   railway logs
   ```

2. **Verify Variable Names:**
   - Variables are case-sensitive
   - No spaces around `=` in `.env` file

3. **Restart Application:**
   - Railway: Redeploy triggers restart
   - Local: Stop and restart `python app.py`

4. **Test Individual Services:**
   - Email: Check SendGrid dashboard
   - WhatsApp: Verify Meta Business Suite settings
   - Calendar: Test Google Calendar API access

---

**Last Updated:** 2026-02-05

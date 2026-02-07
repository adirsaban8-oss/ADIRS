# ✅ Features Implementation Reference

Quick reference showing **exactly where** each requirement was implemented.

---

## 1️⃣ Login & OTP via WhatsApp

### Entry Screen
**Location:** [index.html](index.html:36-123)
- **Line 41-58:** Existing customer login form (שם + טלפון + "שלח קוד אימות")
- **Line 61-87:** New customer registration (שם + טלפון + אימייל + "הירשם ושלח קוד")
- **Line 89-115:** OTP verification screen (6-digit boxes)

### OTP Backend
**Location:** [whatsapp_otp_db.py](whatsapp_otp_db.py:1)
- **Line 78-122:** `request_otp()` - Generate and send OTP
- **Line 125-199:** `verify_otp()` - Verify code with attempts limit
- **Line 32-35:** Configuration (5-min expiry, 3 attempts max, 15-min cooldown)

### OTP API Endpoints
**Location:** [app.py](app.py:742-783)
- **Line 742-761:** `POST /api/otp/request` - Send OTP
- **Line 764-783:** `POST /api/otp/verify` - Verify OTP

### Frontend Logic
**Location:** [scripts/main.js](scripts/main.js:27-400)
- **Line 124-164:** `requestOtpExisting()` - Existing customer OTP request
- **Line 167-216:** `requestOtpNew()` - New customer OTP request
- **Line 219-286:** `verifyOtp()` - OTP verification with session creation
- **Line 339-391:** OTP box management and auto-submit

---

## 2️⃣ Persistent Database (PostgreSQL)

### Database Service
**Location:** [db_service.py](db_service.py:1)
- **Line 28-46:** Connection pool initialization
- **Line 49-69:** Connection context manager
- **Line 93-182:** Migration functions with schema definitions

### Schema
**Location:** [db_service.py](db_service.py:108-162)
```sql
customers (id, name, phone UNIQUE, email, created_at, updated_at)
appointments (id, customer_id, service_name, service_name_he, datetime,
              duration, status, google_event_id, notes, created_at, updated_at)
otp_codes (id, phone, code, expires_at, verified, attempts, cooldown_until, created_at)
```

### Integration
**Location:** [app.py](app.py:43-72)
- **Line 43-52:** Import database modules with fallback
- **Line 54-72:** Database initialization on app startup
- **Line 524-621:** Updated booking flow with database

---

## 3️⃣ Admin Panel - "לקוחות" Tab

### HTML Structure
**Location:** [admin.html](admin.html:486-599)
- **Line 486:** New tab button: "לקוחות"
- **Line 560-597:** Customers tab content (table + search)

### JavaScript
**Location:** [admin.html](admin.html:922-1017)
- **Line 576:** Load customers on login
- **Line 922-959:** `loadCustomers()` - Fetch and display customers
- **Line 961-1008:** `searchCustomers()` - Search with debouncing

### Backend API
**Location:** [app.py](app.py:951-988)
- **Line 951-988:** `GET /api/admin/customers` - Fetch customers with search/pagination

---

## 4️⃣ Personalized Home Page

### Greeting
**Location:** [scripts/main.js](scripts/main.js:1100-1135)
- **Line 1100-1135:** `initializeHomeGreeting()` - Shows "שלום, {Name}! 👋"
- **Line 1180:** Called on page load

### Appointment Banner (Enhanced)
**Location:** [scripts/main.js](scripts/main.js:1032-1042)
- **Line 1032-1042:** `updateHomeBubble()` - Shows "יש לך תור ב-..."
- **Line 1013:** Auto-triggered after login

### HTML Placeholder
**Location:** [index.html](index.html:168)
- **Line 168:** `<div id="homeAppointmentBubble">` - Container for banner

---

## 5️⃣ "התורים שלי" Tab

### Navigation
**Location:** [index.html](index.html:141)
- **Line 141:** Navigation link (between צור קשר and אודות)

### Section Content
**Location:** [index.html](index.html:394-465)
- **Line 394-465:** Full "התורים שלי" section with states:
  - Phone input form
  - Loading state
  - Results with appointments
  - Empty state

### Backend Logic
**Location:** [scripts/main.js](scripts/main.js:920-1097)
- **Line 998-1023:** `lookupPhone()` - Fetch user's appointments
- **Line 954-977:** `showResults()` - Display appointments
- **Line 1065-1096:** `init()` - Auto-load if user logged in

### API Endpoint
**Location:** [app.py](app.py:723-745)
- **Line 723-745:** `GET /api/my-appointments` - Fetch appointments by phone

---

## 6️⃣ Booking Rules

### One Active Appointment Rule
**Location:** [appointment_service.py](appointment_service.py:124-145)
- **Line 124-145:** `has_active_future_appointment()` - Check for existing appointment

**Enforcement:** [app.py](app.py:544-561)
- **Line 544-561:** Check before booking, return 409 error if exists

### 30-Day Limit
**Location:** [appointment_service.py](appointment_service.py:32-41)
- **Line 32-41:** Validation in `create_appointment()`

**Also enforced:** [app.py](app.py:518-525)
- **Line 518-525:** Server-side date validation

### Phone Uniqueness
**Location:** [db_service.py](db_service.py:112)
- **Line 112:** `phone VARCHAR(20) NOT NULL UNIQUE` - Database constraint

**Check before insert:** [customer_service.py](customer_service.py:65-71)
- **Line 65-71:** Prevent duplicate customer creation

---

## 7️⃣ Waze Button

### Booking Success Modal
**Location:** [scripts/main.js](scripts/main.js:843-875)
- **Line 843-875:** `showModal()` - Adds Waze button to modal
- **Line 863-869:** Waze deep link + web fallback

### Address Constant
**Location:** [scripts/main.js](scripts/main.js:1139)
- **Line 1139:** `const BUSINESS_ADDRESS = 'משעול הרקפת 3 קרני שומרון'`

---

## 8️⃣ WhatsApp Notifications

### OTP Messages
**Location:** [whatsapp_otp_db.py](whatsapp_otp_db.py:203-296)
- **Line 203-296:** `_send_otp_whatsapp()` - Send OTP via WhatsApp API
- **Line 209-225:** Template message payload

### Booking Confirmation
**Location:** [whatsapp_service.py](whatsapp_service.py:1)
- Already existed, called in [app.py](app.py:664-686)
- **Line 664-686:** WhatsApp confirmation sent in background thread

### Reminder Scheduler (NEW)
**Location:** [app.py](app.py:270-367)
- **Line 270-325:** `check_and_send_reminders()` - **UPDATED** to use database
- **Line 290-322:** Database-backed reminder logic (day before + morning)
- **Line 324-367:** Calendar fallback for legacy appointments
- **Line 366:** Scheduler runs every hour

### Reminder Query
**Location:** [appointment_service.py](appointment_service.py:282-327)
- **Line 282-327:** `get_appointments_needing_reminders()` - Query for today/tomorrow appointments

---

## 9️⃣ Google Calendar Integration

### Create Event on Booking
**Location:** [app.py](app.py:568-578)
- **Line 568-578:** Create Google Calendar event
- **Line 575:** Store `google_event_id` in database

### Calendar Service
**Location:** [calendar_service.py](calendar_service.py:1)
- Already existed, enhanced with database integration

### Event ID Storage
**Location:** [appointment_service.py](appointment_service.py:334-347)
- **Line 334-347:** `update_google_event_id()` - Update appointment with Calendar event ID

---

## 🔟 UX & Non-Regression

### Loading States
**Example:** [scripts/main.js](scripts/main.js:116-122)
- **Line 116-122:** `setButtonLoading()` - Disable button + show spinner

**Example:** [admin.html](admin.html:932)
- **Line 932:** Loading spinner for customers table

### Error Handling
**Example:** [scripts/main.js](scripts/main.js:232-238)
- **Line 232-238:** OTP verification error handling

**Example:** [app.py](app.py:687-698)
- **Line 687-698:** Try-catch with user-friendly error messages

### Preserved Design
**All new elements use existing CSS classes:**
- `.btn`, `.btn-primary`, `.btn-outline` (buttons)
- `.input`, `.input-group` (forms)
- `.apt-card` (appointment cards)
- Same color scheme (`var(--color-gold)`, `var(--color-text-secondary)`)
- RTL layout maintained

---

## 📦 New Files Summary

| File | Lines | Purpose |
|------|-------|---------|
| [db_service.py](db_service.py:1) | 210 | Database connection & migrations |
| [whatsapp_otp_db.py](whatsapp_otp_db.py:1) | 330 | Database-backed OTP service |
| [customer_service.py](customer_service.py:1) | 220 | Customer CRUD operations |
| [appointment_service.py](appointment_service.py:1) | 380 | Appointment management with rules |
| [DATABASE_SETUP.md](DATABASE_SETUP.md:1) | 460 | Complete setup guide |
| [ENV_VARIABLES.md](ENV_VARIABLES.md:1) | 380 | Environment variables reference |
| [DEPLOYMENT.md](DEPLOYMENT.md:1) | 180 | Quick deployment steps |
| [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md:1) | 300 | Feature overview |
| [FEATURES_IMPLEMENTED.md](FEATURES_IMPLEMENTED.md:1) | 220 | This file |

---

## 🎯 Quick Verification Checklist

Use this to verify everything works:

- [ ] **Line 43-72 in [app.py](app.py:43)** - Database initializes successfully
- [ ] **Line 742-783 in [app.py](app.py:742)** - OTP endpoints respond
- [ ] **Line 486 in [admin.html](admin.html:486)** - "לקוחות" tab visible
- [ ] **Line 1100 in [scripts/main.js](scripts/main.js:1100)** - Greeting appears when logged in
- [ ] **Line 141 in [index.html](index.html:141)** - "התורים שלי" in navigation
- [ ] **Line 544-561 in [app.py](app.py:544)** - One appointment rule enforced
- [ ] **Line 863 in [scripts/main.js](scripts/main.js:863)** - Waze button in modal
- [ ] **Line 290-322 in [app.py](app.py:290)** - Reminders use database

---

## 🔍 How to Find Code

### Search by Feature
```bash
# Find OTP logic
grep -r "request_otp\|verify_otp" --include="*.py" --include="*.js"

# Find customer management
grep -r "customer_service\|customers" --include="*.py" --include="*.html"

# Find Waze button
grep -r "waze://" --include="*.js" --include="*.html"

# Find business rules
grep -r "has_active_future_appointment\|one active" --include="*.py"
```

### Key Import Statements
```python
# In app.py
from db_service import init_db_pool, run_migrations
from whatsapp_otp_db import request_otp, verify_otp
from customer_service import get_customer_by_phone, create_customer
from appointment_service import has_active_future_appointment
```

---

**This document maps every requirement to its exact implementation location.**

**Need to modify a feature? Use the line numbers above to jump directly to the code.**

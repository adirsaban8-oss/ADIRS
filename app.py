"""
LISHAI SIMANI Beauty Studio - Flask Server for Railway
Serves the static HTML/CSS/JS website and provides booking API
"""

from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect
from datetime import datetime, timedelta, date
from functools import wraps
import os
import json
import threading
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
import pytz

# Load environment variables
load_dotenv()

# Import calendar service
from calendar_service import (
    filter_available_slots,
    check_availability,
    create_event,
    get_calendar_service,
    CALENDAR_ID
)

# Import email service
from email_service import (
    send_booking_confirmation,
    send_reminder_day_before,
    send_reminder_morning,
    get_email_template,
    send_email
)

# Import Twilio SMS service
try:
    from twilio_sms_service import (
        send_booking_confirmation as send_sms_booking_confirmation,
        send_reminder_day_before as send_sms_reminder_day_before,
        send_reminder_morning as send_sms_reminder_morning
    )
    SMS_SERVICE_AVAILABLE = True
except Exception as sms_error:
    print(f"[SMS] Twilio service not available: {sms_error}")
    SMS_SERVICE_AVAILABLE = False

# Import Twilio OTP service (database version)
try:
    from db_service import init_db_pool, is_db_available, run_migrations
    from twilio_otp import request_otp, verify_otp
    from customer_service import (
        customer_exists, get_customer_by_phone, create_customer,
        get_all_customers, search_customers, get_customer_count
    )
    from appointment_service import (
        create_appointment, get_customer_future_appointments,
        has_active_future_appointment, cancel_appointment,
        get_appointments_for_date, update_google_event_id
    )
    DB_ENABLED = True
    print("[Database] Using PostgreSQL database with Twilio SMS")
except Exception as db_import_error:
    print(f"[Database] PostgreSQL not available, using legacy mode: {db_import_error}")
    # Fallback to old WhatsApp OTP if Twilio not available
    try:
        from whatsapp_otp import request_otp, verify_otp
    except:
        print("[OTP] No OTP service available")
    DB_ENABLED = False

app = Flask(__name__, static_folder='.', static_url_path='')
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(32).hex())

# ============== DATABASE INITIALIZATION ==============

if DB_ENABLED:
    try:
        db_initialized = init_db_pool()
        if db_initialized:
            print("[Database] Connection pool initialized")
            # Run migrations to ensure tables exist
            migrations_success = run_migrations()
            if migrations_success:
                print("[Database] Migrations completed successfully")
            else:
                print("[Database] WARNING: Migrations failed")
        else:
            print("[Database] WARNING: Failed to initialize database pool")
            DB_ENABLED = False
    except Exception as e:
        print(f"[Database] Initialization error: {str(e)}")
        DB_ENABLED = False

# ============== ADMIN CONFIGURATION ==============

ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
BLOCKED_SLOTS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'blocked_slots.json')
GALLERY_DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', 'gallery.json')
GALLERY_UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'static', 'images')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Ensure data directory exists
os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
os.makedirs(GALLERY_UPLOAD_DIR, exist_ok=True)


def load_blocked_slots():
    """Load blocked slots from JSON file."""
    try:
        if os.path.exists(BLOCKED_SLOTS_FILE):
            with open(BLOCKED_SLOTS_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading blocked slots: {e}")
    return {}


def save_blocked_slots(data):
    """Save blocked slots to JSON file."""
    try:
        with open(BLOCKED_SLOTS_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving blocked slots: {e}")


def load_gallery_data():
    """Load gallery image order from JSON file."""
    try:
        if os.path.exists(GALLERY_DATA_FILE):
            with open(GALLERY_DATA_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading gallery data: {e}")
    # Default: scan existing gallery images
    images = []
    if os.path.exists(GALLERY_UPLOAD_DIR):
        for f in sorted(os.listdir(GALLERY_UPLOAD_DIR)):
            if f.lower().startswith('gallery') and any(f.lower().endswith(ext) for ext in ['jpg', 'jpeg', 'png', 'webp']):
                images.append(f)
    return {"images": images}


def save_gallery_data(data):
    """Save gallery data to JSON file."""
    try:
        with open(GALLERY_DATA_FILE, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving gallery data: {e}")


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def admin_required(f):
    """Decorator to require admin authentication."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated_function

# ============== REMINDER SCHEDULER ==============

# Store sent reminders with expiration (key: reminder_key, value: expiration_date)
# Entries are cleaned up after their event date passes
sent_reminders = {}

# Israel timezone for correct reminder timing
ISRAEL_TZ = pytz.timezone('Asia/Jerusalem')


def cleanup_old_reminders():
    """Remove reminder keys for past events to prevent memory leak."""
    global sent_reminders
    today = datetime.now(ISRAEL_TZ).date()
    sent_reminders = {k: v for k, v in sent_reminders.items() if v >= today}


# ============== MY APPOINTMENTS ==============

# Cache for appointment queries: { phone_normalized: { "data": [...], "timestamp": datetime } }
_appointments_cache = {}
APPOINTMENTS_CACHE_TTL = 300  # 5 minutes


def normalize_phone(phone):
    """Normalize phone number for consistent comparison."""
    p = phone.strip().replace('-', '').replace(' ', '')
    if p.startswith('+972'):
        p = '0' + p[4:]
    elif p.startswith('972') and len(p) > 10:
        p = '0' + p[3:]
    return p


def get_appointments_by_phone(phone):
    """Query Google Calendar for future events belonging to a phone number."""
    global _appointments_cache

    phone_norm = normalize_phone(phone)
    now = datetime.now(ISRAEL_TZ)

    # Check cache
    cached = _appointments_cache.get(phone_norm)
    if cached and (now - cached['timestamp']).total_seconds() < APPOINTMENTS_CACHE_TTL:
        return cached['data']

    try:
        service = get_calendar_service()

        time_min = now.isoformat()
        time_max = (now + timedelta(days=60)).isoformat()

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
            maxResults=250
        ).execute()

        events = events_result.get('items', [])
        appointments = []

        for event in events:
            description = event.get('description', '')
            if not description:
                continue

            lines = [line.strip() for line in description.strip().split('\n') if line.strip()]

            # Phone is at index 2 (service_he, name, phone, email)
            event_phone = ''
            if len(lines) >= 3:
                event_phone = normalize_phone(lines[2])

            if event_phone != phone_norm:
                continue

            start_str = event['start'].get('dateTime', '')
            if not start_str:
                continue

            event_start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            event_start_il = event_start.astimezone(ISRAEL_TZ)

            days_hebrew = ['שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת', 'ראשון']
            day_name = days_hebrew[event_start_il.weekday()]

            service_name = lines[0] if lines else event.get('summary', '')

            appointments.append({
                'service': service_name,
                'date': event_start_il.strftime('%d/%m/%Y'),
                'time': event_start_il.strftime('%H:%M'),
                'day_name': day_name,
                'iso_date': event_start_il.strftime('%Y-%m-%d'),
            })

        _appointments_cache[phone_norm] = {
            'data': appointments,
            'timestamp': now
        }

        return appointments

    except Exception as e:
        print(f"Error fetching appointments by phone: {str(e)}")
        return []


def check_and_send_reminders():
    """
    Check for upcoming appointments and send reminders.
    Called by the scheduler. Works with both DB and Calendar.
    """
    try:
        # Clean up old reminder keys first
        cleanup_old_reminders()

        now = datetime.now(ISRAEL_TZ)
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # Try database first if available
        if DB_ENABLED:
            try:
                from appointment_service import get_appointments_needing_reminders
                reminders_data = get_appointments_needing_reminders()

                # Send day-before reminders (20:00)
                if now.hour == 20:
                    for apt in reminders_data.get('day_before', []):
                        reminder_key = f"day_before_{apt['id']}"
                        if reminder_key not in sent_reminders:
                            booking_data = {
                                'name': apt['customer_name'],
                                'phone': apt['customer_phone'],
                                'email': apt['customer_email'],
                                'service_he': apt['service_name_he'],
                                'date': apt['datetime'].strftime('%Y-%m-%d'),
                                'time': apt['datetime'].strftime('%H:%M'),
                            }
                            # Send email reminder
                            send_reminder_day_before(booking_data)
                            # Send SMS reminder if enabled
                            if SMS_SERVICE_AVAILABLE:
                                send_sms_reminder_day_before(booking_data)
                            sent_reminders[reminder_key] = apt['datetime'].date()
                            print(f"[DB] Sent day-before reminder to {apt['customer_email']}")

                # Send morning reminders (08:00)
                if now.hour == 8:
                    for apt in reminders_data.get('morning', []):
                        reminder_key = f"morning_{apt['id']}"
                        if reminder_key not in sent_reminders:
                            booking_data = {
                                'name': apt['customer_name'],
                                'phone': apt['customer_phone'],
                                'email': apt['customer_email'],
                                'service_he': apt['service_name_he'],
                                'date': apt['datetime'].strftime('%Y-%m-%d'),
                                'time': apt['datetime'].strftime('%H:%M'),
                            }
                            # Send email reminder
                            send_reminder_morning(booking_data)
                            # Send SMS reminder if enabled
                            if SMS_SERVICE_AVAILABLE:
                                send_sms_reminder_morning(booking_data)
                            sent_reminders[reminder_key] = apt['datetime'].date()
                            print(f"[DB] Sent morning reminder to {apt['customer_email']}")

                return  # Successfully used database

            except Exception as db_error:
                print(f"[Reminders] DB error, falling back to Calendar: {str(db_error)}")

        # Fallback to Calendar-based reminders (legacy mode)
        service = get_calendar_service()
        now = datetime.now(ISRAEL_TZ)
        today = now.date()
        tomorrow = today + timedelta(days=1)

        # Get events for today and tomorrow
        time_min = datetime.combine(today, datetime.min.time()).isoformat() + 'Z'
        time_max = datetime.combine(tomorrow + timedelta(days=1), datetime.min.time()).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        for event in events:
            # Parse event details from description
            description = event.get('description', '')
            if not description:
                continue

            lines = description.strip().split('\n')
            if len(lines) < 3:
                continue

            # Extract email from description
            email = None
            for line in lines:
                if '@' in line:
                    email = line.strip()
                    break

            if not email:
                continue

            # Get event start time
            start_str = event['start'].get('dateTime', '')
            if not start_str:
                continue

            event_start = datetime.fromisoformat(start_str.replace('Z', '+00:00'))
            event_date = event_start.date()
            event_time = event_start.strftime('%H:%M')

            # Create booking data for email
            summary = event.get('summary', '')
            name = summary.split(' - ')[0] if ' - ' in summary else summary
            service_name = summary.split(' - ')[1] if ' - ' in summary else lines[0]

            booking_data = {
                'name': name,
                'email': email,
                'service_he': service_name,
                'service': service_name,
                'date': event_date.strftime('%Y-%m-%d'),
                'time': event_time,
                'duration': 60
            }

            event_id = event.get('id', '')

            # Check if we need to send day-before reminder (20:00 the day before)
            if event_date == tomorrow and now.hour == 20:
                reminder_key = f"day_before_{event_id}"
                if reminder_key not in sent_reminders:
                    send_reminder_day_before(booking_data)
                    sent_reminders[reminder_key] = event_date
                    print(f"[Calendar] Sent day-before reminder to {email}")

            # Check if we need to send morning reminder (08:00 same day)
            if event_date == today and now.hour == 8:
                reminder_key = f"morning_{event_id}"
                if reminder_key not in sent_reminders:
                    send_reminder_morning(booking_data)
                    sent_reminders[reminder_key] = event_date
                    print(f"[Calendar] Sent morning reminder to {email}")

    except Exception as e:
        print(f"Error checking reminders: {str(e)}")


# Initialize scheduler
scheduler = BackgroundScheduler()
# Check for reminders every hour
scheduler.add_job(func=check_and_send_reminders, trigger="cron", minute=0)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

# ============== CONFIGURATION ==============

SERVICES = [
    {"name": "Gel Polish", "name_he": "לק ג'ל", "price": 120, "duration": 60},
    {"name": "Anatomical Build", "name_he": "בנייה אנטומית", "price": 140, "duration": 75},
    {"name": "Gel Fill", "name_he": "מילוי ג'ל", "price": 150, "duration": 60},
    {"name": "Single Nail Extension", "name_he": "הארכת ציפורן בודדת", "price": 10, "duration": 10},
    {"name": "Building", "name_he": "בנייה", "price": 300, "duration": 120},
    {"name": "Eyebrows", "name_he": "גבות", "price": 50, "duration": 20},
    {"name": "Mustache", "name_he": "שפם", "price": 15, "duration": 10},
    {"name": "Eyebrow Tinting", "name_he": "צביעת גבות", "price": 30, "duration": 15},
]

BUSINESS_HOURS = {
    0: {"open": "09:00", "close": "20:00"},  # Sunday
    1: {"open": "09:00", "close": "20:00"},  # Monday
    2: {"open": "09:00", "close": "20:00"},  # Tuesday
    3: {"open": "09:00", "close": "20:00"},  # Wednesday
    4: {"open": "09:00", "close": "20:00"},  # Thursday
    5: None,  # Friday - closed
    6: None,  # Saturday - closed
}


# ============== ROUTES ==============

@app.route('/')
def index():
    """Serve the main HTML page"""
    return send_from_directory('.', 'index.html')


@app.route('/styles/<path:filename>')
def serve_styles(filename):
    """Serve CSS files"""
    return send_from_directory('styles', filename)


@app.route('/scripts/<path:filename>')
def serve_scripts(filename):
    """Serve JavaScript files"""
    return send_from_directory('scripts', filename)


@app.route('/static/<path:filename>')
def serve_static(filename):
    """Serve static files (images, etc.)"""
    return send_from_directory('static', filename)


# ============== HEALTH CHECK ==============

@app.route('/health')
def health():
    """Health check for Railway monitoring"""
    health_status = {
        "status": "ok",
        "timestamp": datetime.now(ISRAEL_TZ).isoformat(),
        "email": bool(os.getenv('SENDGRID_API_KEY')),
        "calendar": bool(os.getenv('GOOGLE_CREDENTIALS') or os.getenv('GOOGLE_CREDENTIALS_JSON')),
        "whatsapp": os.getenv('WHATSAPP_ENABLED', 'false').lower() == 'true',
    }
    return jsonify(health_status), 200


# ============== API ENDPOINTS ==============

@app.route('/api/services', methods=['GET'])
def get_services():
    """Get list of all services"""
    return jsonify({"services": SERVICES})


@app.route('/api/available-slots', methods=['GET'])
def get_available_slots():
    """Get available time slots for a given date and service duration"""
    date_str = request.args.get('date')
    service_name = request.args.get('service')

    if not date_str:
        return jsonify({"error": "Date parameter is required"}), 400

    # Find service duration (default 60 minutes if not specified)
    service_duration = 60
    if service_name:
        for s in SERVICES:
            if s['name'] == service_name or s['name_he'] == service_name:
                service_duration = s['duration']
                break

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        day_of_week = date.weekday()
        # Convert Python weekday (Monday=0) to our format (Sunday=0)
        day_of_week = (day_of_week + 1) % 7

        hours = BUSINESS_HOURS.get(day_of_week)
        if not hours:
            return jsonify({"slots": [], "message": "סגור ביום זה"})

        # Generate all possible time slots (every 30 minutes)
        all_slots = []
        open_time = datetime.strptime(hours["open"], "%H:%M")
        close_time = datetime.strptime(hours["close"], "%H:%M")

        current = open_time
        while current < close_time:
            all_slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=30)

        # Filter out busy slots from Google Calendar
        # Pass service duration to prevent overlapping appointments
        try:
            available_slots = filter_available_slots(date_str, all_slots, service_duration)
        except Exception as cal_error:
            print(f"Calendar error (returning all slots): {str(cal_error)}")
            available_slots = all_slots  # Graceful fallback

        # Filter out admin-blocked slots
        blocked = load_blocked_slots()
        blocked_times = blocked.get(date_str, [])
        if blocked_times:
            available_slots = [s for s in available_slots if s not in blocked_times]

        return jsonify({"slots": available_slots})

    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400
    except Exception as e:
        print(f"Error in get_available_slots: {str(e)}")
        return jsonify({"error": "שגיאה בקבלת שעות פנויות"}), 500


@app.route('/api/book', methods=['POST'])
def book_appointment():
    """Create a new booking"""
    try:
        data = request.json

        if not data:
            return jsonify({"error": "Invalid JSON data"}), 400

        # Validate required fields
        required_fields = ['name', 'phone', 'email', 'service', 'date', 'time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Missing required field: {field}"}), 400

        # Max 30 days validation
        try:
            booking_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            today_date = datetime.now(ISRAEL_TZ).date()
            max_allowed = today_date + timedelta(days=30)
            if booking_date > max_allowed:
                return jsonify({"error": "ניתן להזמין תור עד 30 יום קדימה בלבד."}), 400
        except ValueError:
            return jsonify({"error": "Invalid date format"}), 400

        # Find service details
        service = None
        for s in SERVICES:
            if s['name'] == data['service'] or s['name_he'] == data['service']:
                service = s
                break

        if not service:
            return jsonify({"error": "Invalid service"}), 400

        # ============== DATABASE MODE ==============
        if DB_ENABLED:
            # Get or create customer
            customer = get_customer_by_phone(data['phone'])
            if not customer:
                customer = create_customer(data['name'], data['phone'], data['email'])
                if not customer:
                    return jsonify({"error": "שגיאה ביצירת משתמש. נסי שוב."}), 500

            # Check if customer has active future appointment (BUSINESS RULE)
            existing_apt = has_active_future_appointment(customer['id'])
            if existing_apt:
                apt_datetime = existing_apt['datetime']
                apt_date_str = apt_datetime.strftime('%d/%m/%Y')
                apt_time_str = apt_datetime.strftime('%H:%M')
                return jsonify({
                    "error": f"כבר יש לך תור בתאריך {apt_date_str} בשעה {apt_time_str}. "
                             f"ניתן להזמין תור חדש רק לאחר שהתור הקיים יעבור.",
                    "existing_appointment": {
                        "date": apt_date_str,
                        "time": apt_time_str,
                        "service": existing_apt['service_name_he']
                    }
                }), 409

            # Check availability from Calendar
            try:
                is_available = check_availability(data['date'], data['time'], service['duration'])
                if not is_available:
                    return jsonify({"error": "התור כבר לא פנוי. נא לבחור שעה אחרת."}), 409
            except Exception as cal_error:
                print(f"Calendar check error (proceeding anyway): {str(cal_error)}")

            # Create appointment in database (without Google event ID yet)
            appointment_db = create_appointment(
                customer_id=customer['id'],
                service_name=service['name'],
                service_name_he=service['name_he'],
                datetime_str=data['date'],
                time_str=data['time'],
                duration=service['duration'],
                notes=data.get('notes', ''),
                google_event_id=None
            )

            if not appointment_db:
                return jsonify({"error": "שגיאה ביצירת התור במערכת. נסי שוב."}), 500

            # Try to create Google Calendar event
            booking_data = {
                "name": data['name'],
                "phone": data['phone'],
                "email": data['email'],
                "service": service['name'],
                "service_he": service['name_he'],
                "date": data['date'],
                "time": data['time'],
                "duration": service['duration'],
                "notes": data.get('notes', ''),
            }

            event = None
            try:
                event = create_event(booking_data)
                if event and event.get('id'):
                    # Update appointment with Google event ID
                    update_google_event_id(appointment_db['id'], event['id'])
                    print(f"Calendar event created: {event['id']}")
            except Exception as cal_error:
                print(f"Failed to create calendar event: {str(cal_error)}")
                # Continue - appointment is saved in database

        # ============== LEGACY MODE (Calendar-only) ==============
        else:
            # Check if user already has a future appointment (Calendar-based)
            if data.get('phone'):
                existing = get_appointments_by_phone(data['phone'])
                if existing:
                    next_apt = existing[0]
                    return jsonify({
                        "error": f"כבר יש לך תור בתאריך {next_apt['date']} בשעה {next_apt['time']}. "
                                 f"ניתן להזמין תור חדש רק לאחר שהתור הקיים יעבור.",
                        "existing_appointment": next_apt
                    }), 409

            # Check availability
            try:
                is_available = check_availability(data['date'], data['time'], service['duration'])
                if not is_available:
                    return jsonify({"error": "התור כבר לא פנוי. נא לבחור שעה אחרת."}), 409
            except Exception as cal_error:
                print(f"Calendar check error (proceeding anyway): {str(cal_error)}")

            # Create booking data
            booking_data = {
                "name": data['name'],
                "phone": data['phone'],
                "email": data['email'],
                "service": service['name'],
                "service_he": service['name_he'],
                "date": data['date'],
                "time": data['time'],
                "duration": service['duration'],
                "notes": data.get('notes', ''),
            }

            # Try to create calendar event
            event = None
            try:
                event = create_event(booking_data)
                print(f"Calendar event created: {event.get('id') if event else 'N/A'}")
                # Invalidate appointments cache for this phone
                _appointments_cache.pop(normalize_phone(data['phone']), None)
            except Exception as cal_error:
                print(f"Failed to create calendar event: {str(cal_error)}")

        # Send confirmation email via SendGrid HTTP API
        email_sent = False
        try:
            email_sent = send_booking_confirmation(booking_data)
        except Exception as email_error:
            print(f"Failed to send confirmation email: {str(email_error)}")

        # Send SMS confirmation in background (non-blocking)
        sms_enabled = os.getenv("TWILIO_ENABLED", "false").lower() == "true"
        print(f"[Twilio] SMS enabled={sms_enabled}, phone={booking_data.get('phone')}")
        if sms_enabled and SMS_SERVICE_AVAILABLE:
            try:
                print(f"[Twilio] Sending booking confirmation SMS to {booking_data.get('name')}...")
                sms_thread = threading.Thread(
                    target=send_sms_booking_confirmation,
                    args=(booking_data,),
                    daemon=True
                )
                sms_thread.start()
            except Exception as sms_error:
                print(f"[Twilio] Failed to start SMS thread: {str(sms_error)}")
        else:
            print("[Twilio] Skipping SMS - TWILIO_ENABLED is not true or service unavailable")

        return jsonify({
            "success": True,
            "message": "התור נקבע בהצלחה!",
            "event_id": event.get('id') if event else None,
            "email_sent": email_sent
        })

    except Exception as e:
        print(f"Booking error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": "שגיאה בקביעת התור. נסה שוב."}), 500


@app.route('/api/contact', methods=['POST'])
def contact():
    """Handle contact form submission"""
    data = request.json

    if not data:
        return jsonify({"error": "Invalid JSON data"}), 400

    required_fields = ['name', 'phone', 'message']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"Missing required field: {field}"}), 400

    # Here you could add email sending logic
    # For now, just log and return success
    print(f"Contact form submission: {data}")

    return jsonify({
        "success": True,
        "message": "ההודעה נשלחה בהצלחה! אחזור אלייך בהקדם."
    })


# ============== MY APPOINTMENTS ==============

@app.route('/api/my-appointments', methods=['GET'])
def my_appointments():
    """Get future appointments for a phone number."""
    phone = request.args.get('phone', '').strip()

    if not phone:
        return jsonify({"error": "Phone number is required"}), 400

    phone_clean = phone.replace('-', '').replace(' ', '').replace('+', '')
    if not phone_clean.isdigit() or len(phone_clean) < 9:
        return jsonify({"error": "Invalid phone number"}), 400

    appointments = get_appointments_by_phone(phone)

    return jsonify({
        "appointments": appointments,
        "count": len(appointments)
    })


# ============== OTP AUTHENTICATION ==============

@app.route('/api/otp/request', methods=['POST'])
def otp_request():
    """Send OTP to a phone number via WhatsApp (or mock)."""
    data = request.json or {}
    phone = data.get('phone', '').strip()

    if not phone:
        return jsonify({"error": "מספר טלפון חסר"}), 400

    result = request_otp(phone)

    if not result['success']:
        return jsonify({"error": result['error']}), 429 if 'ניסיונות' in result.get('error', '') else 400

    return jsonify({
        "success": True,
        "mock": result.get('mock', False),
    })


@app.route('/api/otp/verify', methods=['POST'])
def otp_verify():
    """Verify an OTP code."""
    data = request.json or {}
    phone = data.get('phone', '').strip()
    code = data.get('code', '').strip()

    if not phone or not code:
        return jsonify({"error": "חסרים פרטים"}), 400

    result = verify_otp(phone, code)

    if not result['verified']:
        return jsonify({"verified": False, "error": result['error']}), 400

    return jsonify({"verified": True})


@app.route('/api/user/lookup', methods=['GET'])
def user_lookup():
    """Look up user details by phone number.
    Returns name and email if found (from database or Calendar)."""
    phone = request.args.get('phone', '').strip()

    if not phone:
        return jsonify({"found": False}), 400

    # Try database first if enabled
    if DB_ENABLED:
        customer = get_customer_by_phone(phone)
        if customer:
            return jsonify({
                "found": True,
                "name": customer['name'],
                "email": customer['email'],
            })

    # Fallback to Calendar search (for legacy data)
    phone_norm = normalize_phone(phone)

    try:
        service = get_calendar_service()
        now = datetime.now(ISRAEL_TZ)

        # Search past 180 days + future 60 days
        time_min = (now - timedelta(days=180)).isoformat()
        time_max = (now + timedelta(days=60)).isoformat()

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime',
            maxResults=50
        ).execute()

        events = events_result.get('items', [])

        for event in events:
            description = event.get('description', '')
            if not description:
                continue

            lines = [line.strip() for line in description.strip().split('\n') if line.strip()]
            if len(lines) < 4:
                continue

            event_phone = normalize_phone(lines[2]) if len(lines) >= 3 else ''
            if event_phone != phone_norm:
                continue

            # Found a match — extract name and email
            name = lines[1] if len(lines) >= 2 else ''
            email = lines[3] if len(lines) >= 4 else ''

            return jsonify({
                "found": True,
                "name": name,
                "email": email,
            })

        return jsonify({"found": False})

    except Exception as e:
        print(f"User lookup error: {str(e)}")
        return jsonify({"found": False})


@app.route('/api/user/register', methods=['POST'])
def user_register():
    """Register a new customer after OTP verification.
    Creates customer in database."""
    if not DB_ENABLED:
        return jsonify({"error": "Database not available"}), 503

    data = request.json or {}
    name = data.get('name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()

    if not name or not phone or not email:
        return jsonify({"error": "חסרים פרטים"}), 400

    # Check if customer already exists
    existing = get_customer_by_phone(phone)
    if existing:
        return jsonify({
            "success": False,
            "error": "מספר זה כבר רשום במערכת",
            "customer": {
                "name": existing['name'],
                "phone": existing['phone'],
                "email": existing['email']
            }
        }), 409

    # Create new customer
    customer = create_customer(name, phone, email)
    if not customer:
        return jsonify({"error": "שגיאה ביצירת משתמש. נסי שוב."}), 500

    return jsonify({
        "success": True,
        "customer": {
            "name": customer['name'],
            "phone": customer['phone'],
            "email": customer['email']
        }
    })


# ============== ADMIN PANEL ==============

@app.route('/admin')
def admin_page():
    """Serve the admin panel page."""
    return send_from_directory('.', 'admin.html')


@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    """Authenticate admin user."""
    data = request.json
    if not data or not data.get('password'):
        return jsonify({"error": "Password required"}), 400

    if data['password'] == ADMIN_PASSWORD:
        session['admin_authenticated'] = True
        return jsonify({"success": True})
    else:
        return jsonify({"error": "סיסמה שגויה"}), 401


@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    """Logout admin user."""
    session.pop('admin_authenticated', None)
    return jsonify({"success": True})


@app.route('/api/admin/customers', methods=['GET'])
@admin_required
def get_admin_customers():
    """Get all customers for admin panel."""
    if not DB_ENABLED:
        return jsonify({"customers": [], "message": "Database not available"}), 503

    # Get pagination parameters
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    search = request.args.get('search', '').strip()

    try:
        if search:
            customers = search_customers(search)
        else:
            customers = get_all_customers(limit=limit, offset=offset)

        # Format dates for display
        for customer in customers:
            if customer.get('created_at'):
                created_at = customer['created_at']
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                customer['created_at_formatted'] = created_at.strftime('%d/%m/%Y')

        total_count = get_customer_count()

        return jsonify({
            "customers": customers,
            "total": total_count,
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        print(f"Error fetching customers: {str(e)}")
        return jsonify({"error": "שגיאה בטעינת לקוחות"}), 500


@app.route('/api/admin/blocked-slots', methods=['GET'])
@admin_required
def get_blocked_slots():
    """Get all blocked time slots."""
    return jsonify(load_blocked_slots())


@app.route('/api/admin/blocked-slots', methods=['POST'])
@admin_required
def update_blocked_slots():
    """Update blocked time slots for a specific date."""
    data = request.json
    if not data or 'date' not in data:
        return jsonify({"error": "Date required"}), 400

    date_str = data['date']
    slots = data.get('slots', [])

    blocked = load_blocked_slots()

    if slots:
        blocked[date_str] = slots
    else:
        blocked.pop(date_str, None)

    save_blocked_slots(blocked)
    return jsonify({"success": True, "blocked": blocked})


@app.route('/api/admin/blocked-slots/clear', methods=['POST'])
@admin_required
def clear_blocked_date():
    """Clear all blocked slots for a specific date."""
    data = request.json
    if not data or 'date' not in data:
        return jsonify({"error": "Date required"}), 400

    blocked = load_blocked_slots()
    blocked.pop(data['date'], None)
    save_blocked_slots(blocked)
    return jsonify({"success": True})


@app.route('/api/admin/gallery', methods=['GET'])
@admin_required
def get_gallery():
    """Get gallery images list."""
    gallery = load_gallery_data()
    return jsonify(gallery)


@app.route('/api/admin/gallery/upload', methods=['POST'])
@admin_required
def upload_gallery_image():
    """Upload a new gallery image."""
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed. Use JPG, PNG, or WebP"}), 400

    # Check file size
    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({"error": "File too large. Max 5MB"}), 400

    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"gallery_{timestamp}.{ext}"
    filepath = os.path.join(GALLERY_UPLOAD_DIR, filename)

    file.save(filepath)

    # Add to gallery data
    gallery = load_gallery_data()
    gallery['images'].append(filename)
    save_gallery_data(gallery)

    return jsonify({"success": True, "filename": filename})


@app.route('/api/admin/gallery/delete', methods=['POST'])
@admin_required
def delete_gallery_image():
    """Delete a gallery image."""
    data = request.json
    if not data or 'filename' not in data:
        return jsonify({"error": "Filename required"}), 400

    filename = secure_filename(data['filename'])
    filepath = os.path.join(GALLERY_UPLOAD_DIR, filename)

    # Remove file
    if os.path.exists(filepath):
        os.remove(filepath)

    # Update gallery data
    gallery = load_gallery_data()
    if filename in gallery['images']:
        gallery['images'].remove(filename)
        save_gallery_data(gallery)

    return jsonify({"success": True})


@app.route('/api/admin/gallery/reorder', methods=['POST'])
@admin_required
def reorder_gallery():
    """Reorder gallery images."""
    data = request.json
    if not data or 'images' not in data:
        return jsonify({"error": "Images list required"}), 400

    gallery = load_gallery_data()
    gallery['images'] = data['images']
    save_gallery_data(gallery)

    return jsonify({"success": True})


@app.route('/api/gallery-images', methods=['GET'])
def get_public_gallery():
    """Public endpoint to get gallery images for the main site."""
    gallery = load_gallery_data()
    return jsonify(gallery)


@app.route('/robots.txt')
def robots():
    """Serve robots.txt - exclude admin routes."""
    return "User-agent: *\nDisallow: /admin\nDisallow: /api/admin/\n", 200, {'Content-Type': 'text/plain'}


# ============== ERROR HANDLERS ==============

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def server_error(e):
    return jsonify({"error": "Internal server error"}), 500


# ============== MAIN ==============

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)

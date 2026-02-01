"""
LISHAY SIMANI Beauty Studio - Flask Server for Railway
Serves the static HTML/CSS/JS website and provides booking API
"""

from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime, timedelta, date
import os
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

app = Flask(__name__, static_folder='.', static_url_path='')

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


def check_and_send_reminders():
    """
    Check for upcoming appointments and send reminders.
    Called by the scheduler.
    """
    try:
        # Clean up old reminder keys first
        cleanup_old_reminders()

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
                    print(f"Sent day-before reminder to {email}")

            # Check if we need to send morning reminder (08:00 same day)
            if event_date == today and now.hour == 8:
                reminder_key = f"morning_{event_id}"
                if reminder_key not in sent_reminders:
                    send_reminder_morning(booking_data)
                    sent_reminders[reminder_key] = event_date
                    print(f"Sent morning reminder to {email}")

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

        # Find service details
        service = None
        for s in SERVICES:
            if s['name'] == data['service'] or s['name_he'] == data['service']:
                service = s
                break

        if not service:
            return jsonify({"error": "Invalid service"}), 400

        # Check availability (with error handling)
        try:
            is_available = check_availability(data['date'], data['time'], service['duration'])
            if not is_available:
                return jsonify({"error": "התור כבר לא פנוי. נא לבחור שעה אחרת."}), 409
        except Exception as cal_error:
            print(f"Calendar check error (proceeding anyway): {str(cal_error)}")
            # Continue with booking even if calendar check fails

        # Create booking
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
        except Exception as cal_error:
            print(f"Failed to create calendar event: {str(cal_error)}")
            # Continue - we'll still send confirmation email

        # Send confirmation email via SendGrid HTTP API
        email_sent = False
        try:
            email_sent = send_booking_confirmation(booking_data)
        except Exception as email_error:
            print(f"Failed to send confirmation email: {str(email_error)}")

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

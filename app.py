from flask import Flask, render_template, request, jsonify
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import calendar service
from calendar_service import (
    filter_available_slots,
    check_availability,
    create_event
)

# Import reminder scheduler
from scheduler import start_scheduler

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'lishay-simani-luxury-nails-2024')

# Services data with duration for calendar events
SERVICES = [
    {"name": "Gel Polish", "name_he": "לק ג'ל", "price": 120, "duration": 60},
    {"name": "Anatomical Build", "name_he": "בנייה אנטומית", "price": 140, "duration": 75},
    {"name": "Gel Fill", "name_he": "מילוי ג'ל", "price": 150, "duration": 60},
    {"name": "Single Nail Extension", "name_he": "הארכת ציפורן בודדת (מעל 2)", "price": 10, "duration": 10, "note": "per nail"},
    {"name": "Building", "name_he": "בנייה", "price": 300, "duration": 120},
    {"name": "Eyebrows", "name_he": "גבות", "price": 50, "duration": 20},
    {"name": "Mustache", "name_he": "שפם", "price": 15, "duration": 10},
    {"name": "Eyebrow Tinting", "name_he": "צביעת גבות", "price": 30, "duration": 15},
]

# Business hours
BUSINESS_HOURS = {
    0: {"open": "09:00", "close": "20:00"},  # Sunday
    1: {"open": "09:00", "close": "20:00"},  # Monday
    2: {"open": "09:00", "close": "20:00"},  # Tuesday
    3: {"open": "09:00", "close": "20:00"},  # Wednesday
    4: {"open": "09:00", "close": "20:00"},  # Thursday
    5: None,  # Friday - closed
    6: None,  # Saturday - closed
}


def get_service_by_name(service_name):
    """Find a service by its Hebrew or English name."""
    for service in SERVICES:
        if service['name'] == service_name or service['name_he'] == service_name:
            return service
    return None


@app.route('/')
def home():
    return render_template('index.html', services=SERVICES)


@app.route('/api/available-slots', methods=['GET'])
def get_available_slots():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({"error": "Date required"}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        day_of_week = date.weekday()
        # Convert Python weekday (Monday=0) to our format (Sunday=0)
        day_of_week = (day_of_week + 1) % 7

        hours = BUSINESS_HOURS.get(day_of_week)
        if not hours:
            return jsonify({"slots": [], "message": "Closed on this day"})

        # Generate all possible time slots (every 30 minutes)
        all_slots = []
        open_time = datetime.strptime(hours["open"], "%H:%M")
        close_time = datetime.strptime(hours["close"], "%H:%M")

        current = open_time
        while current < close_time:
            all_slots.append(current.strftime("%H:%M"))
            current += timedelta(minutes=30)

        # Filter out busy slots from Google Calendar
        available_slots = filter_available_slots(date_str, all_slots)

        return jsonify({"slots": available_slots})
    except ValueError:
        return jsonify({"error": "Invalid date format"}), 400


@app.route('/api/book', methods=['POST'])
def book_appointment():
    data = request.json

    required_fields = ['name', 'phone', 'email', 'service', 'date', 'time']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    # Get service details
    service = get_service_by_name(data['service'])
    if not service:
        return jsonify({"error": "Invalid service"}), 400

    # Check if the slot is still available
    if not check_availability(data['date'], data['time'], service['duration']):
        return jsonify({
            "success": False,
            "error": "This time slot is no longer available. Please choose another time."
        }), 409  # Conflict

    # Prepare booking data for calendar
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

    try:
        # Create event in Google Calendar
        event = create_event(booking_data)

        return jsonify({
            "success": True,
            "message": "Appointment booked successfully!",
            "booking": {
                "name": data['name'],
                "service": service['name_he'],
                "date": data['date'],
                "time": data['time'],
                "event_id": event.get('id')
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to create appointment: {str(e)}"
        }), 500


@app.route('/api/contact', methods=['POST'])
def contact():
    data = request.json

    required_fields = ['name', 'phone', 'message']
    for field in required_fields:
        if not data.get(field):
            return jsonify({"error": f"{field} is required"}), 400

    # In production, send email or save to database
    return jsonify({
        "success": True,
        "message": "Message sent successfully!"
    })


if __name__ == '__main__':
    # Start the reminder scheduler
    start_scheduler()

    app.run(debug=True, port=5000, use_reloader=False)

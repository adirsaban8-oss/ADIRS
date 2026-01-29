import streamlit as st
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

# Page configuration
st.set_page_config(
    page_title="LISHAI SIMAN | מניקוריסטית מקצועית",
    page_icon="💅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for RTL and styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Heebo', sans-serif;
    }

    .main {
        direction: rtl;
        text-align: right;
    }

    .stApp {
        direction: rtl;
    }

    h1, h2, h3, h4, h5, h6, p, label, span {
        direction: rtl;
        text-align: right;
    }

    .hero-title {
        font-size: 3rem;
        text-align: center;
        color: #C9A86C;
        margin-bottom: 0;
    }

    .hero-subtitle {
        font-size: 1.5rem;
        text-align: center;
        color: #666;
        margin-top: 0;
    }

    .service-card {
        background: linear-gradient(135deg, #faf8f5 0%, #fff 100%);
        border: 1px solid #e8e0d5;
        border-radius: 15px;
        padding: 20px;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
    }

    .service-name {
        font-size: 1.3rem;
        color: #333;
        font-weight: 600;
    }

    .service-price {
        font-size: 1.5rem;
        color: #C9A86C;
        font-weight: 700;
    }

    .section-header {
        text-align: center;
        margin: 40px 0 30px 0;
    }

    .gold-text {
        color: #C9A86C;
    }

    .policy-card {
        background: #fff8e7;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        border-right: 4px solid #C9A86C;
    }

    .contact-info {
        background: #f9f6f2;
        padding: 20px;
        border-radius: 10px;
    }

    .stButton > button {
        background: linear-gradient(135deg, #C9A86C 0%, #b8956a 100%);
        color: white;
        border: none;
        padding: 10px 30px;
        border-radius: 25px;
        font-weight: 600;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #b8956a 0%, #a8855a 100%);
    }

    .success-message {
        background: #d4edda;
        color: #155724;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 20px 0;
    }

    .error-message {
        background: #f8d7da;
        color: #721c24;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin: 20px 0;
    }
</style>
""", unsafe_allow_html=True)

# Services data
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


def get_available_slots(date_str):
    """Get available time slots for a given date."""
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d')
        day_of_week = date.weekday()
        # Convert Python weekday (Monday=0) to our format (Sunday=0)
        day_of_week = (day_of_week + 1) % 7

        hours = BUSINESS_HOURS.get(day_of_week)
        if not hours:
            return [], "סגור ביום זה"

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
        return available_slots, None
    except ValueError:
        return [], "תאריך לא תקין"


# ============== HEADER ==============
st.markdown("<p style='text-align: left; font-weight: bold;'>בס\"ד</p>", unsafe_allow_html=True)

st.markdown("<h1 class='hero-title'>LISHAI SIMAN</h1>", unsafe_allow_html=True)
st.markdown("<p class='hero-subtitle'>מניקוריסטית מקצועית</p>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>יוקרה, מקצועיות ודיוק בכל ציפורן</p>", unsafe_allow_html=True)

st.markdown("---")

# ============== NAVIGATION ==============
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏠 בית", "💅 שירותים", "📅 הזמנת תור", "📞 צור קשר", "ℹ️ אודות"])

# ============== HOME TAB ==============
with tab1:
    st.markdown("## ברוכות הבאות!")
    st.markdown("""
    אני לישי סימני, מניקוריסטית מקצועית מקרני שומרון.

    בסטודיו שלי תמצאי חוויה יוקרתית ואישית עם תשומת לב לכל פרט.
    """)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 📍 מיקום")
        st.write("משעול הרקפת 3, קרני שומרון")
    with col2:
        st.markdown("### 📞 טלפון")
        st.write("051-5656295")
    with col3:
        st.markdown("### 🕐 שעות פעילות")
        st.write("ראשון - חמישי: 09:00 - 20:00")
        st.write("שישי - שבת: סגור")

# ============== SERVICES TAB ==============
with tab2:
    st.markdown("## 💅 השירותים שלנו")
    st.markdown("<p style='text-align: center; color: #888;'>טיפולים יוקרתיים במחירים הוגנים</p>", unsafe_allow_html=True)

    # Display services in a grid
    cols = st.columns(2)
    for i, service in enumerate(SERVICES):
        with cols[i % 2]:
            st.markdown(f"""
            <div class='service-card'>
                <p class='service-name'>{service['name_he']}</p>
                <p style='color: #888; font-size: 0.9rem;'>{service['name']}</p>
                <p class='service-price'>{service['price']}₪</p>
                {f"<p style='font-size: 0.8rem; color: #999;'>(לציפורן)</p>" if service.get('note') else ""}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Cancellation Policy
    st.markdown("## 📋 מדיניות ביטולים")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='policy-card'>
            <h4>⚠️ ביטול באותו היום</h4>
            <p>חיוב של 50% מעלות הטיפול</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='policy-card'>
            <h4>❌ אי הגעה ללא הודעה</h4>
            <p>חיוב מלא של עלות הטיפול</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='policy-card'>
            <h4>🕐 איחור מעל 15 דקות</h4>
            <p>ללא הודעה - ייחשב כביטול עם חיוב 50%</p>
        </div>
        """, unsafe_allow_html=True)

# ============== BOOKING TAB ==============
with tab3:
    st.markdown("## 📅 הזמנת תור")
    st.markdown("<p style='text-align: center; color: #888;'>בחרי תאריך ושעה שנוחים לך</p>", unsafe_allow_html=True)

    # Initialize session state for booking
    if 'booking_success' not in st.session_state:
        st.session_state.booking_success = False
    if 'booking_error' not in st.session_state:
        st.session_state.booking_error = None

    # Show success/error messages
    if st.session_state.booking_success:
        st.markdown("""
        <div class='success-message'>
            <h3>✅ התור נקבע בהצלחה!</h3>
            <p>נשמח לראותך בקרוב</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("הזמיני תור נוסף"):
            st.session_state.booking_success = False
            st.rerun()
    elif st.session_state.booking_error:
        st.error(st.session_state.booking_error)
        st.session_state.booking_error = None
    else:
        # Booking form
        with st.form("booking_form"):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input("שם מלא", placeholder="הכניסי את שמך")
            with col2:
                phone = st.text_input("טלפון", placeholder="050-0000000")

            email = st.text_input("אימייל (לקבלת תזכורות)", placeholder="your@email.com")

            # Service selection
            service_options = [f"{s['name_he']} - {s['price']}₪" for s in SERVICES]
            selected_service = st.selectbox("בחרי שירות", options=[""] + service_options)

            col1, col2 = st.columns(2)

            with col1:
                # Date selection
                min_date = datetime.now().date()
                max_date = min_date + timedelta(days=60)
                selected_date = st.date_input(
                    "תאריך",
                    min_value=min_date,
                    max_value=max_date,
                    value=min_date
                )

            with col2:
                # Time selection based on available slots
                if selected_date:
                    date_str = selected_date.strftime('%Y-%m-%d')
                    available_slots, error_msg = get_available_slots(date_str)

                    if error_msg:
                        st.warning(error_msg)
                        selected_time = st.selectbox("שעה", options=["אין תורים פנויים"])
                    elif available_slots:
                        selected_time = st.selectbox("שעה", options=["בחרי שעה"] + available_slots)
                    else:
                        selected_time = st.selectbox("שעה", options=["אין תורים פנויים"])
                else:
                    selected_time = st.selectbox("שעה", options=["בחרי תאריך קודם"])

            notes = st.text_area("הערות (אופציונלי)", placeholder="הערות נוספות...")

            submitted = st.form_submit_button("📅 אשרי הזמנה", use_container_width=True)

            if submitted:
                # Validation
                if not name:
                    st.error("נא להזין שם מלא")
                elif not phone:
                    st.error("נא להזין מספר טלפון")
                elif not email:
                    st.error("נא להזין כתובת אימייל")
                elif not selected_service or selected_service == "":
                    st.error("נא לבחור שירות")
                elif not selected_time or selected_time in ["בחרי שעה", "אין תורים פנויים", "בחרי תאריך קודם"]:
                    st.error("נא לבחור שעה")
                else:
                    # Get service details
                    service_name_he = selected_service.split(" - ")[0]
                    service = None
                    for s in SERVICES:
                        if s['name_he'] == service_name_he:
                            service = s
                            break

                    if service:
                        date_str = selected_date.strftime('%Y-%m-%d')

                        # Check availability
                        if not check_availability(date_str, selected_time, service['duration']):
                            st.session_state.booking_error = "התור כבר לא פנוי. נא לבחור שעה אחרת."
                            st.rerun()
                        else:
                            # Create booking
                            booking_data = {
                                "name": name,
                                "phone": phone,
                                "email": email,
                                "service": service['name'],
                                "service_he": service['name_he'],
                                "date": date_str,
                                "time": selected_time,
                                "duration": service['duration'],
                                "notes": notes,
                            }

                            try:
                                event = create_event(booking_data)
                                st.session_state.booking_success = True
                                st.rerun()
                            except Exception as e:
                                st.session_state.booking_error = f"שגיאה ביצירת התור: {str(e)}"
                                st.rerun()

# ============== CONTACT TAB ==============
with tab4:
    st.markdown("## 📞 צור קשר")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='contact-info'>
            <h3>פרטי התקשרות</h3>
            <p><strong>📍 כתובת:</strong> משעול הרקפת 3, קרני שומרון</p>
            <p><strong>📞 טלפון:</strong> <a href="tel:051-5656295">051-5656295</a></p>
            <p><strong>🕐 שעות פעילות:</strong></p>
            <p>ראשון - חמישי: 09:00 - 20:00</p>
            <p>שישי - שבת: סגור</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 🔗 עקבי אחריי")
        col_ig, col_wa = st.columns(2)
        with col_ig:
            st.link_button("📸 Instagram", "https://www.instagram.com/lishai_simani_beauty")
        with col_wa:
            st.link_button("💬 WhatsApp", "https://wa.me/972515656295?text=Hi%20I%20came%20from%20the%20website")

    with col2:
        st.markdown("### 📝 שלחי הודעה")

        with st.form("contact_form"):
            contact_name = st.text_input("שם מלא", key="contact_name")
            contact_phone = st.text_input("טלפון", key="contact_phone")
            contact_message = st.text_area("הודעה", key="contact_message")

            contact_submitted = st.form_submit_button("📤 שלחי הודעה", use_container_width=True)

            if contact_submitted:
                if contact_name and contact_phone and contact_message:
                    st.success("ההודעה נשלחה בהצלחה! אחזור אלייך בהקדם.")
                else:
                    st.error("נא למלא את כל השדות")

# ============== ABOUT TAB ==============
with tab5:
    st.markdown("## ℹ️ אודות")
    st.markdown("### הכירי את לישי")

    st.markdown("""
    שלום, אני **לישי סימני**, מניקוריסטית מקצועית עם תשוקה אמיתית לאמנות הציפורניים.

    בסטודיו שלי בקרני שומרון, אני מציעה חוויה יוקרתית ואישית לכל לקוחה.

    אני מאמינה שכל אישה ראויה להרגיש מפונקת ויפה. בכל טיפול אני משקיעה תשומת לב מלאה
    לפרטים הקטנים ביותר, משתמשת בחומרים איכותיים בלבד ומקפידה על סטריליות מושלמת.
    """)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 🏆")
        st.markdown("**מקצועיות**")
    with col2:
        st.markdown("### 💎")
        st.markdown("**יוקרה**")
    with col3:
        st.markdown("### ❤️")
        st.markdown("**אכפתיות**")
    with col4:
        st.markdown("### 🛡️")
        st.markdown("**היגיינה**")

# ============== FOOTER ==============
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 20px;'>
    <p><strong>LISHAI SIMAN</strong> | מניקוריסטית מקצועית</p>
    <p>משעול הרקפת 3, קרני שומרון | 051-5656295</p>
    <p>© 2024 כל הזכויות שמורות</p>
</div>
""", unsafe_allow_html=True)

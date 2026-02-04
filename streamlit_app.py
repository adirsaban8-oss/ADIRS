למ        font-size: 0.85rem !important;
        margin: 20px 0 0 0 !important;
    }

    /* ============== FORM ELEMENTS ============== */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div {
        direction: rtl !important;
        text-align: right !important;
        border-radius: 12px !important;
        border: 1px solid #E8E0D5 !important;
        padding: 12px 16px !important;
        background: #FFFFFF !important;
        transition: all 0.3s ease !important;
    }

    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #C9A86C !important;
        box-shadow: 0 0 0 3px rgba(201, 168, 108, 0.1) !important;
    }

    .stTextInput > label,
    .stTextArea > label,
    .stSelectbox > label,
    .stDateInput > label {
        direction: rtl !important;
        text-align: right !important;
        font-weight: 500 !important;
        color: #333 !important;
        margin-bottom: 5px !important;
    }

    .stDateInput > div > div > input {
        direction: ltr !important;
        text-align: center !important;
        border-radius: 12px !important;
        border: 1px solid #E8E0D5 !important;
    }

    /* ============== BUTTONS ============== */
    .stButton > button {
        background: linear-gradient(135deg, #C9A86C 0%, #B8956A 100%) !important;
        color: white !important;
        border: none !important;
        padding: 14px 35px !important;
        border-radius: 30px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        width: 100% !important;
        min-height: 52px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(201, 168, 108, 0.3) !important;
    }

    .stButton > button:hover {
        background: linear-gradient(135deg, #B8956A 0%, #A8855A 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(201, 168, 108, 0.4) !important;
    }

    .stFormSubmitButton > button {
        background: linear-gradient(135deg, #C9A86C 0%, #B8956A 100%) !important;
        color: white !important;
        border: none !important;
        padding: 14px 35px !important;
        border-radius: 30px !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        width: 100% !important;
        min-height: 52px !important;
        margin-top: 10px !important;
        box-shadow: 0 4px 15px rgba(201, 168, 108, 0.3) !important;
    }

    .stFormSubmitButton > button:hover {
        background: linear-gradient(135deg, #B8956A 0%, #A8855A 100%) !important;
    }

    .stLinkButton > a {
        background: linear-gradient(135deg, #C9A86C 0%, #B8956A 100%) !important;
        color: white !important;
        border: none !important;
        padding: 12px 25px !important;
        border-radius: 25px !important;
        font-weight: 600 !important;
        text-decoration: none !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 48px !important;
        box-shadow: 0 4px 15px rgba(201, 168, 108, 0.3) !important;
    }

    /* ============== SECTION HEADERS ============== */
    .section-title {
        text-align: center !important;
        color: #333 !important;
        font-size: 2rem !important;
        font-weight: 600 !important;
        margin-bottom: 10px !important;
    }

    .section-subtitle {
        text-align: center !important;
        color: #888 !important;
        font-size: 1.1rem !important;
        margin-bottom: 30px !important;
    }

    /* ============== DIVIDER ============== */
    hr {
        margin: 30px 0 !important;
        border: none !important;
        border-top: 1px solid #E8E0D5 !important;
    }

    /* ============== COLUMNS ============== */
    [data-testid="column"] {
        direction: rtl !important;
        text-align: right !important;
    }

    /* ============== SUCCESS MESSAGE ============== */
    .success-message {
        background: linear-gradient(135deg, #D4EDDA 0%, #C3E6CB 100%) !important;
        color: #155724 !important;
        padding: 30px !important;
        border-radius: 16px !important;
        text-align: center !important;
        margin: 20px 0 !important;
        border: 1px solid #C3E6CB !important;
    }

    .success-message h3 {
        margin: 0 0 10px 0 !important;
        text-align: center !important;
        font-size: 1.3rem !important;
    }

    .success-message p {
        margin: 0 !important;
        text-align: center !important;
    }

    /* ============== ALERTS ============== */
    .stAlert {
        direction: rtl !important;
        text-align: right !important;
        border-radius: 12px !important;
    }

    /* ============== BSD HEADER ============== */
    .bsd-text {
        text-align: left !important;
        font-weight: bold !important;
        font-size: 14px !important;
        padding: 5px 0 !important;
        direction: ltr !important;
        color: #999 !important;
    }

    /* ============== RESPONSIVE ============== */
    @media (max-width: 992px) {
        .services-grid {
            grid-template-columns: repeat(2, 1fr) !important;
        }
        .about-features {
            grid-template-columns: repeat(2, 1fr) !important;
        }
        .booking-container {
            grid-template-columns: 1fr !important;
        }
    }

    @media (max-width: 768px) {
        .services-grid {
            grid-template-columns: 1fr !important;
        }
        .policies-grid {
            grid-template-columns: 1fr !important;
        }
        .gallery-grid {
            grid-template-columns: repeat(2, 1fr) !important;
        }
        .contact-grid {
            grid-template-columns: 1fr !important;
        }
        .about-features {
            grid-template-columns: 1fr !important;
        }
        .hero-title {
            font-size: 2.5rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

# Services data
SERVICES = [
    {"name": "Gel Polish", "name_he": "לק ג'ל", "price": 120, "duration": 60, "icon": "💅"},
    {"name": "Anatomical Build", "name_he": "בנייה אנטומית", "price": 140, "duration": 75, "icon": "✨"},
    {"name": "Gel Fill", "name_he": "מילוי ג'ל", "price": 150, "duration": 60, "icon": "💎"},
    {"name": "Single Nail Extension", "name_he": "הארכת ציפורן בודדת", "price": 10, "duration": 10, "note": "per nail", "icon": "💫"},
    {"name": "Building", "name_he": "בנייה", "price": 300, "duration": 120, "icon": "🏆"},
    {"name": "Eyebrows", "name_he": "גבות", "price": 50, "duration": 20, "icon": "👁️"},
    {"name": "Mustache", "name_he": "שפם", "price": 15, "duration": 10, "icon": "✂️"},
    {"name": "Eyebrow Tinting", "name_he": "צביעת גבות", "price": 30, "duration": 15, "icon": "🎨"},
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
st.markdown("<p class='bsd-text'>בס\"ד</p>", unsafe_allow_html=True)

st.markdown("""
<div class='hero-container'>
    <h1 class='hero-title'>LISHAI SIMANI</h1>
    <p class='hero-subtitle'>מניקוריסטית מקצועית</p>
    <p class='hero-tagline'>יוקרה, מקצועיות ודיוק בכל ציפורן</p>
</div>
""", unsafe_allow_html=True)

# ============== NAVIGATION ==============
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🏠 בית", "💅 שירותים", "📋 מדיניות", "📅 הזמנת תור", "🖼️ גלריה", "📞 צור קשר"])

# ============== HOME TAB ==============
with tab1:
    st.markdown("<h2 class='section-title'>ברוכות הבאות!</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>אני לישי סימני, מניקוריסטית מקצועית מקרני שומרון</p>", unsafe_allow_html=True)

    st.markdown("""
    בסטודיו שלי תמצאי חוויה יוקרתית ואישית עם תשומת לב לכל פרט.
    אני מאמינה שכל אישה ראויה להרגיש מפונקת ויפה.
    """)

    st.markdown("---")

    # Info cards grid
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class='info-card'>
            <div class='info-card-title'>📍 מיקום</div>
            <p>משעול הרקפת 3</p>
            <p>קרני שומרון</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='info-card'>
            <div class='info-card-title'>📞 טלפון</div>
            <p>051-5656295</p>
            <p>מענה בשעות הפעילות</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='info-card'>
            <div class='info-card-title'>🕐 שעות פעילות</div>
            <p>ראשון - חמישי: 09:00 - 20:00</p>
            <p>שישי - שבת: סגור</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Features
    st.markdown("<h2 class='section-title'>למה לבחור בי?</h2>", unsafe_allow_html=True)

    st.markdown("""
    <div class='about-features'>
        <div class='feature-badge'>
            <div class='feature-icon'>🏆</div>
            <p class='feature-title'>מקצועיות</p>
        </div>
        <div class='feature-badge'>
            <div class='feature-icon'>💎</div>
            <p class='feature-title'>יוקרה</p>
        </div>
        <div class='feature-badge'>
            <div class='feature-icon'>❤️</div>
            <p class='feature-title'>אכפתיות</p>
        </div>
        <div class='feature-badge'>
            <div class='feature-icon'>🛡️</div>
            <p class='feature-title'>היגיינה</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============== SERVICES TAB ==============
with tab2:
    st.markdown("<h2 class='section-title'>💅 השירותים שלנו</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>טיפולים יוקרתיים במחירים הוגנים</p>", unsafe_allow_html=True)

    # Build services grid HTML - 4 per row
    services_html = "<div class='services-grid'>"
    for service in SERVICES:
        duration_text = f"{service['duration']} דק׳"
        note_text = "(לציפורן)" if service.get('note') else ""
        services_html += f"""
        <div class='service-card'>
            <div class='service-icon'>{service['icon']}</div>
            <p class='service-name'>{service['name_he']}</p>
            <p class='service-duration'>{duration_text}</p>
            <p class='service-price'>{service['price']}₪ {note_text}</p>
            <a href='#הזמנת-תור' class='service-btn'>הזמיני עכשיו</a>
        </div>
        """
    services_html += "</div>"
    st.markdown(services_html, unsafe_allow_html=True)

# ============== POLICIES TAB ==============
with tab3:
    st.markdown("<h2 class='section-title'>📋 מדיניות ביטולים</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>נא לקרוא בעיון לפני הזמנת תור</p>", unsafe_allow_html=True)

    st.markdown("""
    <div class='policies-grid'>
        <div class='policy-card'>
            <div class='policy-icon policy-icon-warning'>⚠️</div>
            <p class='policy-title'>ביטול באותו היום</p>
            <p class='policy-text'>חיוב של 50% מעלות הטיפול</p>
        </div>
        <div class='policy-card'>
            <div class='policy-icon policy-icon-danger'>❌</div>
            <p class='policy-title'>אי הגעה ללא הודעה</p>
            <p class='policy-text'>חיוב מלא של עלות הטיפול</p>
        </div>
        <div class='policy-card'>
            <div class='policy-icon policy-icon-clock'>🕐</div>
            <p class='policy-title'>איחור מעל 15 דקות</p>
            <p class='policy-text'>ללא הודעה מראש - ייחשב כביטול עם חיוב 50%</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("""
    <div class='info-card' style='max-width: 600px; margin: 0 auto;'>
        <div class='info-card-title'>💡 טיפ חשוב</div>
        <p>לביטול או שינוי תור, נא ליצור קשר לפחות 24 שעות מראש.</p>
        <p>ניתן להודיע בוואטסאפ או בטלפון: 051-5656295</p>
    </div>
    """, unsafe_allow_html=True)

# ============== BOOKING TAB ==============
with tab4:
    st.markdown("<h2 class='section-title'>📅 הזמנת תור</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>בחרי תאריך ושעה שנוחים לך</p>", unsafe_allow_html=True)

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
        # Two column layout - form and sidebar
        col_form, col_sidebar = st.columns([2, 1])

        with col_form:
            # Booking form
            with st.form("booking_form"):
                st.markdown("### פרטים אישיים")

                col1, col2 = st.columns(2)
                with col1:
                    name = st.text_input("שם מלא", placeholder="הכניסי את שמך")
                with col2:
                    phone = st.text_input("טלפון", placeholder="050-0000000")

                email = st.text_input("אימייל (לקבלת תזכורות)", placeholder="your@email.com")

                st.markdown("### פרטי התור")

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

        with col_sidebar:
            st.markdown("""
            <div class='info-card'>
                <div class='info-card-title'>📍 מיקום הסטודיו</div>
                <p>משעול הרקפת 3</p>
                <p>קרני שומרון</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='info-card'>
                <div class='info-card-title'>🕐 שעות פעילות</div>
                <p>ראשון - חמישי</p>
                <p>09:00 - 20:00</p>
                <p style='color: #999; font-size: 0.85rem;'>שישי - שבת: סגור</p>
            </div>
            """, unsafe_allow_html=True)

            st.markdown("""
            <div class='info-card'>
                <div class='info-card-title'>📞 צרי קשר</div>
                <p>051-5656295</p>
            </div>
            """, unsafe_allow_html=True)

# ============== GALLERY TAB ==============
with tab5:
    st.markdown("<h2 class='section-title'>🖼️ גלריה</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>עבודות אחרונות מהסטודיו</p>", unsafe_allow_html=True)

    # Check if gallery images exist
    gallery_path = "static/images/"
    gallery_images = []
    for i in range(1, 8):
        img_path = f"{gallery_path}gallery{i}.jpeg"
        if os.path.exists(img_path):
            gallery_images.append(img_path)

    if gallery_images:
        # Display in 3 columns
        cols = st.columns(3)
        for i, img_path in enumerate(gallery_images):
            with cols[i % 3]:
                st.image(img_path, use_container_width=True)
    else:
        st.info("תמונות הגלריה יעלו בקרוב...")

# ============== CONTACT TAB ==============
with tab6:
    st.markdown("<h2 class='section-title'>📞 צור קשר</h2>", unsafe_allow_html=True)
    st.markdown("<p class='section-subtitle'>נשמח לשמוע ממך</p>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class='contact-info-box'>
            <h3>פרטי התקשרות</h3>
            <div class='contact-item'>
                <div class='contact-icon'>📍</div>
                <div>
                    <p><strong>כתובת</strong></p>
                    <p>משעול הרקפת 3, קרני שומרון</p>
                </div>
            </div>
            <div class='contact-item'>
                <div class='contact-icon'>📞</div>
                <div>
                    <p><strong>טלפון</strong></p>
                    <p>051-5656295</p>
                </div>
            </div>
            <div class='contact-item'>
                <div class='contact-icon'>🕐</div>
                <div>
                    <p><strong>שעות פעילות</strong></p>
                    <p>ראשון - חמישי: 09:00 - 20:00</p>
                    <p>שישי - שבת: סגור</p>
                </div>
            </div>
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

# ============== FOOTER ==============
st.markdown("---")
st.markdown("""
<div class='footer-container'>
    <p class='footer-brand'>LISHAI SIMANI</p>
    <p class='footer-tagline'>מניקוריסטית מקצועית</p>
    <div class='footer-nav'>
        <span class='footer-link'>בית</span>
        <span class='footer-link'>שירותים</span>
        <span class='footer-link'>מדיניות</span>
        <span class='footer-link'>הזמנת תור</span>
        <span class='footer-link'>גלריה</span>
        <span class='footer-link'>צור קשר</span>
    </div>
    <p>משעול הרקפת 3, קרני שומרון | 051-5656295</p>
    <p class='footer-copyright'>© 2024 כל הזכויות שמורות</p>
</div>
""", unsafe_allow_html=True)

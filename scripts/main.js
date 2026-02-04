/* ============================================
   MAIN JAVASCRIPT - LISHAI SIMANI BEAUTY STUDIO
   Connected to Flask API for Railway Deployment
   ============================================ */

// ============== CONFIGURATION ==============

const CONFIG = {
    API_BASE: '', // Empty for same-origin requests
    BUSINESS_HOURS: {
        start: '09:00',
        end: '20:00',
        interval: 30,
        daysOpen: [0, 1, 2, 3, 4], // Sunday-Thursday
    },
    SERVICES: {
        'gel-polish': { name: 'לק ג\'ל', nameEn: 'Gel Polish', duration: 60, price: 120 },
        'anatomical-build': { name: 'בנייה אנטומית', nameEn: 'Anatomical Build', duration: 75, price: 140 },
        'gel-fill': { name: 'מילוי ג\'ל', nameEn: 'Gel Fill', duration: 60, price: 150 },
        'building': { name: 'בנייה', nameEn: 'Building', duration: 120, price: 300 },
        'eyebrows': { name: 'גבות', nameEn: 'Eyebrows', duration: 20, price: 50 },
        'mustache': { name: 'שפם', nameEn: 'Mustache', duration: 10, price: 15 },
        'eyebrow-tinting': { name: 'צביעת גבות', nameEn: 'Eyebrow Tinting', duration: 15, price: 30 },
    }
};

// ============== USER IDENTITY ==============

const UserIdentity = {
    KEYS: {
        name: 'lishai_user_name',
        phone: 'lishai_user_phone',
        email: 'lishai_user_email',
    },

    get() {
        const name = localStorage.getItem(this.KEYS.name) || '';
        const phone = localStorage.getItem(this.KEYS.phone) || '';
        const email = localStorage.getItem(this.KEYS.email) || '';
        if (name && phone && email) return { name, phone, email };
        return null;
    },

    save(name, phone, email) {
        localStorage.setItem(this.KEYS.name, name.trim());
        localStorage.setItem(this.KEYS.phone, phone.trim());
        localStorage.setItem(this.KEYS.email, email.trim());
    },

    clear() {
        localStorage.removeItem(this.KEYS.name);
        localStorage.removeItem(this.KEYS.phone);
        localStorage.removeItem(this.KEYS.email);
    },

    exists() {
        return !!this.get();
    },

    reset() {
        this.clear();
        location.reload();
    },

    validate(name, phone, email) {
        const errors = [];
        if (!name || name.trim().length < 2) errors.push('נא להזין שם מלא');
        const phoneClean = (phone || '').replace(/[-\s]/g, '');
        if (!phoneClean || !/^0(5[0-9]|[2-4]|[8-9])\d{7}$/.test(phoneClean)) errors.push('נא להזין מספר טלפון תקין');
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.push('נא להזין כתובת אימייל תקינה');
        return errors;
    },

    showOverlay() {
        const overlay = document.getElementById('identityOverlay');
        if (overlay) overlay.style.display = 'flex';
    },

    hideOverlay() {
        const overlay = document.getElementById('identityOverlay');
        if (overlay) overlay.style.display = 'none';
    },

    showResetBtn() {
        const el = document.getElementById('navIdentityReset');
        if (el) el.style.display = '';
    },

    init() {
        const form = document.getElementById('identityForm');

        if (this.exists()) {
            this.hideOverlay();
            this.showResetBtn();
        } else {
            this.showOverlay();
        }

        if (form) {
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const name = document.getElementById('idName').value;
                const phone = document.getElementById('idPhone').value;
                const email = document.getElementById('idEmail').value;

                const errors = this.validate(name, phone, email);
                const errEl = document.getElementById('identityError');

                if (errors.length > 0) {
                    if (errEl) {
                        errEl.textContent = errors.join('. ');
                        errEl.style.display = '';
                    }
                    return;
                }

                if (errEl) errEl.style.display = 'none';
                this.save(name, phone, email);
                this.hideOverlay();
                this.showResetBtn();

                // Trigger My Appointments auto-lookup
                MyAppointments.lookupPhone(phone);
            });
        }
    }
};

// Make reset available globally for onclick
window.UserIdentity = UserIdentity;

// ============== DOM ELEMENTS ==============

const navbar = document.getElementById('navbar');
const navToggle = document.getElementById('navToggle');
const navMenu = document.getElementById('navMenu');
const navLinks = document.querySelectorAll('.nav-link');
const bookingForm = document.getElementById('bookingForm');
const contactForm = document.getElementById('contactForm');
const dateInput = document.getElementById('dateInput');
const timeSlotsContainer = document.getElementById('timeSlots');
const successModal = document.getElementById('successModal');

// ============== NAVIGATION ==============

// Scroll effect for navbar
window.addEventListener('scroll', () => {
    if (window.scrollY > 50) {
        navbar.classList.add('scrolled');
    } else {
        navbar.classList.remove('scrolled');
    }
});

// Mobile menu toggle
navToggle.addEventListener('click', () => {
    navMenu.classList.toggle('active');
    navToggle.classList.toggle('active');
});

// Close mobile menu on link click
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        navMenu.classList.remove('active');
        navToggle.classList.remove('active');
    });
});

// Active link on scroll
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('section[id]');
    const scrollPos = window.scrollY + 100;

    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        const sectionId = section.getAttribute('id');

        if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
            navLinks.forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${sectionId}`) {
                    link.classList.add('active');
                }
            });
        }
    });
});

// ============== DATE & TIME SLOTS ==============

// Set minimum date to today
const today = new Date();
const todayStr = today.toISOString().split('T')[0];
dateInput.setAttribute('min', todayStr);

// Set maximum date to 30 days from now
const maxDate = new Date();
maxDate.setDate(maxDate.getDate() + 30);
dateInput.setAttribute('max', maxDate.toISOString().split('T')[0]);

// Check if date is a business day
function isBusinessDay(date) {
    const dayOfWeek = date.getDay();
    return CONFIG.BUSINESS_HOURS.daysOpen.includes(dayOfWeek);
}

// Load time slots when date changes
dateInput.addEventListener('change', (e) => {
    const selectedDate = new Date(e.target.value);
    loadTimeSlots(selectedDate, e.target.value);
});

// Also reload time slots when service changes (duration affects availability)
const serviceSelect = document.querySelector('select[name="service"]');
if (serviceSelect) {
    serviceSelect.addEventListener('change', () => {
        const dateValue = dateInput.value;
        if (dateValue) {
            const selectedDate = new Date(dateValue);
            loadTimeSlots(selectedDate, dateValue);
        }
    });
}

// Load available time slots from API
async function loadTimeSlots(date, dateStr) {
    timeSlotsContainer.innerHTML = '<div class="loading">טוען זמנים פנויים...</div>';

    // Check if business day
    if (!isBusinessDay(date)) {
        timeSlotsContainer.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--color-text-tertiary);">סגור ביום זה</p>';
        return;
    }

    // Check if date is in the past
    const todayDate = new Date();
    todayDate.setHours(0, 0, 0, 0);
    if (date < todayDate) {
        timeSlotsContainer.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--color-text-tertiary);">לא ניתן להזמין לתאריך שעבר</p>';
        return;
    }

    // Get selected service to check availability based on duration
    const serviceSelect = document.querySelector('select[name="service"]');
    const selectedService = serviceSelect ? serviceSelect.value : '';
    const serviceInfo = CONFIG.SERVICES[selectedService];
    const serviceParam = serviceInfo ? encodeURIComponent(serviceInfo.nameEn) : '';

    try {
        // Fetch available slots from API (pass service for duration-based filtering)
        let url = `${CONFIG.API_BASE}/api/available-slots?date=${dateStr}`;
        if (serviceParam) {
            url += `&service=${serviceParam}`;
        }
        const response = await fetch(url);
        const data = await response.json();

        if (data.message) {
            timeSlotsContainer.innerHTML = `<p style="grid-column: 1/-1; text-align: center; color: var(--color-text-tertiary);">${data.message}</p>`;
            return;
        }

        const availableSlots = data.slots || [];

        // Filter out past times if date is today
        const now = new Date();
        const filteredSlots = availableSlots.filter(slot => {
            if (date.toDateString() === now.toDateString()) {
                const [hours, minutes] = slot.split(':').map(Number);
                const slotTime = new Date(date);
                slotTime.setHours(hours, minutes, 0, 0);
                return slotTime > now;
            }
            return true;
        });

        if (filteredSlots.length === 0) {
            timeSlotsContainer.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--color-text-tertiary);">אין תורים פנויים ביום זה</p>';
            return;
        }

        timeSlotsContainer.innerHTML = '';

        filteredSlots.forEach(slot => {
            const timeSlot = document.createElement('div');
            timeSlot.className = 'time-slot';
            timeSlot.textContent = slot;
            timeSlot.dataset.time = slot;

            timeSlot.addEventListener('click', () => {
                document.querySelectorAll('.time-slot').forEach(s => s.classList.remove('selected'));
                timeSlot.classList.add('selected');
            });

            timeSlotsContainer.appendChild(timeSlot);
        });

    } catch (error) {
        console.error('Error loading time slots:', error);
        timeSlotsContainer.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--color-text-tertiary);">שגיאה בטעינת זמנים. נסי שוב.</p>';
    }
}

// ============== BOOKING FORM ==============

let isBookingSubmitting = false;

function validateBookingData(data) {
    const errors = [];

    if (!data.name || data.name.trim().length < 2) {
        errors.push('נא להזין שם מלא');
    }

    const phoneClean = (data.phone || '').replace(/[-\s]/g, '');
    if (!phoneClean || !/^0(5[0-9]|[2-4]|[8-9])\d{7}$/.test(phoneClean)) {
        errors.push('נא להזין מספר טלפון תקין');
    }

    if (!data.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) {
        errors.push('נא להזין כתובת אימייל תקינה');
    }

    if (!data.service) {
        errors.push('נא לבחור שירות');
    }

    if (!data.date) {
        errors.push('נא לבחור תאריך');
    }

    if (!data.time) {
        errors.push('נא לבחור שעה');
    }

    return errors;
}

bookingForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    if (isBookingSubmitting) return;

    const selectedTimeSlot = document.querySelector('.time-slot.selected');
    if (!selectedTimeSlot) {
        alert('נא לבחור שעה');
        return;
    }

    const identity = UserIdentity.get();
    if (!identity) {
        UserIdentity.showOverlay();
        return;
    }

    const formData = new FormData(bookingForm);
    const serviceKey = formData.get('service');
    const serviceInfo = CONFIG.SERVICES[serviceKey];

    const bookingData = {
        name: identity.name,
        phone: identity.phone,
        email: identity.email,
        service: serviceInfo ? serviceInfo.nameEn : serviceKey,
        date: formData.get('date'),
        time: selectedTimeSlot.dataset.time,
        notes: formData.get('notes') || ''
    };

    const errors = validateBookingData(bookingData);
    if (errors.length > 0) {
        alert(errors.join('\n'));
        return;
    }

    // Check if user already has a future appointment
    const restrictionMsg = document.getElementById('bookingRestrictionMsg');
    if (restrictionMsg) restrictionMsg.style.display = 'none';

    const existingApt = await MyAppointments.checkBookingRestriction(identity.phone);
    if (existingApt) {
        if (restrictionMsg) {
            restrictionMsg.textContent =
                'כבר יש לך תור בתאריך ' + existingApt.date +
                ' בשעה ' + existingApt.time +
                '. ניתן להזמין תור חדש רק לאחר שהתור הקיים יעבור.';
            restrictionMsg.style.display = '';
        }
        return;
    }

    isBookingSubmitting = true;
    const submitBtn = bookingForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> שולח...';
    submitBtn.disabled = true;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000);

    try {
        const response = await fetch(`${CONFIG.API_BASE}/api/book`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(bookingData),
            signal: controller.signal
        });

        clearTimeout(timeoutId);
        const result = await response.json();

        if (response.ok && result.success) {
            showModal({ ...bookingData, serviceKey: serviceKey });
            bookingForm.reset();
            timeSlotsContainer.innerHTML = '<p style="grid-column: 1/-1; text-align: center; color: var(--color-text-tertiary);">בחרי תאריך קודם</p>';
        } else {
            alert(result.error || 'אירעה שגיאה. נסי שוב.');
        }

    } catch (error) {
        clearTimeout(timeoutId);
        console.error('Booking error:', error);
        if (error.name === 'AbortError') {
            alert('הבקשה נמשכה זמן רב מדי. נא לנסות שוב.');
        } else {
            alert('אירעה שגיאה בשליחת הטופס. נסי שוב או התקשרי אלינו.');
        }
    } finally {
        isBookingSubmitting = false;
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
});

// ============== CONTACT FORM ==============

contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const identity = UserIdentity.get();
    if (!identity) {
        UserIdentity.showOverlay();
        return;
    }

    const formData = new FormData(contactForm);
    const contactData = {
        name: identity.name,
        phone: identity.phone,
        message: formData.get('message')
    };

    // Validate
    if (!contactData.message) {
        alert('נא לכתוב הודעה');
        return;
    }

    // Show loading
    const submitBtn = contactForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> שולח...';
    submitBtn.disabled = true;

    try {
        // Send to API
        const response = await fetch(`${CONFIG.API_BASE}/api/contact`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(contactData)
        });

        const result = await response.json();

        if (response.ok && result.success) {
            alert(result.message || 'ההודעה נשלחה בהצלחה! אחזור אלייך בהקדם.');
            contactForm.reset();
        } else {
            alert(result.error || 'אירעה שגיאה. נסי שוב.');
        }

    } catch (error) {
        console.error('Contact error:', error);
        alert('אירעה שגיאה. נסי שוב.');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
});

// ============== WHATSAPP ==============

const BUSINESS_PHONE = '972515656295';

function generateWhatsAppLink(booking) {
    const daysHebrew = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];
    const dateObj = new Date(booking.date);
    const dayName = daysHebrew[dateObj.getDay()];
    const formattedDate = `יום ${dayName}, ${dateObj.toLocaleDateString('he-IL')}`;

    const serviceInfo = CONFIG.SERVICES[booking.serviceKey];
    const serviceName = serviceInfo ? serviceInfo.name : booking.service;

    const message = `היי! נקבע לי תור אצל לישי סימני 💅
שירות: ${serviceName}
תאריך: ${formattedDate}
שעה: ${booking.time}
שם: ${booking.name}
תודה! 💖`;

    return `https://wa.me/${BUSINESS_PHONE}?text=${encodeURIComponent(message)}`;
}

// ============== MODAL ==============

function showModal(booking) {
    if (booking) {
        const serviceInfo = CONFIG.SERVICES[booking.serviceKey];
        const serviceName = serviceInfo ? serviceInfo.name : booking.service;

        const detailsEl = document.getElementById('modalBookingDetails');
        if (detailsEl) {
            const dateObj = new Date(booking.date);
            const daysHebrew = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת'];
            const dayName = daysHebrew[dateObj.getDay()];
            const formattedDate = `יום ${dayName}, ${dateObj.toLocaleDateString('he-IL')}`;

            detailsEl.innerHTML =
                `<p><strong>${serviceName}</strong></p>` +
                `<p>${formattedDate} | ${booking.time}</p>`;
        }

        // WhatsApp confirmation is sent automatically from the backend
    }

    successModal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeModal() {
    successModal.classList.remove('active');
    document.body.style.overflow = '';
}

// Close modal on overlay click
successModal.addEventListener('click', (e) => {
    if (e.target === successModal) {
        closeModal();
    }
});

// Close modal on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && successModal.classList.contains('active')) {
        closeModal();
    }
});

// ============== SCROLL ANIMATIONS ==============

const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, observerOptions);

document.querySelectorAll('.fade-in').forEach(el => {
    observer.observe(el);
});

// ============== SMOOTH SCROLL ==============

document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            const navHeight = navbar.offsetHeight;
            const targetPosition = target.offsetTop - navHeight;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// ============== INITIALIZE ==============

// ============== MY APPOINTMENTS ==============

const MyAppointments = {

    async fetchAppointments(phone) {
        const p = phone.trim().replace(/[-\s]/g, '');
        const response = await fetch(
            `${CONFIG.API_BASE}/api/my-appointments?phone=${encodeURIComponent(p)}`
        );
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || 'Failed to fetch appointments');
        }
        return response.json();
    },

    showPhoneForm() {
        document.getElementById('aptPhoneForm').style.display = '';
        document.getElementById('aptLoading').style.display = 'none';
        document.getElementById('aptResults').style.display = 'none';
        document.getElementById('aptEmpty').style.display = 'none';
    },

    showLoading() {
        document.getElementById('aptPhoneForm').style.display = 'none';
        document.getElementById('aptLoading').style.display = '';
        document.getElementById('aptResults').style.display = 'none';
        document.getElementById('aptEmpty').style.display = 'none';
    },

    showResults(phone, appointments) {
        document.getElementById('aptPhoneForm').style.display = 'none';
        document.getElementById('aptLoading').style.display = 'none';
        document.getElementById('aptResults').style.display = '';
        document.getElementById('aptEmpty').style.display = 'none';

        document.getElementById('aptUserPhone').textContent = phone;

        const container = document.getElementById('aptCardsList');
        container.innerHTML = '';

        appointments.forEach(function(apt) {
            const card = document.createElement('div');
            card.className = 'apt-card fade-in visible';
            card.innerHTML =
                '<div class="apt-card-service">' + apt.service + '</div>' +
                '<div class="apt-card-datetime">' +
                    '<i class="fas fa-calendar" style="color: var(--color-gold); margin-left: 8px;"></i>' +
                    apt.date + ' | ' + apt.time +
                '</div>' +
                '<div class="apt-card-day">יום ' + apt.day_name + '</div>';
            container.appendChild(card);
        });
    },

    showEmpty(phone) {
        document.getElementById('aptPhoneForm').style.display = 'none';
        document.getElementById('aptLoading').style.display = 'none';
        document.getElementById('aptResults').style.display = 'none';
        document.getElementById('aptEmpty').style.display = '';

        document.getElementById('aptEmptyPhone').textContent = phone;
    },

    showPhoneError(message) {
        const el = document.getElementById('aptPhoneError');
        el.textContent = message;
        el.style.display = '';
    },

    hidePhoneError() {
        document.getElementById('aptPhoneError').style.display = 'none';
    },

    async lookupPhone(phone) {
        if (!phone || phone.replace(/[-\s]/g, '').length < 9) {
            this.showPhoneError('נא להזין מספר טלפון תקין');
            return;
        }

        this.hidePhoneError();
        this.storeUserIdentity(phone);
        this.showLoading();

        try {
            const data = await this.fetchAppointments(phone);

            if (data.appointments && data.appointments.length > 0) {
                this.showResults(phone, data.appointments);
                this.updateHomeBubble(data.appointments[0]);
            } else {
                this.showEmpty(phone);
                this.hideHomeBubble();
            }
        } catch (err) {
            console.error('My appointments error:', err);
            this.showPhoneForm();
            this.showPhoneError('שגיאה בחיפוש. נסי שוב.');
        }
    },

    reset() {
        this.showPhoneForm();
        this.hideHomeBubble();
        const input = document.getElementById('aptPhoneInput');
        if (input) input.value = '';
    },

    updateHomeBubble(appointment) {
        const bubble = document.getElementById('homeAppointmentBubble');
        if (!bubble || !appointment) return;

        bubble.style.display = '';
        bubble.innerHTML =
            '<a href="#my-appointments" class="apt-bubble-inner">' +
                '<i class="fas fa-calendar-check"></i>' +
                '<span>יש לך תור ב-' + appointment.date + ' בשעה ' + appointment.time + '</span>' +
            '</a>';
    },

    hideHomeBubble() {
        const bubble = document.getElementById('homeAppointmentBubble');
        if (bubble) {
            bubble.style.display = 'none';
            bubble.innerHTML = '';
        }
    },

    async checkBookingRestriction(phone) {
        if (!phone) return null;
        try {
            const data = await this.fetchAppointments(phone);
            if (data.appointments && data.appointments.length > 0) {
                return data.appointments[0];
            }
        } catch (e) {
            console.error('Booking restriction check error:', e);
        }
        return null;
    },

    init() {
        const phoneInput = document.getElementById('aptPhoneInput');
        const phoneSubmit = document.getElementById('aptPhoneSubmit');

        if (phoneSubmit) {
            phoneSubmit.addEventListener('click', () => {
                this.lookupPhone(phoneInput.value);
            });
        }

        if (phoneInput) {
            phoneInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.lookupPhone(phoneInput.value);
                }
            });
        }

        const resetBtn = document.getElementById('aptResetBtn');
        const emptyResetBtn = document.getElementById('aptEmptyResetBtn');

        if (resetBtn) resetBtn.addEventListener('click', () => this.reset());
        if (emptyResetBtn) emptyResetBtn.addEventListener('click', () => this.reset());

        // Auto-lookup if identity exists
        const identity = UserIdentity.get();
        if (identity) {
            if (phoneInput) phoneInput.value = identity.phone;
            this.lookupPhone(identity.phone);
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    console.log('LISHAI SIMANI Beauty Studio - Website Loaded');

    // Add visible class to hero elements
    document.querySelectorAll('.hero .fade-in').forEach(el => {
        el.classList.add('visible');
    });

    // Initialize identity system
    UserIdentity.init();

    // Initialize My Appointments
    MyAppointments.init();
});

// Make closeModal available globally
window.closeModal = closeModal;

// ============== SERVICE CARD AUTO-SELECT ==============

document.querySelectorAll('.service-card[data-service]').forEach(card => {
    card.addEventListener('click', () => {
        const serviceKey = card.dataset.service;
        const select = document.querySelector('select[name="service"]');
        if (select && serviceKey) {
            select.value = serviceKey;
            select.dispatchEvent(new Event('change'));
        }
    });
});

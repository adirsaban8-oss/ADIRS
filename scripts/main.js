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

// ============== PHONE UTILITIES ==============
// Centralized phone normalization to E.164 format (+972XXXXXXXXX)
// Ensures all phone numbers sent to backend are in correct format for Twilio

const PhoneUtils = {
    /**
     * Normalize any Israeli phone number to E.164 format (+972XXXXXXXXX).
     *
     * Accepts:
     *   - 0501234567      -> +972501234567
     *   - 050-123-4567    -> +972501234567
     *   - 050 123 4567    -> +972501234567
     *   - 972501234567    -> +972501234567
     *   - +972501234567   -> +972501234567
     *   - +972-50-123-4567 -> +972501234567
     *
     * @param {string} phone - Phone number in any format
     * @returns {string|null} - Phone in +972XXXXXXXXX format, or null if invalid
     */
    normalize(phone) {
        if (!phone) return null;

        // Remove all non-digit characters except leading +
        let clean = String(phone).replace(/[^\d+]/g, '');

        // Remove leading + for processing
        if (clean.startsWith('+')) {
            clean = clean.substring(1);
        }

        // Case 1: Already has 972 prefix (12 digits)
        if (clean.startsWith('972')) {
            if (clean.length === 12) {
                return '+' + clean;
            }
            return null;
        }

        // Case 2: Israeli local format (starts with 0, 10 digits)
        if (clean.startsWith('0') && clean.length === 10) {
            return '+972' + clean.substring(1);
        }

        // Case 3: Israeli format without leading 0 (9 digits, starts with 5)
        if (clean.startsWith('5') && clean.length === 9) {
            return '+972' + clean;
        }

        return null;
    },

    /**
     * Check if a phone number is a valid Israeli mobile number.
     * Israeli mobile prefixes: 050, 051, 052, 053, 054, 055, 058
     *
     * @param {string} phone - Phone number in any format
     * @returns {boolean} - True if valid Israeli mobile number
     */
    isValid(phone) {
        const normalized = this.normalize(phone);
        if (!normalized) return false;

        // Check Israeli mobile prefixes (after +972)
        const prefix = normalized.substring(4, 6);
        const mobilePrefixes = ['50', '51', '52', '53', '54', '55', '58'];
        return mobilePrefixes.includes(prefix);
    },

    /**
     * Format phone for local Israeli display: 050-123-4567
     *
     * @param {string} phone - Phone in any format
     * @returns {string} - Formatted for display
     */
    formatLocal(phone) {
        const normalized = this.normalize(phone);
        if (!normalized) return phone || '';

        const digits = normalized.substring(4); // Remove +972
        if (digits.length === 9) {
            return '0' + digits.substring(0, 2) + '-' + digits.substring(2, 5) + '-' + digits.substring(5);
        }
        return normalized;
    },

    /**
     * Get validation error message in Hebrew, or null if valid.
     *
     * @param {string} phone - Phone number to validate
     * @returns {string|null} - Error message in Hebrew, or null if valid
     */
    getValidationError(phone) {
        if (!phone || !phone.trim()) {
            return 'נא להזין מספר טלפון';
        }

        const normalized = this.normalize(phone);
        if (!normalized) {
            return 'מספר טלפון לא תקין. נא להזין מספר ישראלי (למשל 050-1234567)';
        }

        if (!this.isValid(phone)) {
            return 'נא להזין מספר טלפון נייד ישראלי תקין';
        }

        return null;
    }
};

// Make PhoneUtils available globally
window.PhoneUtils = PhoneUtils;

// ============== USER IDENTITY ==============

const UserIdentity = {
    KEYS: {
        name: 'lishai_user_name',
        phone: 'lishai_user_phone',
        email: 'lishai_user_email',
    },

    // State for OTP flow
    _pendingPhone: '',
    _pendingName: '',
    _pendingEmail: '',
    _isNewCustomer: false,
    _resendTimer: null,

    get() {
        const name = localStorage.getItem(this.KEYS.name) || '';
        const phone = localStorage.getItem(this.KEYS.phone) || '';
        const email = localStorage.getItem(this.KEYS.email) || '';
        if (name && phone && email) return { name, phone, email };
        return null;
    },

    save(name, phone, email) {
        // Always store phone in normalized +972 format
        const normalizedPhone = PhoneUtils.normalize(phone) || phone.trim();
        localStorage.setItem(this.KEYS.name, name.trim());
        localStorage.setItem(this.KEYS.phone, normalizedPhone);
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

    validatePhone(phone) {
        return PhoneUtils.getValidationError(phone);
    },

    /**
     * Normalize phone to E.164 format before storage/submission.
     */
    normalizePhone(phone) {
        return PhoneUtils.normalize(phone);
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

    // Step management
    showStep(step) {
        document.getElementById('idStep1').style.display = step === 1 ? '' : 'none';
        document.getElementById('idStep1b').style.display = step === '1b' ? '' : 'none';
        document.getElementById('idStep2').style.display = step === 2 ? '' : 'none';
    },

    showError(stepId, msg) {
        const el = document.getElementById(stepId);
        if (el) { el.textContent = msg; el.style.display = ''; }
    },

    hideError(stepId) {
        const el = document.getElementById(stepId);
        if (el) el.style.display = 'none';
    },

    setButtonLoading(btn, loading) {
        if (!btn) return;
        if (loading) {
            btn._origHTML = btn.innerHTML;
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> שולח...';
            btn.disabled = true;
        } else {
            btn.innerHTML = btn._origHTML || btn.innerHTML;
            btn.disabled = false;
        }
    },

    // OTP request for existing customer
    async requestOtpExisting(phone) {
        const err = this.validatePhone(phone);
        if (err) { this.showError('idStep1Error', err); return; }
        this.hideError('idStep1Error');

        // Normalize to +972 format before sending to backend
        const normalizedPhone = PhoneUtils.normalize(phone);
        if (!normalizedPhone) {
            this.showError('idStep1Error', 'מספר טלפון לא תקין');
            return;
        }

        const btn = document.getElementById('idSendOtpBtn');
        this.setButtonLoading(btn, true);

        try {
            const res = await fetch(CONFIG.API_BASE + '/api/otp/request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: normalizedPhone })
            });
            const data = await res.json();

            if (!res.ok) {
                this.showError('idStep1Error', data.error || 'שגיאה בשליחת הקוד');
                return;
            }

            this._pendingPhone = normalizedPhone;
            this._isNewCustomer = false;

            if (data.mock) {
                document.getElementById('idMockBanner').style.display = 'flex';
            }

            this.showStep(2);
            // Display user-friendly local format
            document.getElementById('idOtpPhone').textContent = PhoneUtils.formatLocal(normalizedPhone);
            this._initOtpBoxes();
            this._startResendTimer();

        } catch (e) {
            console.error('OTP request error:', e);
            this.showError('idStep1Error', 'שגיאה בשליחת הקוד. נסי שוב');
        } finally {
            this.setButtonLoading(btn, false);
        }
    },

    // OTP request for new customer
    async requestOtpNew(name, phone, email) {
        const errors = [];
        if (!name || name.trim().length < 2) errors.push('נא להזין שם מלא');
        const phoneErr = this.validatePhone(phone);
        if (phoneErr) errors.push(phoneErr);
        if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errors.push('נא להזין כתובת אימייל תקינה');

        if (errors.length > 0) {
            this.showError('idStep1bError', errors.join('. '));
            return;
        }
        this.hideError('idStep1bError');

        // Normalize to +972 format before sending to backend
        const normalizedPhone = PhoneUtils.normalize(phone);
        if (!normalizedPhone) {
            this.showError('idStep1bError', 'מספר טלפון לא תקין');
            return;
        }

        const btn = document.getElementById('idRegSendOtpBtn');
        this.setButtonLoading(btn, true);

        try {
            const res = await fetch(CONFIG.API_BASE + '/api/otp/request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: normalizedPhone })
            });
            const data = await res.json();

            if (!res.ok) {
                this.showError('idStep1bError', data.error || 'שגיאה בשליחת הקוד');
                return;
            }

            this._pendingPhone = normalizedPhone;
            this._pendingName = name;
            this._pendingEmail = email;
            this._isNewCustomer = true;

            if (data.mock) {
                document.getElementById('idMockBanner').style.display = 'flex';
            }

            this.showStep(2);
            // Display user-friendly local format
            document.getElementById('idOtpPhone').textContent = PhoneUtils.formatLocal(normalizedPhone);
            this._initOtpBoxes();
            this._startResendTimer();

        } catch (e) {
            console.error('OTP request error:', e);
            this.showError('idStep1bError', 'שגיאה בשליחת הקוד. נסי שוב');
        } finally {
            this.setButtonLoading(btn, false);
        }
    },

    // Verify OTP
    async verifyOtp(code) {
        this.hideError('idStep2Error');
        const btn = document.getElementById('idVerifyBtn');
        this.setButtonLoading(btn, true);

        try {
            const res = await fetch(CONFIG.API_BASE + '/api/otp/verify', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: this._pendingPhone, code: code })
            });
            const data = await res.json();

            if (!data.verified) {
                this.showError('idStep2Error', data.error || 'קוד שגוי');
                // Clear OTP boxes
                document.querySelectorAll('.otp-box').forEach(function(b) { b.value = ''; });
                document.querySelector('.otp-box').focus();
                btn.disabled = true;
                return;
            }

            // OTP verified! Now get user details
            if (this._isNewCustomer) {
                // New customer — use the registration data
                this.save(this._pendingName, this._pendingPhone, this._pendingEmail);
            } else {
                // Existing customer — lookup from Calendar
                try {
                    const lookupRes = await fetch(
                        CONFIG.API_BASE + '/api/user/lookup?phone=' + encodeURIComponent(this._pendingPhone)
                    );
                    const lookupData = await lookupRes.json();

                    if (lookupData.found && lookupData.name && lookupData.email) {
                        this.save(lookupData.name, this._pendingPhone, lookupData.email);
                    } else {
                        // Not found in Calendar — switch to registration
                        this._isNewCustomer = true;
                        document.getElementById('idRegPhone').value = this._pendingPhone;
                        this.showStep('1b');
                        this.showError('idStep1bError', 'לא מצאנו תורים קודמים. מלאי את הפרטים שלך');
                        return;
                    }
                } catch (e) {
                    console.error('User lookup error:', e);
                    // Fallback to registration
                    document.getElementById('idRegPhone').value = this._pendingPhone;
                    this.showStep('1b');
                    return;
                }
            }

            // Done — hide overlay
            this.hideOverlay();
            this.showResetBtn();
            if (this._resendTimer) clearInterval(this._resendTimer);

            // Trigger My Appointments auto-lookup
            MyAppointments.lookupPhone(this._pendingPhone);

        } catch (e) {
            console.error('OTP verify error:', e);
            this.showError('idStep2Error', 'שגיאה באימות. נסי שוב');
        } finally {
            this.setButtonLoading(btn, false);
        }
    },

    // Resend OTP
    async resendOtp() {
        try {
            const res = await fetch(CONFIG.API_BASE + '/api/otp/request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ phone: this._pendingPhone })
            });
            const data = await res.json();

            if (!res.ok) {
                this.showError('idStep2Error', data.error || 'שגיאה בשליחה חוזרת');
                return;
            }

            this.hideError('idStep2Error');
            document.querySelectorAll('.otp-box').forEach(function(b) { b.value = ''; });
            document.querySelector('.otp-box').focus();
            this._startResendTimer();
        } catch (e) {
            this.showError('idStep2Error', 'שגיאה בשליחה חוזרת');
        }
    },

    // OTP box behavior
    _initOtpBoxes() {
        const boxes = document.querySelectorAll('.otp-box');
        const self = this;

        boxes.forEach(function(box, i) {
            box.value = '';
            box.classList.remove('filled');

            box.addEventListener('input', function() {
                const val = this.value.replace(/\D/g, '');
                this.value = val.slice(0, 1);

                if (val && i < boxes.length - 1) {
                    boxes[i + 1].focus();
                }

                this.classList.toggle('filled', !!val);

                // Check if all filled
                let code = '';
                boxes.forEach(function(b) { code += b.value; });
                document.getElementById('idVerifyBtn').disabled = code.length < 6;

                // Auto-submit when complete
                if (code.length === 6) {
                    self.verifyOtp(code);
                }
            });

            box.addEventListener('keydown', function(e) {
                if (e.key === 'Backspace' && !this.value && i > 0) {
                    boxes[i - 1].focus();
                    boxes[i - 1].value = '';
                    boxes[i - 1].classList.remove('filled');
                }
            });

            box.addEventListener('paste', function(e) {
                e.preventDefault();
                const pasted = (e.clipboardData || window.clipboardData).getData('text').replace(/\D/g, '');
                for (let j = 0; j < Math.min(pasted.length, boxes.length); j++) {
                    boxes[j].value = pasted[j];
                    boxes[j].classList.add('filled');
                }
                const focusIdx = Math.min(pasted.length, boxes.length - 1);
                boxes[focusIdx].focus();

                if (pasted.length >= 6) {
                    document.getElementById('idVerifyBtn').disabled = false;
                    self.verifyOtp(pasted.slice(0, 6));
                }
            });
        });

        boxes[0].focus();
    },

    _startResendTimer() {
        const timerEl = document.getElementById('otpResendTimer');
        const resendBtn = document.getElementById('otpResendBtn');
        const countdownEl = document.getElementById('otpCountdown');
        let seconds = 60;

        timerEl.style.display = '';
        resendBtn.style.display = 'none';
        countdownEl.textContent = seconds;

        if (this._resendTimer) clearInterval(this._resendTimer);

        const self = this;
        this._resendTimer = setInterval(function() {
            seconds--;
            countdownEl.textContent = seconds;
            if (seconds <= 0) {
                clearInterval(self._resendTimer);
                timerEl.style.display = 'none';
                resendBtn.style.display = '';
            }
        }, 1000);
    },

    init() {
        if (this.exists()) {
            this.hideOverlay();
            this.showResetBtn();
            return;
        }

        this.showOverlay();
        this.showStep(1);

        const self = this;

        // Step 1: Existing customer — phone form
        document.getElementById('idPhoneForm').addEventListener('submit', function(e) {
            e.preventDefault();
            self.requestOtpExisting(document.getElementById('idPhone').value);
        });

        // Step 1b: New customer — registration form
        document.getElementById('idRegisterForm').addEventListener('submit', function(e) {
            e.preventDefault();
            self.requestOtpNew(
                document.getElementById('idRegName').value,
                document.getElementById('idRegPhone').value,
                document.getElementById('idRegEmail').value
            );
        });

        // Toggle between existing/new customer
        document.getElementById('idNewCustomerLink').addEventListener('click', function() {
            self.showStep('1b');
        });
        document.getElementById('idExistingCustomerLink').addEventListener('click', function() {
            self.showStep(1);
        });

        // Back from OTP
        document.getElementById('idBackToPhone').addEventListener('click', function() {
            if (self._resendTimer) clearInterval(self._resendTimer);
            self.showStep(self._isNewCustomer ? '1b' : 1);
            document.getElementById('idMockBanner').style.display = 'none';
        });

        // Verify button
        document.getElementById('idVerifyBtn').addEventListener('click', function() {
            let code = '';
            document.querySelectorAll('.otp-box').forEach(function(b) { code += b.value; });
            if (code.length === 6) self.verifyOtp(code);
        });

        // Resend
        document.getElementById('otpResendBtn').addEventListener('click', function() {
            self.resendOtp();
        });
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
                `<p>${formattedDate} | ${booking.time}</p>` +
                `<div style="margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid rgba(196, 163, 90, 0.2);">` +
                    `<p style="color: var(--color-text-secondary); font-size: 0.9rem; margin-bottom: 0.75rem;">הגעה לסטודיו:</p>` +
                    `<a href="waze://?q=${encodeURIComponent(BUSINESS_ADDRESS)}" ` +
                       `onclick="event.preventDefault(); window.location.href='waze://?q=${encodeURIComponent(BUSINESS_ADDRESS)}'; ` +
                       `setTimeout(function(){ window.location.href='https://www.waze.com/ul?q=${encodeURIComponent(BUSINESS_ADDRESS)}'; }, 500);" ` +
                       `class="btn btn-outline" style="display: inline-flex; align-items: center; gap: 8px; font-size: 0.95rem;">` +
                        `<i class="fas fa-route"></i> נווט עם Waze` +
                    `</a>` +
                `</div>`;
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
        // Normalize to +972 format for backend
        const normalizedPhone = PhoneUtils.normalize(phone) || phone.trim().replace(/[-\s]/g, '');
        const response = await fetch(
            `${CONFIG.API_BASE}/api/my-appointments?phone=${encodeURIComponent(normalizedPhone)}`
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
        // Validate phone using PhoneUtils
        const validationError = PhoneUtils.getValidationError(phone);
        if (validationError) {
            this.showPhoneError(validationError);
            return;
        }

        // Normalize to +972 format
        const normalizedPhone = PhoneUtils.normalize(phone);
        if (!normalizedPhone) {
            this.showPhoneError('מספר טלפון לא תקין');
            return;
        }

        this.hidePhoneError();
        this.storeUserIdentity(normalizedPhone);
        this.showLoading();

        try {
            const data = await this.fetchAppointments(normalizedPhone);
            const displayPhone = PhoneUtils.formatLocal(normalizedPhone);

            if (data.appointments && data.appointments.length > 0) {
                this.showResults(displayPhone, data.appointments);
                this.updateHomeBubble(data.appointments[0]);
            } else {
                this.showEmpty(displayPhone);
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
            // Display in user-friendly local format
            if (phoneInput) phoneInput.value = PhoneUtils.formatLocal(identity.phone);
            this.lookupPhone(identity.phone);
        }
    }
};

// ============== HOME PERSONALIZATION ==============

function initializeHomeGreeting() {
    const identity = UserIdentity.get();
    if (!identity || !identity.name) return;

    // Find hero title and add greeting
    const heroContent = document.querySelector('.hero-content');
    if (!heroContent) return;

    // Check if greeting already exists
    if (document.getElementById('personalizedGreeting')) return;

    // Create greeting element
    const greetingDiv = document.createElement('div');
    greetingDiv.id = 'personalizedGreeting';
    greetingDiv.style.cssText = `
        margin-bottom: 1.5rem;
        text-align: center;
        color: var(--color-gold);
        font-size: 1.3rem;
        font-family: var(--font-hebrew-heading);
        font-weight: 300;
        letter-spacing: 0.05em;
        animation: fadeIn 0.8s ease-out;
    `;

    const firstName = identity.name.split(' ')[0];
    greetingDiv.textContent = `שלום, ${firstName}! 👋`;

    // Insert after hero-badge
    const heroBadge = heroContent.querySelector('.hero-badge');
    if (heroBadge && heroBadge.nextSibling) {
        heroContent.insertBefore(greetingDiv, heroBadge.nextSibling);
    } else {
        heroContent.insertBefore(greetingDiv, heroContent.firstChild);
    }
}

// ============== WAZE NAVIGATION ==============

const BUSINESS_ADDRESS = 'משעול הרקפת 3 קרני שומרון';

function addWazeButton(containerElement) {
    if (!containerElement) return;

    // Check if Waze button already exists
    if (containerElement.querySelector('.waze-button')) return;

    const wazeBtn = document.createElement('a');
    wazeBtn.className = 'waze-button btn btn-outline btn-lg';
    wazeBtn.style.cssText = `
        display: inline-flex;
        align-items: center;
        gap: 10px;
        margin-top: 1rem;
    `;

    wazeBtn.href = `waze://?q=${encodeURIComponent(BUSINESS_ADDRESS)}`;

    // Deep link with fallback to Waze web
    wazeBtn.onclick = function(e) {
        e.preventDefault();
        window.location.href = `waze://?q=${encodeURIComponent(BUSINESS_ADDRESS)}`;
        setTimeout(() => {
            window.location.href = `https://www.waze.com/ul?q=${encodeURIComponent(BUSINESS_ADDRESS)}`;
        }, 500);
    };

    wazeBtn.innerHTML = '<i class="fas fa-route"></i> נווט עם Waze';
    containerElement.appendChild(wazeBtn);
}

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

    // Initialize Home Personalization
    initializeHomeGreeting();
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

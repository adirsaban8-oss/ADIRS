/* ========================================
   LISHAI SIMANI - Luxury Nail Studio
   Main JavaScript
   ======================================== */

// ============== PHONE UTILITIES ==============
// Centralized phone normalization to E.164 format (+972XXXXXXXXX)

const PhoneUtils = {
    /**
     * Normalize any Israeli phone number to E.164 format (+972XXXXXXXXX).
     */
    normalize(phone) {
        if (!phone) return null;
        let clean = String(phone).replace(/[^\d+]/g, '');
        if (clean.startsWith('+')) clean = clean.substring(1);

        if (clean.startsWith('972') && clean.length === 12) return '+' + clean;
        if (clean.startsWith('0') && clean.length === 10) return '+972' + clean.substring(1);
        if (clean.startsWith('5') && clean.length === 9) return '+972' + clean;

        return null;
    },

    /**
     * Check if a phone number is a valid Israeli mobile number.
     */
    isValid(phone) {
        const normalized = this.normalize(phone);
        if (!normalized) return false;
        const prefix = normalized.substring(4, 6);
        return ['50', '51', '52', '53', '54', '55', '58'].includes(prefix);
    },

    /**
     * Format phone for local Israeli display: 050-123-4567
     */
    formatLocal(phone) {
        const normalized = this.normalize(phone);
        if (!normalized) return phone || '';
        const digits = normalized.substring(4);
        if (digits.length === 9) {
            return '0' + digits.substring(0, 2) + '-' + digits.substring(2, 5) + '-' + digits.substring(5);
        }
        return normalized;
    },

    /**
     * Get validation error message in Hebrew, or null if valid.
     */
    getValidationError(phone) {
        if (!phone || !phone.trim()) return 'נא להזין מספר טלפון';
        if (!this.normalize(phone)) return 'מספר טלפון לא תקין. נא להזין מספר ישראלי';
        if (!this.isValid(phone)) return 'נא להזין מספר טלפון נייד ישראלי תקין';
        return null;
    }
};

window.PhoneUtils = PhoneUtils;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initNavbar();
    initMobileMenu();
    initSmoothScroll();
    initScrollAnimations();
    initBookingForm();
    initContactForm();
    initBackToTop();
    initDatePicker();
});

/* ========================================
   Navbar Scroll Effect
   ======================================== */
function initNavbar() {
    const navbar = document.getElementById('navbar');
    let lastScroll = 0;

    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;

        // Add/remove scrolled class
        if (currentScroll > 100) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        lastScroll = currentScroll;
    });

    // Set active nav link based on scroll position
    const sections = document.querySelectorAll('section[id]');
    const navLinks = document.querySelectorAll('.nav-link');

    window.addEventListener('scroll', () => {
        let current = '';

        sections.forEach(section => {
            const sectionTop = section.offsetTop - 150;
            const sectionHeight = section.offsetHeight;

            if (window.pageYOffset >= sectionTop && window.pageYOffset < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
}

/* ========================================
   Mobile Menu Toggle
   ======================================== */
function initMobileMenu() {
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    const navLinks = document.querySelectorAll('.nav-link');

    navToggle.addEventListener('click', () => {
        navToggle.classList.toggle('active');
        navMenu.classList.toggle('active');
        document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
    });

    // Close menu when clicking a link
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navToggle.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.style.overflow = '';
        });
    });

    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!navMenu.contains(e.target) && !navToggle.contains(e.target) && navMenu.classList.contains('active')) {
            navToggle.classList.remove('active');
            navMenu.classList.remove('active');
            document.body.style.overflow = '';
        }
    });
}

/* ========================================
   Smooth Scroll for Anchor Links
   ======================================== */
function initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);

            if (targetElement) {
                const navbarHeight = document.getElementById('navbar').offsetHeight;
                const targetPosition = targetElement.offsetTop - navbarHeight;

                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

/* ========================================
   Scroll Animations
   ======================================== */
function initScrollAnimations() {
    // Elements to animate
    const animateElements = document.querySelectorAll(
        '.section-header, .about-content, .service-card, .gallery-item, ' +
        '.policy-card, .info-card, .contact-item, .feature'
    );

    // Create intersection observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');

                // Add stagger effect for grid items
                if (entry.target.classList.contains('service-card') ||
                    entry.target.classList.contains('gallery-item') ||
                    entry.target.classList.contains('policy-card')) {
                    const siblings = entry.target.parentElement.children;
                    Array.from(siblings).forEach((sibling, index) => {
                        sibling.style.transitionDelay = `${index * 0.1}s`;
                    });
                }
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });

    // Add animate-on-scroll class and observe
    animateElements.forEach(element => {
        element.classList.add('animate-on-scroll');
        observer.observe(element);
    });
}

/* ========================================
   Date Picker Initialization
   ======================================== */
function initDatePicker() {
    const dateInput = document.getElementById('bookingDate');
    const timeSelect = document.getElementById('bookingTime');

    if (!dateInput || !timeSelect) return;

    // Set minimum date to today
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);
    dateInput.min = tomorrow.toISOString().split('T')[0];

    // Set maximum date to 60 days from now
    const maxDate = new Date(today);
    maxDate.setDate(maxDate.getDate() + 60);
    dateInput.max = maxDate.toISOString().split('T')[0];

    // Handle date change
    dateInput.addEventListener('change', async function() {
        const selectedDate = this.value;

        if (!selectedDate) {
            timeSelect.disabled = true;
            timeSelect.innerHTML = '<option value="">בחרי תאריך קודם</option>';
            return;
        }

        // Check if it's Friday or Saturday
        const date = new Date(selectedDate);
        const dayOfWeek = date.getDay();

        if (dayOfWeek === 5 || dayOfWeek === 6) {
            timeSelect.disabled = true;
            timeSelect.innerHTML = '<option value="">סגור בימי שישי ושבת</option>';
            showNotification('הסטודיו סגור בימי שישי ושבת', 'warning');
            return;
        }

        // Fetch available time slots
        try {
            timeSelect.disabled = true;
            timeSelect.innerHTML = '<option value="">טוען שעות...</option>';

            const response = await fetch(`/api/available-slots?date=${selectedDate}`);
            const data = await response.json();

            if (data.slots && data.slots.length > 0) {
                timeSelect.disabled = false;
                timeSelect.innerHTML = '<option value="">בחרי שעה...</option>';
                data.slots.forEach(slot => {
                    const option = document.createElement('option');
                    option.value = slot;
                    option.textContent = slot;
                    timeSelect.appendChild(option);
                });
            } else {
                timeSelect.innerHTML = '<option value="">אין שעות פנויות</option>';
            }
        } catch (error) {
            console.error('Error fetching time slots:', error);
            timeSelect.innerHTML = '<option value="">שגיאה בטעינת שעות</option>';
        }
    });
}

/* ========================================
   Booking Form Handler
   ======================================== */
function initBookingForm() {
    const form = document.getElementById('bookingForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;

        // Validate form
        if (!validateForm(form)) {
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> שולח...';

        // Collect form data with phone normalization
        const rawPhone = form.querySelector('#bookingPhone').value;
        const normalizedPhone = PhoneUtils.normalize(rawPhone);

        // Validate phone
        const phoneError = PhoneUtils.getValidationError(rawPhone);
        if (phoneError) {
            showNotification(phoneError, 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
            return;
        }

        const formData = {
            name: form.querySelector('#bookingName').value,
            phone: normalizedPhone,
            email: form.querySelector('#bookingEmail').value,
            service: form.querySelector('#bookingService').value,
            date: form.querySelector('#bookingDate').value,
            time: form.querySelector('#bookingTime').value,
            notes: form.querySelector('#bookingNotes').value
        };

        try {
            const response = await fetch('/api/book', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                showModal();
                form.reset();
                document.getElementById('bookingTime').disabled = true;
                document.getElementById('bookingTime').innerHTML = '<option value="">בחרי תאריך קודם</option>';
            } else {
                showNotification(data.error || 'שגיאה בשליחת הטופס', 'error');
            }
        } catch (error) {
            console.error('Error submitting booking:', error);
            showNotification('שגיאה בשליחת הטופס. נסי שוב מאוחר יותר.', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    });
}

/* ========================================
   Contact Form Handler
   ======================================== */
function initContactForm() {
    const form = document.getElementById('contactForm');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        const submitBtn = form.querySelector('button[type="submit"]');
        const originalBtnText = submitBtn.innerHTML;

        // Validate form
        if (!validateForm(form)) {
            return;
        }

        // Show loading state
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> שולח...';

        // Collect form data with phone normalization
        const rawPhone = form.querySelector('#contactPhone').value;
        const normalizedPhone = PhoneUtils.normalize(rawPhone);

        // Validate phone
        const phoneError = PhoneUtils.getValidationError(rawPhone);
        if (phoneError) {
            showNotification(phoneError, 'error');
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
            return;
        }

        const formData = {
            name: form.querySelector('#contactName').value,
            phone: normalizedPhone,
            message: form.querySelector('#contactMessage').value
        };

        try {
            const response = await fetch('/api/contact', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (data.success) {
                showNotification('ההודעה נשלחה בהצלחה!', 'success');
                form.reset();
            } else {
                showNotification(data.error || 'שגיאה בשליחת הטופס', 'error');
            }
        } catch (error) {
            console.error('Error submitting contact form:', error);
            showNotification('שגיאה בשליחת הטופס. נסי שוב מאוחר יותר.', 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        }
    });
}

/* ========================================
   Form Validation
   ======================================== */
function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;

    requiredFields.forEach(field => {
        removeFieldError(field);

        if (!field.value.trim()) {
            showFieldError(field, 'שדה חובה');
            isValid = false;
        } else if (field.type === 'tel' && !isValidPhone(field.value)) {
            showFieldError(field, 'מספר טלפון לא תקין');
            isValid = false;
        }
    });

    return isValid;
}

function isValidPhone(phone) {
    const phoneRegex = /^[\d\-+\s()]{9,15}$/;
    return phoneRegex.test(phone);
}

function showFieldError(field, message) {
    field.classList.add('error');
    const errorEl = document.createElement('span');
    errorEl.className = 'field-error';
    errorEl.textContent = message;
    errorEl.style.cssText = 'color: #dc3545; font-size: 0.8rem; display: block; margin-top: 5px;';
    field.parentNode.appendChild(errorEl);
}

function removeFieldError(field) {
    field.classList.remove('error');
    const existingError = field.parentNode.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

/* ========================================
   Back to Top Button
   ======================================== */
function initBackToTop() {
    const backToTopBtn = document.getElementById('backToTop');
    if (!backToTopBtn) return;

    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 500) {
            backToTopBtn.classList.add('visible');
        } else {
            backToTopBtn.classList.remove('visible');
        }
    });

    backToTopBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

/* ========================================
   Modal Functions
   ======================================== */
function showModal() {
    const modal = document.getElementById('successModal');
    if (modal) {
        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }
}

function closeModal() {
    const modal = document.getElementById('successModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}

// Close modal when clicking outside
document.addEventListener('click', (e) => {
    const modal = document.getElementById('successModal');
    if (modal && e.target === modal) {
        closeModal();
    }
});

// Close modal with Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal();
    }
});

/* ========================================
   Notification System
   ======================================== */
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotification = document.querySelector('.notification');
    if (existingNotification) {
        existingNotification.remove();
    }

    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${getNotificationIcon(type)}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    // Style the notification
    notification.style.cssText = `
        position: fixed;
        top: 100px;
        right: 20px;
        padding: 15px 20px;
        background: ${getNotificationColor(type)};
        color: white;
        border-radius: 0;
        box-shadow: 0 5px 25px rgba(0,0,0,0.15);
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 15px;
        z-index: 3000;
        animation: slideInRight 0.3s ease;
        max-width: 400px;
    `;

    // Add animation keyframes if not exists
    if (!document.querySelector('#notification-styles')) {
        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            @keyframes slideInRight {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }
            .notification-content {
                display: flex;
                align-items: center;
                gap: 10px;
            }
            .notification-close {
                background: none;
                border: none;
                color: white;
                cursor: pointer;
                padding: 5px;
                opacity: 0.8;
            }
            .notification-close:hover {
                opacity: 1;
            }
        `;
        document.head.appendChild(style);
    }

    document.body.appendChild(notification);

    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.style.animation = 'slideInRight 0.3s ease reverse';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

function getNotificationIcon(type) {
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-circle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    return icons[type] || icons.info;
}

function getNotificationColor(type) {
    const colors = {
        success: '#28a745',
        error: '#dc3545',
        warning: '#c9a961',
        info: '#17a2b8'
    };
    return colors[type] || colors.info;
}

/* ========================================
   Gallery Lightbox (Optional Enhancement)
   ======================================== */
function initGalleryLightbox() {
    const galleryItems = document.querySelectorAll('.gallery-item');

    galleryItems.forEach(item => {
        item.addEventListener('click', () => {
            // This can be expanded to show a lightbox with actual images
            // For now, it's a placeholder for future implementation
            console.log('Gallery item clicked - lightbox can be implemented here');
        });
    });
}

/* ========================================
   Service Card Hover Effects
   ======================================== */
document.addEventListener('DOMContentLoaded', () => {
    const serviceCards = document.querySelectorAll('.service-card');

    serviceCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px)';
        });

        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
});

/* ========================================
   Lazy Loading for Images
   ======================================== */
function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

/* ========================================
   Utility Functions
   ======================================== */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

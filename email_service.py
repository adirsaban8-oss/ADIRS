"""
Email Service Module for LISHAY Booking System
Handles sending booking confirmations and reminders
"""

import os
import sys
import logging
import smtplib
import socket
import traceback
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Configure logging for production (Railway)
# Force unbuffered output so logs appear immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [EMAIL_SERVICE] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Force stdout to be unbuffered for Railway
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)


def get_smtp_config():
    """
    Get SMTP configuration from environment variables.
    Fetches fresh values each time to handle runtime changes.
    """
    return {
        'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
        'port': int(os.getenv('SMTP_PORT', 587)),
        'email': os.getenv('SMTP_EMAIL', ''),
        'password': os.getenv('SMTP_PASSWORD', ''),
        'sender_name': os.getenv('SMTP_SENDER_NAME', 'Nexora Digital'),
    }


# Legacy variables for backward compatibility
SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SMTP_EMAIL = os.getenv('SMTP_EMAIL', '')
SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', '')
SMTP_SENDER_NAME = os.getenv('SMTP_SENDER_NAME', 'Nexora Digital')
BUSINESS_NAME = 'LISHAY SIMANI'
BUSINESS_PHONE = '051-5656295'
BUSINESS_ADDRESS = 'משעול הרקפת 3, קרני שומרון'


def get_email_template(booking_data, template_type='confirmation'):
    """
    Generate beautiful HTML email template.

    Args:
        booking_data: Dictionary with booking details
        template_type: 'confirmation', 'reminder_day_before', or 'reminder_morning'
    """

    # Format date nicely in Hebrew
    date_obj = datetime.strptime(booking_data['date'], '%Y-%m-%d')
    days_hebrew = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת']
    day_name = days_hebrew[date_obj.weekday()]
    formatted_date = f"יום {day_name}, {date_obj.strftime('%d/%m/%Y')}"

    # Set subject and intro based on template type
    if template_type == 'confirmation':
        subject = f'אישור תור - {BUSINESS_NAME}'
        intro_text = 'התור שלך אושר בהצלחה!'
        emoji = '✨'
    elif template_type == 'reminder_day_before':
        subject = f'תזכורת לתור מחר - {BUSINESS_NAME}'
        intro_text = 'רק להזכיר - יש לך תור מחר!'
        emoji = '💅'
    else:  # reminder_morning
        subject = f'תזכורת - התור שלך היום! - {BUSINESS_NAME}'
        intro_text = 'היום יש לך תור אצלנו!'
        emoji = '🌸'

    html_content = f'''
<!DOCTYPE html>
<html dir="rtl" lang="he">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin: 0; padding: 0; font-family: 'Heebo', Arial, sans-serif; background-color: #FBF6EE;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #FBF6EE; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #FFFCF5; border-radius: 20px; box-shadow: 0 8px 30px rgba(196, 163, 90, 0.15);">

                    <!-- Header -->
                    <tr>
                        <td style="padding: 40px 40px 30px; text-align: center; border-bottom: 1px solid rgba(196, 163, 90, 0.2);">
                            <h1 style="margin: 0; font-size: 32px; font-weight: 300; color: #C4A35A; letter-spacing: 8px; text-transform: uppercase;">
                                {BUSINESS_NAME}
                            </h1>
                            <p style="margin: 10px 0 0; font-size: 14px; color: #8A847C; letter-spacing: 2px;">
                                מניקוריסטית מקצועית
                            </p>
                        </td>
                    </tr>

                    <!-- Main Content -->
                    <tr>
                        <td style="padding: 40px;">
                            <div style="text-align: center; margin-bottom: 30px;">
                                <span style="font-size: 48px;">{emoji}</span>
                            </div>

                            <h2 style="margin: 0 0 10px; font-size: 24px; font-weight: 400; color: #1A1714; text-align: center;">
                                שלום {booking_data['name']},
                            </h2>

                            <p style="margin: 0 0 30px; font-size: 18px; color: #C4A35A; text-align: center; font-weight: 300;">
                                {intro_text}
                            </p>

                            <!-- Booking Details Card -->
                            <div style="background: linear-gradient(135deg, #F5EFE3 0%, #FBF6EE 100%); border-radius: 15px; padding: 30px; margin-bottom: 30px; border-right: 4px solid #C4A35A;">
                                <h3 style="margin: 0 0 20px; font-size: 16px; color: #C4A35A; font-weight: 500; letter-spacing: 1px;">
                                    פרטי התור
                                </h3>

                                <table width="100%" cellpadding="0" cellspacing="0">
                                    <tr>
                                        <td style="padding: 10px 0; border-bottom: 1px solid rgba(196, 163, 90, 0.15);">
                                            <span style="color: #8A847C; font-size: 14px;">טיפול:</span>
                                        </td>
                                        <td style="padding: 10px 0; border-bottom: 1px solid rgba(196, 163, 90, 0.15); text-align: left;">
                                            <span style="color: #1A1714; font-size: 16px; font-weight: 500;">{booking_data.get('service_he', booking_data['service'])}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0; border-bottom: 1px solid rgba(196, 163, 90, 0.15);">
                                            <span style="color: #8A847C; font-size: 14px;">תאריך:</span>
                                        </td>
                                        <td style="padding: 10px 0; border-bottom: 1px solid rgba(196, 163, 90, 0.15); text-align: left;">
                                            <span style="color: #1A1714; font-size: 16px; font-weight: 500;">{formatted_date}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0; border-bottom: 1px solid rgba(196, 163, 90, 0.15);">
                                            <span style="color: #8A847C; font-size: 14px;">שעה:</span>
                                        </td>
                                        <td style="padding: 10px 0; border-bottom: 1px solid rgba(196, 163, 90, 0.15); text-align: left;">
                                            <span style="color: #1A1714; font-size: 16px; font-weight: 500;">{booking_data['time']}</span>
                                        </td>
                                    </tr>
                                    <tr>
                                        <td style="padding: 10px 0;">
                                            <span style="color: #8A847C; font-size: 14px;">משך:</span>
                                        </td>
                                        <td style="padding: 10px 0; text-align: left;">
                                            <span style="color: #1A1714; font-size: 16px; font-weight: 500;">{booking_data.get('duration', 60)} דקות</span>
                                        </td>
                                    </tr>
                                </table>
                            </div>

                            <!-- Location -->
                            <div style="text-align: center; margin-bottom: 30px; padding: 20px; background-color: #FBF6EE; border-radius: 10px;">
                                <p style="margin: 0 0 5px; font-size: 14px; color: #8A847C;">
                                    📍 הכתובת שלנו
                                </p>
                                <p style="margin: 0; font-size: 16px; color: #1A1714;">
                                    {BUSINESS_ADDRESS}
                                </p>
                            </div>

                            <!-- Cancellation Policy -->
                            <div style="background-color: #FFF8E7; border-radius: 10px; padding: 20px; margin-bottom: 20px;">
                                <p style="margin: 0 0 10px; font-size: 14px; color: #C4A35A; font-weight: 500;">
                                    ⚠️ מדיניות ביטולים
                                </p>
                                <p style="margin: 0; font-size: 13px; color: #5C5650; line-height: 1.6;">
                                    ביטול באותו היום - 50% מעלות הטיפול<br>
                                    אי הגעה ללא הודעה - חיוב מלא<br>
                                    איחור מעל 15 דקות ללא הודעה - ייחשב כביטול
                                </p>
                            </div>

                            <!-- Contact -->
                            <p style="margin: 20px 0 0; font-size: 14px; color: #8A847C; text-align: center;">
                                שאלות? התקשרי אלינו: <a href="tel:{BUSINESS_PHONE}" style="color: #C4A35A; text-decoration: none;">{BUSINESS_PHONE}</a>
                            </p>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="padding: 30px 40px; background-color: #2C2620; border-radius: 0 0 20px 20px; text-align: center;">
                            <p style="margin: 0 0 10px; font-size: 18px; color: #C4A35A; letter-spacing: 4px; text-transform: uppercase;">
                                {BUSINESS_NAME}
                            </p>
                            <p style="margin: 0; font-size: 12px; color: rgba(255,255,255,0.5);">
                                יוקרה, מקצועיות ודיוק בכל ציפורן
                            </p>
                            <p style="margin: 15px 0 0; font-size: 11px; color: rgba(255,255,255,0.3);">
                                נשמח לראותך! 💕
                            </p>
                        </td>
                    </tr>

                </table>
            </td>
        </tr>
    </table>
</body>
</html>
'''

    return subject, html_content


def send_email(to_email, subject, html_content):
    """
    Send an email using SMTP.

    Args:
        to_email: Recipient email address
        subject: Email subject
        html_content: HTML content of the email

    Returns:
        True if sent successfully, False otherwise
    """
    # Get fresh SMTP config from environment
    smtp_config = get_smtp_config()
    smtp_email = smtp_config['email']
    smtp_password = smtp_config['password']
    smtp_server = smtp_config['server']
    smtp_port = smtp_config['port']
    smtp_sender_name = smtp_config['sender_name']

    logger.info("=" * 50)
    logger.info("EMAIL SEND ATTEMPT STARTED")
    logger.info(f"To: {to_email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"SMTP Server: {smtp_server}:{smtp_port}")
    logger.info(f"SMTP Email configured: {bool(smtp_email)} (value: {smtp_email[:3]}...{smtp_email[-10:] if len(smtp_email) > 13 else '***'})" if smtp_email else "SMTP Email: NOT SET")
    logger.info(f"SMTP Password configured: {bool(smtp_password)} (length: {len(smtp_password) if smtp_password else 0})")
    sys.stdout.flush()

    if not smtp_email or not smtp_password:
        logger.error("SMTP CREDENTIALS MISSING!")
        logger.error(f"  - SMTP_EMAIL is {'SET' if smtp_email else 'EMPTY/MISSING'}")
        logger.error(f"  - SMTP_PASSWORD is {'SET' if smtp_password else 'EMPTY/MISSING'}")
        logger.error("Please check Railway environment variables.")
        sys.stdout.flush()
        return False

    try:
        logger.info("Step 1: Building email message...")
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{smtp_sender_name} <{smtp_email}>'
        msg['To'] = to_email

        # Attach HTML content
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        logger.info("Step 1: Email message built successfully")
        sys.stdout.flush()

        logger.info(f"Step 2: Connecting to SMTP server {smtp_server}:{smtp_port}...")
        sys.stdout.flush()

        # Set socket timeout to prevent hanging
        socket.setdefaulttimeout(30)

        with smtplib.SMTP(smtp_server, smtp_port, timeout=30) as server:
            logger.info("Step 2: Connected to SMTP server")
            sys.stdout.flush()

            logger.info("Step 3: Starting TLS encryption...")
            server.starttls()
            logger.info("Step 3: TLS encryption enabled")
            sys.stdout.flush()

            logger.info("Step 4: Authenticating with SMTP server...")
            sys.stdout.flush()
            server.login(smtp_email, smtp_password)
            logger.info("Step 4: Authentication successful")
            sys.stdout.flush()

            logger.info("Step 5: Sending email...")
            sys.stdout.flush()
            server.send_message(msg)
            logger.info("Step 5: Email sent successfully")
            sys.stdout.flush()

        logger.info(f"SUCCESS: Email sent to {to_email}")
        logger.info("=" * 50)
        sys.stdout.flush()
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error("=" * 50)
        logger.error("SMTP AUTHENTICATION FAILED!")
        logger.error(f"Error code: {e.smtp_code if hasattr(e, 'smtp_code') else 'N/A'}")
        logger.error(f"Error message: {e.smtp_error if hasattr(e, 'smtp_error') else str(e)}")
        logger.error("Possible causes:")
        logger.error("  1. Wrong SMTP_EMAIL or SMTP_PASSWORD")
        logger.error("  2. Gmail: Need to use App Password, not regular password")
        logger.error("  3. Gmail: 2FA might be required with App Password")
        logger.error("  4. Account may be locked or require verification")
        logger.error(f"Full exception: {repr(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        sys.stdout.flush()
        return False

    except smtplib.SMTPConnectError as e:
        logger.error("=" * 50)
        logger.error("SMTP CONNECTION FAILED!")
        logger.error(f"Could not connect to {smtp_server}:{smtp_port}")
        logger.error(f"Error: {str(e)}")
        logger.error("Possible causes:")
        logger.error("  1. Wrong SMTP_SERVER or SMTP_PORT")
        logger.error("  2. Firewall blocking outbound SMTP")
        logger.error("  3. Railway may block port 587 (try port 465 with SSL)")
        logger.error(f"Full exception: {repr(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        sys.stdout.flush()
        return False

    except smtplib.SMTPRecipientsRefused as e:
        logger.error("=" * 50)
        logger.error("RECIPIENT REFUSED!")
        logger.error(f"The recipient {to_email} was rejected by the server")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Full exception: {repr(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        sys.stdout.flush()
        return False

    except smtplib.SMTPException as e:
        logger.error("=" * 50)
        logger.error("SMTP ERROR!")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Full exception: {repr(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        sys.stdout.flush()
        return False

    except socket.timeout as e:
        logger.error("=" * 50)
        logger.error("SMTP CONNECTION TIMEOUT!")
        logger.error(f"Connection to {smtp_server}:{smtp_port} timed out after 30 seconds")
        logger.error("Possible causes:")
        logger.error("  1. Network issues")
        logger.error("  2. SMTP server is down")
        logger.error("  3. Port might be blocked by Railway")
        logger.error(f"Full exception: {repr(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        sys.stdout.flush()
        return False

    except socket.gaierror as e:
        logger.error("=" * 50)
        logger.error("DNS RESOLUTION FAILED!")
        logger.error(f"Could not resolve hostname: {smtp_server}")
        logger.error(f"Error: {str(e)}")
        logger.error("Possible causes:")
        logger.error("  1. Wrong SMTP_SERVER value")
        logger.error("  2. Network/DNS issues")
        logger.error(f"Full exception: {repr(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        sys.stdout.flush()
        return False

    except Exception as e:
        logger.error("=" * 50)
        logger.error("UNEXPECTED EMAIL ERROR!")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error message: {str(e)}")
        logger.error(f"Full exception: {repr(e)}")
        logger.error("Traceback:")
        logger.error(traceback.format_exc())
        logger.error("=" * 50)
        sys.stdout.flush()
        return False


def send_booking_confirmation(booking_data):
    """
    Send booking confirmation email to customer.
    """
    logger.info("=" * 50)
    logger.info("BOOKING CONFIRMATION EMAIL TRIGGERED")
    logger.info(f"Customer: {booking_data.get('name', 'N/A')}")
    logger.info(f"Email: {booking_data.get('email', 'N/A')}")
    logger.info(f"Service: {booking_data.get('service_he', booking_data.get('service', 'N/A'))}")
    logger.info(f"Date: {booking_data.get('date', 'N/A')} at {booking_data.get('time', 'N/A')}")
    sys.stdout.flush()

    try:
        subject, html_content = get_email_template(booking_data, 'confirmation')
        result = send_email(booking_data['email'], subject, html_content)
        logger.info(f"BOOKING CONFIRMATION RESULT: {'SUCCESS' if result else 'FAILED'}")
        sys.stdout.flush()
        return result
    except Exception as e:
        logger.error(f"BOOKING CONFIRMATION EXCEPTION: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        sys.stdout.flush()
        raise


def send_reminder_day_before(booking_data):
    """
    Send reminder email one day before the appointment.
    """
    logger.info("DAY-BEFORE REMINDER EMAIL TRIGGERED")
    logger.info(f"Customer: {booking_data.get('name', 'N/A')} - {booking_data.get('email', 'N/A')}")
    sys.stdout.flush()

    try:
        subject, html_content = get_email_template(booking_data, 'reminder_day_before')
        result = send_email(booking_data['email'], subject, html_content)
        logger.info(f"DAY-BEFORE REMINDER RESULT: {'SUCCESS' if result else 'FAILED'}")
        sys.stdout.flush()
        return result
    except Exception as e:
        logger.error(f"DAY-BEFORE REMINDER EXCEPTION: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        sys.stdout.flush()
        raise


def send_reminder_morning(booking_data):
    """
    Send reminder email on the morning of the appointment.
    """
    logger.info("MORNING REMINDER EMAIL TRIGGERED")
    logger.info(f"Customer: {booking_data.get('name', 'N/A')} - {booking_data.get('email', 'N/A')}")
    sys.stdout.flush()

    try:
        subject, html_content = get_email_template(booking_data, 'reminder_morning')
        result = send_email(booking_data['email'], subject, html_content)
        logger.info(f"MORNING REMINDER RESULT: {'SUCCESS' if result else 'FAILED'}")
        sys.stdout.flush()
        return result
    except Exception as e:
        logger.error(f"MORNING REMINDER EXCEPTION: {type(e).__name__}: {str(e)}")
        logger.error(traceback.format_exc())
        sys.stdout.flush()
        raise


def get_reminders_to_send():
    """
    Get list of reminders that need to be sent.
    This should be called by a scheduler (e.g., APScheduler, cron job).

    Returns bookings that need:
    - Day before reminder (at 20:00)
    - Morning reminder (at 08:00)
    """
    # This function would query your database/calendar for upcoming appointments
    # For now, it's a placeholder - you'd need to implement based on your storage
    pass

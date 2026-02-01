"""
Email Service Module for LISHAY Booking System
Uses SendGrid HTTP API (no SMTP)
"""

import os
import sys
import logging
import requests
import traceback
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Configure logging for production (Railway)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [EMAIL_SERVICE] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)

# SendGrid configuration
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
EMAIL_FROM = os.getenv('EMAIL_FROM', '')
EMAIL_SENDER_NAME = os.getenv('EMAIL_SENDER_NAME', 'LISHAY SIMANI')

# Business info
BUSINESS_NAME = 'LISHAY SIMANI'
BUSINESS_PHONE = '051-5656295'
BUSINESS_ADDRESS = 'משעול הרקפת 3, קרני שומרון'

# SendGrid API endpoint
SENDGRID_URL = 'https://api.sendgrid.com/v3/mail/send'


def get_email_template(booking_data, template_type='confirmation'):
    """Generate HTML email template."""
    date_obj = datetime.strptime(booking_data['date'], '%Y-%m-%d')
    days_hebrew = ['ראשון', 'שני', 'שלישי', 'רביעי', 'חמישי', 'שישי', 'שבת']
    day_name = days_hebrew[date_obj.weekday()]
    formatted_date = f"יום {day_name}, {date_obj.strftime('%d/%m/%Y')}"

    if template_type == 'confirmation':
        subject = f'אישור תור - {BUSINESS_NAME}'
        intro_text = 'התור שלך אושר בהצלחה!'
        emoji = '✨'
    elif template_type == 'reminder_day_before':
        subject = f'תזכורת לתור מחר - {BUSINESS_NAME}'
        intro_text = 'רק להזכיר - יש לך תור מחר!'
        emoji = '💅'
    else:
        subject = f'תזכורת - התור שלך היום! - {BUSINESS_NAME}'
        intro_text = 'היום יש לך תור אצלנו!'
        emoji = '🌸'

    html_content = f'''<!DOCTYPE html>
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
                            <div style="text-align: center; margin-bottom: 30px; padding: 20px; background-color: #FBF6EE; border-radius: 10px;">
                                <p style="margin: 0 0 5px; font-size: 14px; color: #8A847C;">
                                    📍 הכתובת שלנו
                                </p>
                                <p style="margin: 0; font-size: 16px; color: #1A1714;">
                                    {BUSINESS_ADDRESS}
                                </p>
                            </div>
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
                            <p style="margin: 20px 0 0; font-size: 14px; color: #8A847C; text-align: center;">
                                שאלות? התקשרי אלינו: <a href="tel:{BUSINESS_PHONE}" style="color: #C4A35A; text-decoration: none;">{BUSINESS_PHONE}</a>
                            </p>
                        </td>
                    </tr>
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
</html>'''

    return subject, html_content


def send_email(to_email, subject, html_content):
    """
    Send email using SendGrid HTTP API.
    Returns True on success, False on failure.
    """
    logger.info("=" * 50)
    logger.info("SENDGRID EMAIL - SEND ATTEMPT STARTED")
    logger.info(f"To: {to_email}")
    logger.info(f"Subject: {subject}")
    logger.info(f"From: {EMAIL_FROM}")
    logger.info(f"Sender Name: {EMAIL_SENDER_NAME}")
    logger.info(f"API Key configured: {bool(SENDGRID_API_KEY)} (length: {len(SENDGRID_API_KEY) if SENDGRID_API_KEY else 0})")
    sys.stdout.flush()

    if not SENDGRID_API_KEY:
        logger.error("SENDGRID_API_KEY is missing!")
        sys.stdout.flush()
        return False

    if not EMAIL_FROM:
        logger.error("EMAIL_FROM is missing!")
        sys.stdout.flush()
        return False

    payload = {
        "personalizations": [
            {
                "to": [{"email": to_email}],
                "subject": subject
            }
        ],
        "from": {
            "email": EMAIL_FROM,
            "name": EMAIL_SENDER_NAME
        },
        "content": [
            {
                "type": "text/html",
                "value": html_content
            }
        ]
    }

    headers = {
        "Authorization": f"Bearer {SENDGRID_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        logger.info("Sending request to SendGrid API...")
        sys.stdout.flush()

        response = requests.post(
            SENDGRID_URL,
            json=payload,
            headers=headers,
            timeout=30
        )

        if response.status_code in [200, 201, 202]:
            logger.info(f"SUCCESS: Email sent to {to_email}")
            logger.info(f"SendGrid status code: {response.status_code}")
            logger.info("=" * 50)
            sys.stdout.flush()
            return True
        else:
            logger.error("=" * 50)
            logger.error("SENDGRID EMAIL FAILED!")
            logger.error(f"Status code: {response.status_code}")
            logger.error(f"Response: {response.text}")
            logger.error("=" * 50)
            sys.stdout.flush()
            return False

    except requests.exceptions.Timeout:
        logger.error("=" * 50)
        logger.error("SENDGRID TIMEOUT!")
        logger.error("Request timed out after 30 seconds")
        logger.error("=" * 50)
        sys.stdout.flush()
        return False

    except requests.exceptions.ConnectionError as e:
        logger.error("=" * 50)
        logger.error("SENDGRID CONNECTION ERROR!")
        logger.error(f"Error: {str(e)}")
        logger.error("=" * 50)
        sys.stdout.flush()
        return False

    except Exception as e:
        logger.error("=" * 50)
        logger.error("SENDGRID UNEXPECTED ERROR!")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error(f"Error: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        logger.error("=" * 50)
        sys.stdout.flush()
        return False


def send_booking_confirmation(booking_data):
    """Send booking confirmation email to customer."""
    logger.info("=" * 50)
    logger.info("BOOKING CONFIRMATION EMAIL TRIGGERED")
    logger.info(f"Customer: {booking_data.get('name', 'N/A')}")
    logger.info(f"Email: {booking_data.get('email', 'N/A')}")
    logger.info(f"Service: {booking_data.get('service_he', booking_data.get('service', 'N/A'))}")
    logger.info(f"Date: {booking_data.get('date', 'N/A')} at {booking_data.get('time', 'N/A')}")
    sys.stdout.flush()

    subject, html_content = get_email_template(booking_data, 'confirmation')
    result = send_email(booking_data['email'], subject, html_content)
    logger.info(f"BOOKING CONFIRMATION RESULT: {'SUCCESS' if result else 'FAILED'}")
    sys.stdout.flush()
    return result


def send_reminder_day_before(booking_data):
    """Send reminder email one day before the appointment."""
    logger.info("DAY-BEFORE REMINDER EMAIL TRIGGERED")
    logger.info(f"Customer: {booking_data.get('name', 'N/A')} - {booking_data.get('email', 'N/A')}")
    sys.stdout.flush()

    subject, html_content = get_email_template(booking_data, 'reminder_day_before')
    result = send_email(booking_data['email'], subject, html_content)
    logger.info(f"DAY-BEFORE REMINDER RESULT: {'SUCCESS' if result else 'FAILED'}")
    sys.stdout.flush()
    return result


def send_reminder_morning(booking_data):
    """Send reminder email on the morning of the appointment."""
    logger.info("MORNING REMINDER EMAIL TRIGGERED")
    logger.info(f"Customer: {booking_data.get('name', 'N/A')} - {booking_data.get('email', 'N/A')}")
    sys.stdout.flush()

    subject, html_content = get_email_template(booking_data, 'reminder_morning')
    result = send_email(booking_data['email'], subject, html_content)
    logger.info(f"MORNING REMINDER RESULT: {'SUCCESS' if result else 'FAILED'}")
    sys.stdout.flush()
    return result

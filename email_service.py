"""
Email Service Module for LISHAY Booking System
Handles sending booking confirmations and reminders
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# Email configuration
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
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        print("Warning: SMTP credentials not configured (SMTP_EMAIL or SMTP_PASSWORD missing). Email not sent.")
        print(f"SMTP_EMAIL configured: {bool(SMTP_EMAIL)}")
        print(f"SMTP_PASSWORD configured: {bool(SMTP_PASSWORD)}")
        return False

    try:
        print(f"Attempting to send email to {to_email} via {SMTP_SERVER}:{SMTP_PORT}")

        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'{SMTP_SENDER_NAME} <{SMTP_EMAIL}>'
        msg['To'] = to_email

        # Attach HTML content
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)

        # Connect and send
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)

        print(f"Email sent successfully to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        print(f"SMTP Authentication failed - check SMTP_EMAIL and SMTP_PASSWORD: {str(e)}")
        return False
    except smtplib.SMTPException as e:
        print(f"SMTP error: {str(e)}")
        return False
    except Exception as e:
        print(f"Failed to send email: {type(e).__name__}: {str(e)}")
        return False


def send_booking_confirmation(booking_data):
    """
    Send booking confirmation email to customer.
    """
    subject, html_content = get_email_template(booking_data, 'confirmation')
    return send_email(booking_data['email'], subject, html_content)


def send_reminder_day_before(booking_data):
    """
    Send reminder email one day before the appointment.
    """
    subject, html_content = get_email_template(booking_data, 'reminder_day_before')
    return send_email(booking_data['email'], subject, html_content)


def send_reminder_morning(booking_data):
    """
    Send reminder email on the morning of the appointment.
    """
    subject, html_content = get_email_template(booking_data, 'reminder_morning')
    return send_email(booking_data['email'], subject, html_content)


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

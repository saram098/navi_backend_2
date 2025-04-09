import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from settings.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_email(to_email: str, subject: str, body: str, is_html: bool = False):
    """
    Send an email using the configured SMTP server.
    
    In production, this would send an actual email.
    For development, it's mocked to print the email content to console.
    """
    # If email credentials are not configured, just log the email
    if not all([settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD, settings.EMAIL_FROM]):
        logger.info(f"Email would be sent to: {to_email}")
        logger.info(f"Subject: {subject}")
        logger.info(f"Body: {body}")
        return True
    
    # In production, send actual email
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_FROM
        msg['To'] = to_email
        msg['Subject'] = subject
        
        if is_html:
            msg.attach(MIMEText(body, 'html'))
        else:
            msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(settings.EMAIL_HOST, settings.EMAIL_PORT)
        server.starttls()
        server.login(settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(settings.EMAIL_FROM, to_email, text)
        server.quit()
        logger.info(f"Email sent successfully to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

async def send_otp_email(to_email: str, otp: str):
    """Send an OTP to the user's email."""
    subject = "Your OTP for Account Verification"
    body = f"""
    Hello,
    
    Your One Time Password (OTP) for account verification is: {otp}
    
    This OTP is valid for 10 minutes.
    
    If you didn't request this OTP, please ignore this email.
    
    Regards,
    The Clinic Team
    """
    return await send_email(to_email, subject, body)

async def send_password_reset_email(to_email: str, reset_token: str):
    """Send a password reset email with a token link."""
    subject = "Password Reset Request"
    # In a real application, you would include a link to your frontend
    # that includes the token as a parameter
    body = f"""
    Hello,
    
    You have requested to reset your password. Please use the following token:
    
    {reset_token}
    
    This token is valid for 1 hour.
    
    If you didn't request a password reset, please ignore this email.
    
    Regards,
    The Clinic Team
    """
    return await send_email(to_email, subject, body)

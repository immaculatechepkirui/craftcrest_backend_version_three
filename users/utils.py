from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
import logging

logger = logging.getLogger(__name__)

def send_otp_email(email, otp, purpose='verify'):
    if not email:
        raise ValueError("Email address is required.")
    if purpose not in ['verify', 'reset']:
        raise ValueError("Purpose must be 'verify' or 'reset'.")
    subject = 'Verify Your Email - CraftCrest App' if purpose == 'verify' else 'Reset Your Password - CraftCrest App'
    message = f'Hello,\n\nYour {"verification" if purpose == "verify" else "password reset"} code is: {otp}\n\nThis code is valid for 10 minutes. Please use it to {"verify your account" if purpose == "verify" else "reset your password"}.\n\nThank you,\nCraftCrest Team'    
    logger.debug(f"Sending {purpose} email to {email} with OTP {otp}")
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    logger.debug(f"{purpose.capitalize()} email with OTP {otp} sent to {email}")
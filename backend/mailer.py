import os
import smtplib
from email.message import EmailMessage


SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "SentinelAI")


def smtp_is_configured() -> bool:
    return bool(SMTP_EMAIL and SMTP_APP_PASSWORD)


def send_otp_email(recipient_email: str, otp_code: str, expires_in_minutes: int = 5) -> str:
    """Send an OTP email via SMTP. Falls back to console logging if SMTP is not configured."""
    subject = "Your SentinelAI login code"
    body = (
        f"Your SentinelAI verification code is: {otp_code}\n\n"
        f"This code expires in {expires_in_minutes} minute(s).\n"
        "If you did not request this, you can ignore this email."
    )

    if not smtp_is_configured():
        print(f"OTP for {recipient_email}: {otp_code}")
        return "console"

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_EMAIL}>"
    message["To"] = recipient_email
    message.set_content(body)

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
            smtp.send_message(message)
        return "smtp"
    except Exception as exc:
        print(f"[mailer] SMTP delivery failed, falling back to console: {exc}")
        print(f"OTP for {recipient_email}: {otp_code}")
        return "console_fallback"
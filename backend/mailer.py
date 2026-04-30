import os
import smtplib
import logging
import time
from email.message import EmailMessage
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_APP_PASSWORD = os.getenv("SMTP_APP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "SentinelAI")
SMTP_RETRIES = int(os.getenv("SMTP_RETRIES", "3"))
SMTP_TIMEOUT = int(os.getenv("SMTP_TIMEOUT", "10"))

# Production mode: fail hard on SMTP errors instead of falling back to console
# Set SMTP_STRICT_MODE=1 to require SMTP delivery (no console fallback)
SMTP_STRICT_MODE = os.getenv("SMTP_STRICT_MODE", "0") == "1"


def smtp_is_configured() -> bool:
    """Check if SMTP credentials are configured."""
    return bool(SMTP_EMAIL and SMTP_APP_PASSWORD)


def send_otp_email(recipient_email: str, otp_code: str, expires_in_minutes: int = 5) -> dict:
    """
    Send an OTP email via SMTP with retry logic.
    
    Returns dict with:
    {
        "status": "delivered" | "failed" | "console_fallback" | "not_configured",
        "attempts": <int>,
        "error": <str or None>,
        "timestamp": <ISO string>
    }
    """
    subject = "Your SentinelAI login code"
    body = (
        f"Your SentinelAI verification code is: {otp_code}\n\n"
        f"This code expires in {expires_in_minutes} minute(s).\n"
        "If you did not request this, you can ignore this email."
    )

    result = {
        "status": "not_configured",
        "attempts": 0,
        "error": None,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if not smtp_is_configured():
        logger.warning(f"[{result['timestamp']}] SMTP not configured. Falling back to console for {recipient_email}")
        print(f"[OTP_CONSOLE] {recipient_email}: {otp_code}")
        result["status"] = "console_fallback" if not SMTP_STRICT_MODE else "failed"
        result["error"] = "SMTP not configured"
        return result

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{SMTP_FROM_NAME} <{SMTP_EMAIL}>"
    message["To"] = recipient_email
    message.set_content(body)

    last_error = None
    for attempt in range(1, SMTP_RETRIES + 1):
        result["attempts"] = attempt
        try:
            logger.info(f"[{result['timestamp']}] SMTP attempt {attempt}/{SMTP_RETRIES} for {recipient_email}")
            
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=SMTP_TIMEOUT) as smtp:
                smtp.starttls()
                smtp.login(SMTP_EMAIL, SMTP_APP_PASSWORD)
                smtp.send_message(message)
            
            result["status"] = "delivered"
            logger.info(f"[{result['timestamp']}] OTP delivered via SMTP for {recipient_email}")
            return result
            
        except smtplib.SMTPAuthenticationError as e:
            last_error = f"SMTP authentication failed: {str(e)}"
            logger.error(f"[{result['timestamp']}] {last_error} (attempt {attempt}/{SMTP_RETRIES})")
            if attempt < SMTP_RETRIES:
                backoff_seconds = 2 ** (attempt - 1)  # 1s, 2s, 4s
                time.sleep(backoff_seconds)
                
        except smtplib.SMTPException as e:
            last_error = f"SMTP error: {str(e)}"
            logger.error(f"[{result['timestamp']}] {last_error} (attempt {attempt}/{SMTP_RETRIES})")
            if attempt < SMTP_RETRIES:
                backoff_seconds = 2 ** (attempt - 1)
                time.sleep(backoff_seconds)
                
        except Exception as e:
            last_error = f"Unexpected error: {type(e).__name__}: {str(e)}"
            logger.error(f"[{result['timestamp']}] {last_error} (attempt {attempt}/{SMTP_RETRIES})")
            if attempt < SMTP_RETRIES:
                backoff_seconds = 2 ** (attempt - 1)
                time.sleep(backoff_seconds)

    # All retries exhausted
    result["error"] = last_error
    
    if SMTP_STRICT_MODE:
        result["status"] = "failed"
        logger.critical(f"[{result['timestamp']}] SMTP delivery failed after {SMTP_RETRIES} attempts for {recipient_email}. Strict mode enabled, not falling back to console.")
        return result
    else:
        result["status"] = "console_fallback"
        logger.warning(f"[{result['timestamp']}] SMTP delivery failed after {SMTP_RETRIES} attempts. Falling back to console for {recipient_email}")
        print(f"[OTP_CONSOLE_FALLBACK] {recipient_email}: {otp_code}")
        return result
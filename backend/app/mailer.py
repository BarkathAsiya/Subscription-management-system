import smtplib
from email.message import EmailMessage
from .config import settings

def send_password_reset_email(to_email: str, reset_url: str) -> bool:
    required = [settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]
    if not all(required):
        if settings.debug_reset_links:
            print(f"[LOCAL DEVELOPMENT ONLY] Password reset link for {to_email}: {reset_url}")
        return False

    message = EmailMessage()
    message["Subject"] = "Reset your SubSentry AI password"
    message["From"] = settings.smtp_from
    message["To"] = to_email
    message.set_content(
        "We received a request to reset your SubSentry AI password.\n\n"
        f"Use this one-time link within 30 minutes:\n{reset_url}\n\n"
        "If you did not request this, you can ignore this email."
    )
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        server.starttls()
        server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)
    return True

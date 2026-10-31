
import os
import requests
from dotenv import load_dotenv

load_dotenv()

BREVO_API_KEY = os.getenv("BREVO_API_KEY")
BREVO_SENDER_EMAIL = os.getenv("BREVO_SENDER_EMAIL")


def send_reset_email(receiver_email: str, reset_link: str):

    if not BREVO_API_KEY or not BREVO_SENDER_EMAIL:
        raise RuntimeError("Brevo email settings are missing")

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {
            "name": "SubSentry AI",
            "email": BREVO_SENDER_EMAIL
        },
        "to": [
            {
                "email": receiver_email
            }
        ],
        "subject": "Reset Your SubSentry AI Password",
        "htmlContent": f"""
            <h2>Password Reset Request</h2>
            <p>We received a request to reset your SubSentry AI password.</p>
            <p>Click the link below to reset your password:</p>
            <a href="{reset_link}">Reset Password</a>
            <p>If you did not request this, please ignore this email.</p>
        """
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=15
    )

    if response.status_code not in (200, 201, 202):
        raise RuntimeError(
            f"Brevo email sending failed: "
            f"{response.status_code} - {response.text}"
        )

    print("Brevo response:", response.status_code, response.text)

    return response.json()

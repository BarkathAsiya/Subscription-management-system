
import secrets
import hashlib
from datetime import datetime, timedelta, timezone


def generate_reset_token():
    # Generate a secure random token
    token = secrets.token_urlsafe(32)

    # Store only the hash in the database
    token_hash = hashlib.sha256(
        token.encode()
    ).hexdigest()

    # Token expires after 15 minutes
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=15
    )

    return token, token_hash, expires_at


def hash_reset_token(token: str):
    return hashlib.sha256(
        token.encode()
    ).hexdigest()

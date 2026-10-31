import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
from pwdlib import PasswordHash
from .config import settings

password_hasher = PasswordHash.recommended()
ALGORITHM = "HS256"

def validate_password(password: str) -> None:
    problems = []
    if len(password) <= 8:
        problems.append("Password must be longer than 8 characters.")
    if not re.search(r"[A-Z]", password):
        problems.append("Password must include an uppercase letter.")
    if not re.search(r"[a-z]", password):
        problems.append("Password must include a lowercase letter.")
    if not re.search(r"[^A-Za-z0-9]", password):
        problems.append("Password must include a special character.")
    if problems:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=problems)

def hash_password(password: str) -> str:
    validate_password(password)
    return password_hasher.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return password_hasher.verify(password, hashed)

def create_access_token(user_id: int, role: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(user_id), "role": role, "exp": expires}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="Invalid or expired access token.")

def create_reset_token() -> str:
    return secrets.token_urlsafe(40)

def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()

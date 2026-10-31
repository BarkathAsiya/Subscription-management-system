from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, UserRole, PasswordResetToken
from ..schemas import (
    RegisterRequest, LoginRequest, UserOut, TokenResponse,
    ForgotPasswordRequest, ResetPasswordRequest
)
from ..security import (
    hash_password, verify_password, validate_password, create_access_token,
    create_reset_token, hash_reset_token
)
from ..deps import get_current_user, require_roles
from ..mailer import send_password_reset_email
from ..config import settings

router = APIRouter(prefix="/api", tags=["Authentication"])

@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    validate_password(payload.password)
    user = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.customer,  # Public registration can NEVER select a privileged role.
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, user=user)

@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="This account has been deactivated.")
    token = create_access_token(user.id, user.role.value)
    return TokenResponse(access_token=token, user=user)

@router.get("/auth/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user

@router.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    # Generic response prevents account/email enumeration.
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if user and user.is_active:
        raw_token = create_reset_token()
        record = PasswordResetToken(
            user_id=user.id,
            token_hash=hash_reset_token(raw_token),
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        )
        db.add(record)
        db.commit()
        reset_url = f"{settings.frontend_url}/reset-password?token={raw_token}"
        try:
            send_password_reset_email(user.email, reset_url)
        except Exception as exc:
            # Avoid leaking account existence or SMTP details to the caller.
            print(f"Password reset email delivery failed: {exc}")
    return {"message": "If an account exists for that email, password reset instructions have been sent."}

@router.post("/auth/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)):
    validate_password(payload.new_password)
    token_hash = hash_reset_token(payload.token)
    record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None),
    ).first()
    now = datetime.now(timezone.utc)
    if not record:
        raise HTTPException(status_code=400, detail="This reset link is invalid or has already been used.")
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < now:
        raise HTTPException(status_code=400, detail="This reset link has expired. Request a new one.")
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=400, detail="This reset link is invalid.")
    user.password_hash = hash_password(payload.new_password)
    record.used_at = now
    db.commit()
    return {"message": "Password updated successfully. You can now log in."}

@router.get("/customer/me", response_model=UserOut)
def customer_profile(user: User = Depends(require_roles(UserRole.customer))):
    # Only the authenticated customer's own profile is returned.
    return user

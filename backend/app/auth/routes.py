
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.auth.user import User, PasswordResetToken
from app.auth.schemas import (
    UserSignup,
    UserResponse,
    UserLogin,
    ForgotPasswordRequest,
    ResetPasswordRequest
)
from app.auth.security import hash_password, verify_password
from app.auth.token import create_access_token
from app.auth.password_reset import (
    generate_reset_token,
    hash_reset_token
)
from app.auth.email_service import send_reset_email

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post(
    "/signup",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(user_data: UserSignup, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email is already registered"
        )

    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role="customer"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post("/login")
def login(user_data: UserLogin, db: Session = Depends(get_db)):

    user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if not user or not verify_password(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == request.email
    ).first()

    # Use the same response whether or not the email exists.
    response_message = (
        "If the email is registered, a password reset link will be sent."
    )

    if not user or not user.is_active:
        return {"message": response_message}

    token, token_hash, expires_at = generate_reset_token()

    # Invalidate previous unused reset tokens for this user.
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id,
        PasswordResetToken.used_at.is_(None)
    ).update(
        {"used_at": datetime.now(timezone.utc)},
        synchronize_session=False
    )

    reset_record = PasswordResetToken(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at
    )

    db.add(reset_record)
    db.commit()

    frontend_url = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173"
    )

    reset_link = (
        f"{frontend_url}/reset-password?token={token}"
    )

    try:
        send_reset_email(user.email, reset_link)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=502,
            detail="Unable to send reset email. Please try again later."
        )

    return {"message": response_message}


@router.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):

    token_hash = hash_reset_token(request.token)

    reset_record = db.query(PasswordResetToken).filter(
        PasswordResetToken.token_hash == token_hash,
        PasswordResetToken.used_at.is_(None)
    ).first()

    if not reset_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid or already used reset link"
        )

    now = datetime.now(timezone.utc)

    if reset_record.expires_at <= now:
        raise HTTPException(
            status_code=400,
            detail="Reset link has expired"
        )

    user = db.query(User).filter(
        User.id == reset_record.user_id
    ).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Unable to reset password"
        )

    user.hashed_password = hash_password(
        request.new_password
    )

    reset_record.used_at = now

    db.commit()

    return {
        "message": "Password reset successfully. Please log in."
    }

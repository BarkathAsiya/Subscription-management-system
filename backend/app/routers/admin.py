from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import require_roles
from ..models import User, UserRole
from ..schemas import CreateStaffRequest, UserOut
from ..security import hash_password, validate_password

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.post("/staff", response_model=UserOut, status_code=201)
def create_staff(
    payload: CreateStaffRequest,
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.admin)),
):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    validate_password(payload.password)
    staff = User(
        full_name=payload.full_name.strip(),
        email=email,
        password_hash=hash_password(payload.password),
        role=UserRole.staff,
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff

@router.get("/users", response_model=list[UserOut])
def list_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_roles(UserRole.admin)),
):
    return db.query(User).order_by(User.created_at.desc()).limit(500).all()

from getpass import getpass
from sqlalchemy.orm import Session
from app.database import Base, engine, SessionLocal
from app.models import User, UserRole
from app.security import hash_password, validate_password

def main():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        if db.query(User).filter(User.role == UserRole.admin).first():
            print("An Admin account already exists. Bootstrap stopped.")
            return
        full_name = input("Admin full name: ").strip()
        email = input("Admin email: ").strip().lower()
        password = getpass("Admin password: ")
        validate_password(password)
        if db.query(User).filter(User.email == email).first():
            print("This email is already registered.")
            return
        admin = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.admin,
        )
        db.add(admin)
        db.commit()
        print(f"Admin account created for {email}. You can now log in.")
    finally:
        db.close()

if __name__ == "__main__":
    main()

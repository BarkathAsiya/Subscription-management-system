
from fastapi import FastAPI

from app.database import engine, Base
from app.auth.user import User, PasswordResetToken
from app.auth.routes import router as auth_router

app = FastAPI(
    title="SubSentry AI",
    description="Subscription Management System API",
    version="1.0.0"
)

# Create database tables
Base.metadata.create_all(bind=engine)

# Register authentication routes
app.include_router(auth_router)


@app.get("/")
def home():
    return {
        "message": "Welcome to SubSentry AI Backend!",
        "status": "Running successfully"
    }

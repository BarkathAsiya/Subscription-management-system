
from fastapi import FastAPI

app = FastAPI(
    title="SubSentry AI",
    description="Subscription Management System API",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "message": "Welcome to SubSentry AI Backend!",
        "status": "Running successfully"
    }


import re
from pydantic import BaseModel, EmailStr, Field, field_validator


class UserSignup(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=9)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain an uppercase letter")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain a lowercase letter")

        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("Password must contain a special character")

        return value

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    is_active: bool

    class Config:
        from_attributes = True
class UserLogin(BaseModel):
    email: EmailStr
    password: str
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=9)

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value):
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain an uppercase letter")

        if not re.search(r"[a-z]", value):
            raise ValueError("Password must contain a lowercase letter")

        if not re.search(r"[^A-Za-z0-9]", value):
            raise ValueError("Password must contain a special character")

        return value

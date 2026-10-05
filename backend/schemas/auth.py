from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class UserProfile(BaseModel):
    id: str
    full_name: str
    email: str
    role: str = "user"
    created_at: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class AuthMessageResponse(BaseModel):
    message: str
    success: bool = True

class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None

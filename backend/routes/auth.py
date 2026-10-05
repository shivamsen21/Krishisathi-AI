import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status

from schemas.auth import (
    UserRegister,
    UserLogin,
    ForgotPasswordRequest,
    TokenResponse,
    UserProfile,
    AuthMessageResponse,
    ProfileUpdate
)
from services.supabase_service import supabase_service
from dependencies import get_current_user

logger = logging.getLogger("agrovision.routes.auth")
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserRegister):
    """
    Register a new user account with Supabase Auth and create a profile.
    """
    try:
        result = supabase_service.sign_up(
            email=str(data.email).strip().lower(),
            password=data.password,
            full_name=data.full_name.strip(),
            role="user"
        )
        return TokenResponse(
            access_token=result["access_token"],
            user=UserProfile(**result["user"])
        )
    except Exception as e:
        logger.error("Registration error: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin):
    """
    Authenticate user via Supabase Auth and return access token & profile.
    """
    try:
        result = supabase_service.sign_in(
            email=str(data.email).strip().lower(),
            password=data.password
        )
        return TokenResponse(
            access_token=result["access_token"],
            user=UserProfile(**result["user"])
        )
    except Exception as e:
        logger.warning("Login failed for %s: %s", data.email, e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )

@router.post("/logout", response_model=AuthMessageResponse)
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Log out the current session.
    """
    return AuthMessageResponse(message="Successfully logged out.")

@router.get("/profile", response_model=UserProfile)
@router.get("/me", response_model=UserProfile)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Retrieve the profile of the currently authenticated user.
    Accessible via both /api/auth/me and /api/auth/profile.
    """
    return UserProfile(
        id=current_user["id"],
        full_name=current_user.get("full_name", ""),
        email=current_user.get("email", ""),
        role=current_user.get("role", "user"),
        created_at=current_user.get("created_at")
    )

@router.put("/profile", response_model=UserProfile)
async def update_profile(
    data: ProfileUpdate,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update profile details for the authenticated user.
    """
    updates = {}
    if data.full_name is not None:
        updates["full_name"] = data.full_name.strip()

    updated = supabase_service.update_profile(current_user["id"], updates)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found or could not be updated."
        )
    return UserProfile(**updated)

@router.post("/forgot-password", response_model=AuthMessageResponse)
async def forgot_password(data: ForgotPasswordRequest):
    """
    Trigger password recovery email via Supabase Auth.
    """
    supabase_service.reset_password_for_email(str(data.email).strip().lower())
    return AuthMessageResponse(
        message="If an account exists with this email, a password reset link has been dispatched."
    )

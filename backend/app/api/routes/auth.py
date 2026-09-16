"""
Authentication API routes for user registration, login, and profile management.
"""
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..database.connection import get_db
from ..services.auth_service import (
    authenticate_user, create_access_token, create_refresh_token,
    decode_token, create_user, get_user_by_email, get_user_by_username,
    get_user_by_id, update_user_profile
)
from ..database.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


# Pydantic models for request/response
class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email_or_username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserProfileResponse(BaseModel):
    id: int
    email: str
    username: str
    full_name: Optional[str] = None
    is_admin: bool
    favorite_driver: Optional[str] = None
    favorite_team: Optional[str] = None
    theme_preference: str
    created_at: datetime


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    favorite_driver: Optional[str] = None
    favorite_team: Optional[str] = None
    theme_preference: Optional[str] = None


# Dependency to get current user from token
async def get_current_user(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Extract and validate JWT token to get current user."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication scheme",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Decode token
    payload = decode_token(token)
    if payload is None or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    user = get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency that requires admin privileges."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    if get_user_by_email(db, request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Check if username already exists
    if get_user_by_username(db, request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken",
        )
    
    # Validate password strength
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
    
    # Create user
    user = create_user(
        db=db,
        email=request.email,
        username=request.username,
        password=request.password,
        full_name=request.full_name,
        is_admin=False  # Regular users are not admins by default
    )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return {
        "message": "Registration successful",
        "user": {
            "id": user.id,
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "is_admin": user.is_admin,
        },
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": 86400,  # 24 hours in seconds
    }


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with email/username and password."""
    # Authenticate user
    user = authenticate_user(db, request.email_or_username, request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=86400,  # 24 hours
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh: str, db: Session = Depends(get_db)):
    """Refresh an access token using a refresh token."""
    # Decode refresh token
    payload = decode_token(refresh)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Verify user exists and is active
    user = get_user_by_id(db, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    
    # Generate new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(data={"sub": str(user.id)})
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=86400,
    )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        is_admin=current_user.is_admin,
        favorite_driver=current_user.favorite_driver,
        favorite_team=current_user.favorite_team,
        theme_preference=current_user.theme_preference,
        created_at=current_user.created_at,
    )


@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    updates = request.dict(exclude_unset=True)
    updated_user = update_user_profile(db, current_user.id, **updates)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update profile",
        )
    
    return UserProfileResponse(
        id=updated_user.id,
        email=updated_user.email,
        username=updated_user.username,
        full_name=updated_user.full_name,
        is_admin=updated_user.is_admin,
        favorite_driver=updated_user.favorite_driver,
        favorite_team=updated_user.favorite_team,
        theme_preference=updated_user.theme_preference,
        created_at=updated_user.created_at,
    )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Logout current user (client-side token removal)."""
    # In a stateless JWT system, logout is handled client-side by removing tokens
    # For enhanced security, you could maintain a blacklist of tokens in Redis
    return {"message": "Logged out successfully"}


@router.get("/verify")
async def verify_token(current_user: User = Depends(get_current_user)):
    """Verify if the current token is valid."""
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "is_admin": current_user.is_admin,
    }

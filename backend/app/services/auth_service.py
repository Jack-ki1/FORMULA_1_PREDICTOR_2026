"""
Authentication service for user management and JWT token handling.
Implements secure password hashing, JWT token creation/validation, and user operations.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..database.models import User
from ..config.settings import Settings

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Settings instance
settings = Settings()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_EXPIRATION_HOURS * 60)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT refresh token with longer expiration."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)  # 7 days for refresh
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def authenticate_user(db: Session, email_or_username: str, password: str) -> Optional[User]:
    """Authenticate a user by email/username and password."""
    # Try to find user by email first, then username
    user = db.query(User).filter(
        (User.email == email_or_username) | (User.username == email_or_username)
    ).first()
    
    if not user:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    if not user.is_active:
        return None
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    return user


def create_user(db: Session, email: str, username: str, password: str, 
                full_name: Optional[str] = None, is_admin: bool = False) -> User:
    """Create a new user with hashed password."""
    hashed_password = get_password_hash(password)
    
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        full_name=full_name,
        is_admin=is_admin,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def update_user_profile(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Update user profile information."""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    # Only allow updating certain fields
    allowed_fields = ['full_name', 'favorite_driver', 'favorite_team', 'theme_preference']
    for field, value in kwargs.items():
        if field in allowed_fields:
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    return user


def deactivate_user(db: Session, user_id: int) -> bool:
    """Deactivate a user account."""
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    user.is_active = False
    db.commit()
    return True


def create_admin_user(db: Session, email: str, username: str, password: str, 
                      full_name: str = "Admin") -> User:
    """Create an admin user."""
    return create_user(db, email, username, password, full_name, is_admin=True)

"""
Authentication middleware to protect API routes.
Requires valid JWT token for all routes except public ones.
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from typing import List, Optional

from ..config.settings import Settings

settings = Settings()

# Public routes that don't require authentication
PUBLIC_ROUTES: List[str] = [
    "/health",
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/api/v1/openapi.json",
    "/metrics",
    "/auth/register",
    "/auth/login",
    "/auth/refresh",
]


def is_public_route(path: str) -> bool:
    """Check if a route is public (doesn't require authentication)."""
    # Exact match
    if path in PUBLIC_ROUTES:
        return True
    
    # Check if path starts with any public route prefix
    for public_path in PUBLIC_ROUTES:
        if path.startswith(public_path):
            return True
    
    return False


async def auth_middleware(request: Request, call_next):
    """Middleware to enforce authentication on protected routes."""
    path = request.url.path
    
    # Skip auth for public routes
    if is_public_route(path):
        return await call_next(request)
    
    # Get authorization header
    authorization = request.headers.get("Authorization")
    
    if not authorization:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Authentication required. Please log in.",
                    "details": {"reason": "missing_token"},
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except (ValueError, AttributeError):
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid authentication format. Use: Bearer <token>",
                    "details": {"reason": "invalid_format"},
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate token
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        
        # Check token type
        if payload.get("type") != "access":
            raise ValueError("Not an access token")
        
        # Store user info in request state for downstream use
        request.state.user_id = payload.get("sub")
        request.state.is_admin = payload.get("is_admin", False)
        
    except (JWTError, ValueError) as e:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid or expired token. Please log in again.",
                    "details": {"reason": str(e)},
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Proceed with request
    return await call_next(request)

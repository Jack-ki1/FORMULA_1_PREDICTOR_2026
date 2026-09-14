import jwt
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g
from backend.app.config.settings import settings

logger = logging.getLogger(__name__)

class AuthError(Exception):
    """Custom exception for authentication errors."""
    pass

def generate_jwt_token(user_id: str, user_role: str = 'user') -> str:
    """Generate JWT token for authenticated user."""
    try:
        payload = {
            'user_id': user_id,
            'role': user_role,
            'exp': datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRATION_HOURS),
            'iat': datetime.utcnow()
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        return token
    except Exception as e:
        logger.error(f"Error generating JWT token: {e}")
        raise AuthError(f"Token generation failed: {str(e)}")

def decode_jwt_token(token: str) -> dict:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")
    except Exception as e:
        logger.error(f"Error decoding JWT token: {e}")
        raise AuthError(f"Token decoding failed: {str(e)}")

def require_auth(f):
    """Decorator to require authentication for endpoints."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            logger.warning("Missing or invalid Authorization header")
            return jsonify({'error': 'Authentication required'}), 401
        
        token = auth_header.split(' ')[1]
        
        try:
            # Decode and verify token
            payload = decode_jwt_token(token)
            g.current_user = payload
            
        except AuthError as e:
            logger.warning(f"Authentication failed: {e}")
            return jsonify({'error': str(e)}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def require_role(required_role: str):
    """Decorator to require specific role for endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401
            
            user_role = g.current_user.get('role', 'user')
            if user_role != required_role:
                logger.warning(f"User {g.current_user.get('user_id')} attempted unauthorized access to {required_role} endpoint")
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input(data: dict, required_fields: list = None, max_length: int = None) -> list:
    """Validate and sanitize input data."""
    errors = []
    
    if not isinstance(data, dict):
        errors.append("Input must be a JSON object")
        return errors
    
    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
    
    # Check input length
    if max_length and len(str(data)) > max_length:
        errors.append(f"Input exceeds maximum length of {max_length} characters")
    
    # Sanitize inputs (basic sanitization)
    for key, value in data.items():
        if isinstance(value, str):
            # Remove potentially dangerous characters
            sanitized_value = value.replace('<', '&lt;').replace('>', '&gt;')
            if sanitized_value != value:
                logger.info(f"Sanitized input field {key} to prevent XSS")
                data[key] = sanitized_value
    
    return errors
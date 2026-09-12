import logging
from functools import wraps
from flask import request, g, jsonify
from config.settings import settings
from security.auth import validate_input

logger = logging.getLogger(__name__)

def add_security_headers(f):
    """Add security headers to response."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Add security headers
        if hasattr(response, 'headers'):
            for header, value in settings.SECURITY_HEADERS.items():
                response.headers[header] = value
        
        return response
    return decorated_function

def rate_limit(limit: str = None):
    """Rate limiting decorator."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not settings.RATE_LIMIT_ENABLED:
                return f(*args, **kwargs)
            
            # Simple in-memory rate limiting (for production, use Redis)
            from datetime import datetime, timedelta
            import time
            
            # Get client IP
            client_ip = request.remote_addr
            
            # Create rate limit key
            limit_key = f"rate_limit:{client_ip}:{f.__name__}"
            
            # Check if we have a rate limit record
            if not hasattr(g, 'rate_limit_records'):
                g.rate_limit_records = {}
            
            if limit_key in g.rate_limit_records:
                record = g.rate_limit_records[limit_key]
                last_request_time = record['time']
                request_count = record['count']
                
                # Reset counter if time window has passed
                if datetime.now() - last_request_time > timedelta(hours=1):
                    request_count = 0
                    
                # Check if limit exceeded
                max_requests = int(limit.split('/')[0]) if limit else 100
                if request_count >= max_requests:
                    logger.warning(f"Rate limit exceeded for {client_ip}")
                    return jsonify({'error': 'Rate limit exceeded'}), 429
                
                # Update record
                g.rate_limit_records[limit_key] = {
                    'time': datetime.now(),
                    'count': request_count + 1
                }
            else:
                # Create new record
                g.rate_limit_records[limit_key] = {
                    'time': datetime.now(),
                    'count': 1
                }
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_and_sanitize_inputs(required_fields: list = None):
    """Validate and sanitize input data for endpoints."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get JSON data
            data = request.get_json()
            
            # Validate input
            if settings.INPUT_VALIDATION_ENABLED:
                errors = validate_input(data, required_fields, settings.MAX_INPUT_LENGTH)
                if errors:
                    logger.warning(f"Input validation errors: {errors}")
                    return jsonify({'errors': errors}), 400
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
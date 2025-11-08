# identity_verification/decorators.py
from django.core.cache import cache
from django.http import JsonResponse
from functools import wraps
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Extract client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def rate_limit(requests=5, window=60, scope='user'):
    """
    Rate limiting decorator for views

    Args:
        requests: Number of allowed requests
        window: Time window in seconds
        scope: 'user' for per-user, 'ip' for per-IP
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if scope == 'user' and request.user.is_authenticated:
                identifier = f"user:{request.user.id}"
            else:
                identifier = f"ip:{get_client_ip(request)}"

            key = f"rate_limit:{identifier}:{request.path}"

            # Get current attempts
            attempts_data = cache.get(
                key, {'count': 0, 'first_attempt': timezone.now().isoformat()})
            current_attempts = attempts_data['count']

            if current_attempts >= requests:
                logger.warning(
                    f"Rate limit exceeded for {identifier} on {request.path}")
                return JsonResponse({
                    'success': False,
                    'message': f'Rate limit exceeded. Please try again in {window} seconds.',
                    'retry_after': window,
                    'code': 'RATE_LIMIT_EXCEEDED'
                }, status=429)

            # Increment attempt count
            attempts_data['count'] = current_attempts + 1
            cache.set(key, attempts_data, window)

            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def sensitive_operation_limit(operations=3, window=300):
    """
    Special rate limiting for sensitive operations like face enrollment
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({
                    'success': False,
                    'message': 'Authentication required'
                }, status=401)

            identifier = f"sensitive:{request.user.id}"
            key = f"operation_limit:{identifier}:{request.path}"

            operations_data = cache.get(
                key, {'count': 0, 'first_operation': timezone.now().isoformat()})
            current_operations = operations_data['count']

            if current_operations >= operations:
                logger.warning(
                    f"Sensitive operation limit exceeded for user {request.user.username}")
                return JsonResponse({
                    'success': False,
                    'message': 'Too many sensitive operations. Please wait before trying again.',
                    'code': 'OPERATION_LIMIT_EXCEEDED'
                }, status=429)

            # Increment operation count
            operations_data['count'] = current_operations + 1
            cache.set(key, operations_data, window)

            response = view_func(request, *args, **kwargs)
            return response
        return wrapped
    return decorator


def require_ajax(view_func):
    """Ensure the request is AJAX"""
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if not request.headers.get('X-Requested-With') == 'XMLHttpRequest' and not settings.DEBUG:
            return JsonResponse({
                'success': False,
                'message': 'AJAX request required',
                'code': 'AJAX_REQUIRED'
            }, status=400)
        return view_func(request, *args, **kwargs)
    return wrapped


def enforce_privacy(view_func):
    """Add privacy headers to response"""
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        response = view_func(request, *args, **kwargs)
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'
        return response
    return wrapped

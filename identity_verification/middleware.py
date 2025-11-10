# identity_verification/middleware.py
from django.utils import timezone
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

# Import camera manager safely to avoid circular imports
try:
    from .views import camera_manager
except ImportError:
    logger.warning("Could not import camera_manager from views")
    camera_manager = None


class CameraCleanupMiddleware:
    """
    Middleware to release camera resources when exceptions occur
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_exception(self, request, exception):
        """Release cameras when an exception occurs in any view"""
        try:
            if camera_manager:
                logger.warning(
                    f"CameraCleanupMiddleware: Releasing cameras due to exception: {str(exception)}")
                camera_manager.release_all_cameras()
                # Small delay to ensure camera is released
                time.sleep(0.5)
            else:
                logger.warning(
                    "CameraCleanupMiddleware: camera_manager not available")
        except Exception as e:
            logger.error(f"Error in camera cleanup middleware: {str(e)}")
        return None


class CameraReleaseMiddleware:
    """
    Middleware to ensure cameras are released after video feed requests
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Define camera-related URL patterns
        self.camera_urls = [
            '/video_feed/',
            '/verify/',
            '/start_camera/',
            '/stop_camera/',
            '/capture_face/',
            '/enroll-face/',
        ]

    def __call__(self, request):
        try:
            response = self.get_response(request)
            return response
        finally:
            # Always try to release cameras after request completion for camera-related URLs
            if self._is_camera_request(request):
                self._release_camera_after_request(request)

    def _is_camera_request(self, request):
        """Check if this is a camera-related request"""
        if not hasattr(request, 'path'):
            return False

        path = request.path
        return any(camera_url in path for camera_url in self.camera_urls)

    def _release_camera_after_request(self, request):
        """Release camera resources after request completion"""
        if not camera_manager:
            return

        try:
            # Extract camera_id from URL if possible
            camera_id = self._extract_camera_id(request.path)

            # Small delay to ensure any ongoing camera operations complete
            time.sleep(0.1)

            # Release the specific camera
            camera_manager.release_camera(camera_id)

            logger.debug(
                f"CameraReleaseMiddleware: Released camera {camera_id} after {request.path}")

        except Exception as e:
            logger.error(f"Error releasing camera in middleware: {str(e)}")

    def _extract_camera_id(self, path):
        """Extract camera ID from URL path"""
        try:
            if '/video_feed/' in path:
                parts = path.split('/')
                for i, part in enumerate(parts):
                    if part == 'video_feed' and i + 1 < len(parts) and parts[i + 1].isdigit():
                        return int(parts[i + 1])

            # Check for camera_id parameter in other URLs
            if '/start_camera/' in path or '/stop_camera/' in path:
                parts = path.split('/')
                if len(parts) > 2 and parts[-2].isdigit():
                    return int(parts[-2])

        except (ValueError, IndexError):
            pass

        return 0  # Default camera ID


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip rate limiting for static files and admin
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return self.get_response(request)

        # Rate limiting for authentication endpoints
        auth_endpoints = [
            '/login/',
            '/admin-login/',
            '/api/face-verification/verify_face/',
            '/api/face-verification/register_face/'
        ]

        if any(request.path.endswith(endpoint) for endpoint in auth_endpoints):
            ip = self.get_client_ip(request)
            key = f"rate_limit:{ip}:{request.path}"

            attempts = cache.get(key, 0)
            if attempts >= 5:  # 5 attempts per minute
                logger.warning(
                    f"Rate limit exceeded for IP: {ip}, Path: {request.path}")
                return JsonResponse({
                    'success': False,
                    'message': 'Too many attempts. Please try again in 60 seconds.',
                    'code': 'RATE_LIMIT_EXCEEDED'
                }, status=429)

            cache.set(key, attempts + 1, 60)  # 1 minute

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip


class SecurityHeadersMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        # CSP Header
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "font-src 'self' https://cdn.jsdelivr.net; "
            "object-src 'none'; "
            "media-src 'self'; "
            "frame-src 'none';"
        )
        response['Content-Security-Policy'] = csp

        # Remove server header
        if 'Server' in response:
            del response['Server']

        return response


class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Update last activity timestamp
            request.session['last_activity'] = timezone.now().isoformat()

            # Check session timeout (1 hour)
            last_activity_str = request.session.get('last_activity')
            if last_activity_str:
                try:
                    last_activity = timezone.datetime.fromisoformat(
                        last_activity_str)
                    if timezone.now() - last_activity > timezone.timedelta(hours=1):
                        # Session expired
                        from django.contrib.auth import logout
                        logout(request)
                        logger.info(
                            f"Session expired for user: {request.user.username}")
                except (ValueError, TypeError):
                    pass

        response = self.get_response(request)
        return response


class LoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Log request details for sensitive endpoints
        sensitive_endpoints = [
            '/login/',
            '/admin-login/',
            '/api/face-verification/',
            '/user-management/',
            '/verify/',
            '/video_feed/',
            '/enroll-face/'
        ]

        if any(request.path.endswith(endpoint) for endpoint in sensitive_endpoints):
            logger.info(
                f"AFZ Access: {request.method} {request.path} - "
                f"IP: {self.get_client_ip(request)} - "
                f"User: {getattr(request.user, 'username', 'Anonymous')}"
            )

        response = self.get_response(request)
        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')

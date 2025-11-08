# identity_verification/context_processors.py
from django.conf import settings
from .models import SystemSettings


def afz_settings(request):
    """Add AFZ system settings to template context"""
    return {
        'afz_system_name': 'Air Force of Zimbabwe Identity System',
        'afz_version': '2.1.0',
        'afz_security_level': 'TOP SECRET',
        'afz_min_confidence': getattr(settings, 'AFZ_CONFIG', {}).get('MIN_FACE_CONFIDENCE', 85.0),
    }


def system_status(request):
    """Add system status information to context"""
    status_info = {
        'system_operational': True,
        'maintenance_mode': False,
        'system_load': 'normal',
    }

    # Check for any critical alerts
    from .models import SecurityAlert
    critical_alerts = SecurityAlert.objects.filter(
        is_resolved=False,
        alert_level__in=['HIGH', 'CRITICAL']
    ).exists()

    if critical_alerts:
        status_info['system_operational'] = False
        status_info['system_load'] = 'high'

    return status_info


def user_permissions(request):
    """Add user permission information to context"""
    if request.user.is_authenticated:
        return {
            'user_can_manage_users': request.user.is_staff,
            'user_can_view_logs': request.user.is_staff,
            'user_can_manage_system': request.user.is_superuser,
            'user_has_face_enrolled': hasattr(request.user, 'userprofile') and request.user.userprofile.face_enrolled,
        }
    return {}

from django.contrib import admin
from .models import (
    SystemSettings, Person, IDRecord, SecurityLog,
    FaceVerificationSession, AccessLog
)


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    """
    Admin interface for system settings
    """
    list_display = ['system_name', 'max_login_attempts',
                    'session_timeout', 'face_match_threshold']
    list_editable = ['max_login_attempts',
                     'session_timeout', 'face_match_threshold']


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    """
    Admin interface for military personnel
    """
    list_display = ['service_number', 'rank', 'first_name',
                    'last_name', 'unit', 'security_clearance', 'status']
    list_filter = ['rank', 'unit', 'security_clearance', 'status']
    search_fields = ['first_name', 'last_name', 'service_number', 'rank']
    ordering = ['rank', 'last_name']


@admin.register(IDRecord)
class IDRecordAdmin(admin.ModelAdmin):
    """
    Admin interface for ID records
    """
    list_display = ['security_number', 'person',
                    'id_type', 'issue_date', 'expiry_date', 'status']
    list_filter = ['id_type', 'status', 'issue_date']
    search_fields = ['security_number',
                     'person__first_name', 'person__last_name']
    ordering = ['-issue_date']


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    """
    Admin interface for security logs
    """
    list_display = ['timestamp', 'person', 'action', 'ip_address']
    list_filter = ['action', 'timestamp']
    search_fields = ['person__first_name', 'person__last_name', 'action']
    ordering = ['-timestamp']
    readonly_fields = ['timestamp']  # Can't edit timestamps


# YOUR EXISTING ADMIN REGISTRATIONS
@admin.register(FaceVerificationSession)
class FaceVerificationSessionAdmin(admin.ModelAdmin):
    """
    Admin interface for your existing face verification sessions
    """
    list_display = ['user', 'session_id', 'created_at', 'is_active']
    list_filter = ['is_active', 'created_at']


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    """
    Admin interface for your existing access logs
    """
    list_display = ['user', 'timestamp',
                    'verification_method', 'success', 'confidence_score']
    list_filter = ['verification_method', 'success', 'timestamp']

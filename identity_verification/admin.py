from django.contrib import admin
from .models import FaceVerificationSession, AccessLog


@admin.register(FaceVerificationSession)
class FaceVerificationSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'verification_type',
                    'status', 'created_at', 'confidence_score')
    list_filter = ('verification_type', 'status', 'created_at')
    search_fields = ('user__username', 'session_id', 'security_number')
    readonly_fields = ('session_id', 'created_at', 'completed_at')

    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'session_id', 'security_number', 'verification_type')
        }),
        ('Status', {
            'fields': ('status', 'confidence_score', 'created_at', 'completed_at')
        }),
    )


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'visitor', 'action',
                    'verified_by_face', 'timestamp', 'location')
    list_filter = ('action', 'verified_by_face', 'timestamp')
    search_fields = ('user__username', 'visitor__full_name', 'location')
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'visitor', 'action', 'location')
        }),
        ('Verification', {
            'fields': ('verified_by_face', 'ip_address', 'user_agent')
        }),
        ('Timing', {
            'fields': ('timestamp',)
        }),
    )

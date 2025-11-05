from django.contrib import admin
from .models import FaceVerificationSession, AccessLog


@admin.register(FaceVerificationSession)
class FaceVerificationSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_id', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__username', 'session_id')
    readonly_fields = ('session_id', 'created_at')

    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'session_id')
        }),
        ('Status', {
            'fields': ('is_active', 'created_at')
        }),
    )


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'timestamp', 'verification_method',
                    'success', 'confidence_score')
    list_filter = ('verification_method', 'success', 'timestamp')
    search_fields = ('user__username', 'user__security_number')
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'verification_method', 'success')
        }),
        ('Verification Details', {
            'fields': ('confidence_score', 'timestamp')
        }),
    )

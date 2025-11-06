from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import FaceVerificationSession, AccessLog


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'timestamp', 'verification_method',
                    'success_badge', 'confidence_score', 'get_security_number']
    list_filter = ['verification_method', 'success', 'timestamp']
    search_fields = ['user__username', 'user__security_number']
    readonly_fields = ['timestamp']
    list_per_page = 25

    def success_badge(self, obj):
        if obj.success:
            return format_html('<span style="color: green; font-weight: bold;">✅ SUCCESS</span>')
        else:
            return format_html('<span style="color: red; font-weight: bold;">❌ FAILED</span>')
    success_badge.short_description = 'Status'

    def get_security_number(self, obj):
        return obj.user.security_number
    get_security_number.short_description = 'Security Number'


@admin.register(FaceVerificationSession)
class FaceVerificationSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'session_id', 'created_at', 'is_active_badge']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'session_id']
    readonly_fields = ['created_at']
    list_per_page = 20

    def is_active_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green; font-weight: bold;">● ACTIVE</span>')
        else:
            return format_html('<span style="color: gray; font-weight: bold;">● INACTIVE</span>')
    is_active_badge.short_description = 'Session Status'


# Custom admin site header
admin.site.site_header = "🛡️ Air Force Zimbabwe - Identity System Administration"
admin.site.site_title = "AFZ Identity System"
admin.site.index_title = "Command Center Administration"

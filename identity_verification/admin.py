# identity_verification/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import UserProfile, AccessLog, SystemSettings, SecurityAlert, FaceEncodingArchive, SystemHealth


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'
    fields = (
        'face_enrolled', 'face_enrollment_date', 'security_clearance',
        'department', 'rank', 'service_number', 'verification_count'
    )
    readonly_fields = ('face_enrollment_date', 'verification_count')


class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'is_staff', 'face_enrolled_status', 'last_login', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active',
                   'userprofile__face_enrolled', 'userprofile__security_clearance')

    def face_enrolled_status(self, obj):
        try:
            return obj.userprofile.face_enrolled
        except UserProfile.DoesNotExist:
            return False
    face_enrolled_status.boolean = True
    face_enrolled_status.short_description = 'Face Enrolled'


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'login_method', 'status', 'ip_address',
                    'timestamp', 'confidence_score', 'is_suspicious')
    list_filter = ('login_method', 'status', 'timestamp', 'is_suspicious')
    search_fields = ('user__username', 'ip_address', 'details')
    readonly_fields = ('timestamp',)
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Authentication Details', {
            'fields': ('user', 'login_method', 'status', 'confidence_score')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'geolocation')
        }),
        ('Security Information', {
            'fields': ('is_suspicious', 'flagged_reason', 'details')
        }),
        ('Timestamps', {
            'fields': ('timestamp', 'session_duration')
        }),
    )


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('key', 'value', 'data_type', 'is_public', 'updated_at')
    list_filter = ('data_type', 'is_public')
    search_fields = ('key', 'description')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(SecurityAlert)
class SecurityAlertAdmin(admin.ModelAdmin):
    list_display = ('title', 'alert_type', 'alert_level',
                    'related_user', 'is_resolved', 'created_at')
    list_filter = ('alert_type', 'alert_level', 'is_resolved', 'created_at')
    search_fields = ('title', 'description', 'related_user__username')
    readonly_fields = ('created_at',)


@admin.register(FaceEncodingArchive)
class FaceEncodingArchiveAdmin(admin.ModelAdmin):
    list_display = ('user', 'encoding_version', 'quality_score', 'archived_at')
    list_filter = ('encoding_version', 'archived_at')
    search_fields = ('user__username',)
    readonly_fields = ('created_at', 'archived_at')


@admin.register(SystemHealth)
class SystemHealthAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'cpu_usage', 'memory_usage',
                    'disk_usage', 'active_users')
    list_filter = ('timestamp',)
    readonly_fields = ('timestamp',)


# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

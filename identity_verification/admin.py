from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserProfile, AccessLog, SystemSettings


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'security_number',
                    'unit', 'user_type', 'is_verified', 'is_active', 'is_staff']
    list_filter = ['user_type', 'is_verified',
                   'is_active', 'is_staff', 'date_joined']
    search_fields = ['username', 'email', 'security_number',
                     'unit', 'first_name', 'last_name']
    ordering = ['-date_joined']

    fieldsets = UserAdmin.fieldsets + (
        ('AFZ Information', {
            'fields': (
                'security_number',
                'unit',
                'user_type',
                'is_verified',
                'verification_date',
                'face_encoding'
            )
        }),
    )

    readonly_fields = ['verification_date']

    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ['security_number']
        return self.readonly_fields


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'face_enrolled',
                    'face_enrollment_date', 'department', 'phone', 'created_at']
    list_filter = ['face_enrolled', 'department', 'created_at']
    search_fields = ['user__username', 'user__email', 'department', 'phone']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'face_enrolled', 'face_enrollment_date')
        }),
        ('Contact Information', {
            'fields': ('department', 'phone'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AccessLog)
class AccessLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'login_method', 'status',
                    'ip_address', 'timestamp', 'confidence_score']
    list_filter = ['login_method', 'status', 'timestamp', 'device_type']
    search_fields = ['user__username', 'ip_address', 'details', 'location']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'

    fieldsets = (
        (None, {
            'fields': ('user', 'login_method', 'status')
        }),
        ('Technical Details', {
            'fields': ('ip_address', 'user_agent', 'device_type', 'location', 'confidence_score'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('details', 'timestamp'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Prevent manual addition of access logs (they should be created by the system)
        return False


@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ['setting_key', 'setting_value', 'updated_at']
    list_filter = ['updated_at']
    search_fields = ['setting_key', 'description', 'setting_value']
    readonly_fields = ['updated_at']

    fieldsets = (
        (None, {
            'fields': ('setting_key', 'setting_value')
        }),
        ('Description', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of critical system settings
        if obj and obj.setting_key in ['SYSTEM_NAME', 'SECURITY_LEVEL', 'SYSTEM_VERSION']:
            return False
        return super().has_delete_permission(request, obj)


# Custom admin site header and title
admin.site.site_header = "🛡️ AFZ Identity System Administration"
admin.site.site_title = "AFZ Identity System"
admin.site.index_title = "Welcome to AFZ Identity System Administration"

# Optional: Custom admin actions


def activate_users(modeladmin, request, queryset):
    queryset.update(is_active=True)


activate_users.short_description = "Activate selected users"


def deactivate_users(modeladmin, request, queryset):
    queryset.update(is_active=False)


deactivate_users.short_description = "Deactivate selected users"


def mark_face_enrolled(modeladmin, request, queryset):
    for profile in queryset:
        profile.face_enrolled = True
        profile.save()


mark_face_enrolled.short_description = "Mark as face enrolled"

# Add custom actions to UserProfile admin
UserProfileAdmin.actions = [mark_face_enrolled]

# Add custom actions to CustomUser admin
CustomUserAdmin.actions = [activate_users, deactivate_users]

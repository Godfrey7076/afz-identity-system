from django.contrib import admin
from .models import SecuritySettings, SecurityLog


@admin.register(SecuritySettings)
class SecuritySettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'value', 'description')
    search_fields = ('name', 'description')

    fieldsets = (
        ('Security Setting', {
            'fields': ('name', 'value', 'description')
        }),
    )


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'timestamp', 'ip_address')
    list_filter = ('timestamp', 'action')
    search_fields = ('user__username', 'action', 'details', 'ip_address')
    readonly_fields = ('timestamp',)

    fieldsets = (
        ('Security Event', {
            'fields': ('user', 'action', 'details')
        }),
        ('Technical Information', {
            'fields': ('ip_address', 'timestamp')
        }),
    )

from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'notification_type', 'title',
                    'is_read', 'created_at', 'priority')
    list_filter = ('notification_type', 'is_read', 'priority', 'created_at')
    search_fields = ('recipient__username', 'title', 'message')
    readonly_fields = ('created_at',)
    fieldsets = (
        ('Notification Details', {
            'fields': ('recipient', 'notification_type', 'title', 'message', 'priority')
        }),
        ('Related Information', {
            'fields': ('related_visitor',)
        }),
        ('Delivery Status', {
            'fields': ('is_read', 'sent_via_sms', 'sent_via_email', 'sent_via_whatsapp')
        }),
        ('Timing', {
            'fields': ('created_at',)
        }),
    )

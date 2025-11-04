from django.db import models
from users.models import CustomUser, Visitor
import uuid


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('overstay', 'Overstay Alert'),
        ('security_breach', 'Security Breach'),
        ('visitor_approval', 'Visitor Approval Required'),
        ('system_alert', 'System Alert'),
        ('reminder', 'Reminder'),
        ('access_granted', 'Access Granted'),
        ('access_denied', 'Access Denied'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(
        max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_visitor = models.ForeignKey(
        Visitor, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_via_sms = models.BooleanField(default=False)
    sent_via_email = models.BooleanField(default=False)
    sent_via_whatsapp = models.BooleanField(default=False)
    priority = models.CharField(max_length=10, choices=[(
        'low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium')

    def __str__(self):
        return f"{self.notification_type} - {self.recipient.username}"

    class Meta:
        ordering = ['-created_at']

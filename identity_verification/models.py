from django.db import models
from users.models import CustomUser, Visitor
import uuid


class FaceVerificationSession(models.Model):
    SESSION_STATUS = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('timeout', 'Timeout')
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    session_id = models.CharField(
        max_length=100, unique=True, default=uuid.uuid4)
    security_number = models.CharField(max_length=20)
    verification_type = models.CharField(
        max_length=10, choices=[('login', 'Login'), ('logout', 'Logout')])
    status = models.CharField(
        max_length=20, choices=SESSION_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    confidence_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.verification_type} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class AccessLog(models.Model):
    ACCESS_TYPES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('visitor_in', 'Visitor Entry'),
        ('visitor_out', 'Visitor Exit'),
        ('system_access', 'System Access')
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    visitor = models.ForeignKey(
        Visitor, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=20, choices=ACCESS_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)
    location = models.CharField(
        max_length=100, blank=True, default='Main Gate')
    verified_by_face = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.action} - {self.timestamp}"

    class Meta:
        ordering = ['-timestamp']

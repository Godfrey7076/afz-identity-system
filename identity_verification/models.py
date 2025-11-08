from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings


class CustomUser(AbstractUser):
    USER_TYPES = [
        ('command', 'Command Staff'),
        ('security', 'Security Personnel'),
        ('admin', 'Administrative Staff'),
        ('standard', 'Standard User'),
    ]

    security_number = models.CharField(
        max_length=20, unique=True, blank=True, null=True)
    unit = models.CharField(max_length=100, blank=True, null=True)
    user_type = models.CharField(
        max_length=20, choices=USER_TYPES, default='standard')
    is_verified = models.BooleanField(default=False)
    verification_date = models.DateTimeField(null=True, blank=True)
    face_encoding = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'auth_user'

    def __str__(self):
        return f"{self.username} ({self.security_number})"


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    face_enrolled = models.BooleanField(default=False)
    face_enrollment_date = models.DateTimeField(null=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"


class AccessLog(models.Model):
    LOGIN_METHODS = [
        ('Password', 'Password'),
        ('Face Recognition', 'Face Recognition'),
        ('2FA', 'Two-Factor Authentication'),
    ]

    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Failed', 'Failed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE, null=True, blank=True)
    login_method = models.CharField(max_length=20, choices=LOGIN_METHODS)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True)
    confidence_score = models.FloatField(null=True, blank=True)
    device_type = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        username = self.user.username if self.user else 'Unknown'
        return f"{username} - {self.login_method} - {self.status}"


class SystemSettings(models.Model):
    setting_key = models.CharField(max_length=100, unique=True)
    setting_value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.setting_key


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

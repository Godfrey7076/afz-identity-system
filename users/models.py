from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


def generate_security_number():
    return f"AFZ{uuid.uuid4().hex[:8].upper()}"


def generate_visitor_id():
    return uuid.uuid4().hex[:8].upper()


class CustomUser(AbstractUser):
    USER_TYPES = (
        ('pass_desk', 'Passes & Permits Desk'),
        ('supervisor', 'Supervisor'),
        ('commander', 'Unit Commander'),
        ('security_officer', 'Chief Security Officer'),
    )

    user_type = models.CharField(
        max_length=20, choices=USER_TYPES, default='pass_desk')
    security_number = models.CharField(
        max_length=20, unique=True, default=generate_security_number)
    phone_number = models.CharField(max_length=15, blank=True)
    unit = models.CharField(max_length=100, default='Passes and Permits Unit')
    face_encoding = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(
        upload_to='profiles/', null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.security_number:
            self.security_number = generate_security_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"


class Visitor(models.Model):
    VISITOR_STATUS = [
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('active', 'Active Visit'),
        ('completed', 'Completed'),
        ('overstayed', 'Overstayed')
    ]

    visitor_id = models.CharField(
        max_length=20, unique=True, default=generate_visitor_id)
    full_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=20)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(blank=True)
    purpose_of_visit = models.TextField()
    host_member = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='visitors')
    expected_duration = models.IntegerField(
        help_text="Duration in minutes", default=60)
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=VISITOR_STATUS, default='pending')
    created_by = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='created_visitors')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.full_name} - {self.visitor_id}"

    class Meta:
        ordering = ['-created_at']

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

# Get the custom user model from your settings
CustomUser = get_user_model()


# NEW MODELS FOR MILITARY PERSONNEL MANAGEMENT
class SystemSettings(models.Model):
    """
    Stores system-wide settings like security parameters and thresholds
    """
    system_name = models.CharField(
        max_length=200, default='Air Force Zimbabwe Identity System')
    max_login_attempts = models.IntegerField(default=3)
    session_timeout = models.IntegerField(default=30)  # minutes
    face_match_threshold = models.FloatField(default=0.8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.system_name

    class Meta:
        verbose_name = "System Settings"
        verbose_name_plural = "System Settings"


class Person(models.Model):
    """
    Represents military personnel with ranks, units, and security clearances
    """
    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
        ('SUSPENDED', 'Suspended'),
        ('RETIRED', 'Retired'),
    ]

    SECURITY_CLEARANCE_CHOICES = [
        ('TOP SECRET', 'Top Secret'),
        ('SECRET', 'Secret'),
        ('CONFIDENTIAL', 'Confidential'),
        ('RESTRICTED', 'Restricted'),
    ]

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    # Sergeant, Flight Lieutenant, etc.
    rank = models.CharField(max_length=100)
    # Flying Wing, Regiment Dog Section, etc.
    unit = models.CharField(max_length=200)
    service_number = models.CharField(
        max_length=50, unique=True)  # AFZ-XX-XXXX format
    date_of_birth = models.DateField()

    # Security Information
    security_clearance = models.CharField(
        max_length=20,
        choices=SECURITY_CLEARANCE_CHOICES,
        default='RESTRICTED'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    # Face Recognition Data
    face_encoding = models.TextField(
        blank=True, null=True)  # Stores facial features data
    photo = models.ImageField(
        upload_to='person_photos/', blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.rank} {self.first_name} {self.last_name}"

    class Meta:
        verbose_name = "Person"
        verbose_name_plural = "Personnel"


class IDRecord(models.Model):
    """
    Stores ID card information with security numbers for each person
    """
    ID_TYPE_CHOICES = [
        ('MILITARY_ID', 'Military ID'),
        ('ACCESS_CARD', 'Access Card'),
        ('VISITOR_PASS', 'Visitor Pass'),
    ]

    STATUS_CHOICES = [
        ('ACTIVE', 'Active'),
        ('EXPIRED', 'Expired'),
        ('SUSPENDED', 'Suspended'),
        ('REVOKED', 'Revoked'),
    ]

    # Link to Person
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name='id_records')

    # ID Information
    security_number = models.CharField(
        max_length=20, unique=True)  # AFZ-XXXX-XXXX-XXXX format
    issue_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField()
    id_type = models.CharField(
        max_length=20, choices=ID_TYPE_CHOICES, default='MILITARY_ID')
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.security_number} - {self.person}"

    class Meta:
        verbose_name = "ID Record"
        verbose_name_plural = "ID Records"


class SecurityLog(models.Model):
    """
    Logs all security-related events and access attempts
    """
    ACTION_CHOICES = [
        ('LOGIN_ATTEMPT', 'Login Attempt'),
        ('ACCESS_GRANTED', 'Access Granted'),
        ('ACCESS_DENIED', 'Access Denied'),
        ('ID_ISSUED', 'ID Issued'),
        ('ID_REVOKED', 'ID Revoked'),
        ('FACE_VERIFICATION_SUCCESS', 'Face Verification Success'),
        ('FACE_VERIFICATION_FAILED', 'Face Verification Failed'),
    ]

    # Link to Person
    person = models.ForeignKey(
        Person, on_delete=models.CASCADE, related_name='security_logs')

    # Event Information
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)

    # Technical Information
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)

    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp} - {self.person} - {self.action}"

    class Meta:
        verbose_name = "Security Log"
        verbose_name_plural = "Security Logs"


# YOUR EXISTING MODELS - KEEP THESE!
class FaceVerificationSession(models.Model):
    """
    Your existing model for face verification sessions
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.session_id}"


class AccessLog(models.Model):
    """
    Your existing model for access logging
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    verification_method = models.CharField(max_length=20, choices=[
        ('face', 'Face Recognition'),
        ('registration', 'Face Registration'),
        ('manual', 'Manual Verification')
    ])
    success = models.BooleanField()
    confidence_score = models.FloatField(null=True, blank=True)

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.user.username} - {self.verification_method} - {status}"

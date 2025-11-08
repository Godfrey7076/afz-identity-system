# identity_verification/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json
from django.core.cache import cache
from django.db.models.signals import post_save
from django.dispatch import receiver


class UserProfile(models.Model):
    SECURITY_LEVELS = [
        ('RESTRICTED', 'Restricted'),
        ('CONFIDENTIAL', 'Confidential'),
        ('SECRET', 'Secret'),
        ('TOP_SECRET', 'Top Secret'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='userprofile')
    face_enrolled = models.BooleanField(default=False)
    face_enrollment_date = models.DateTimeField(null=True, blank=True)

    # Encrypted face encodings (supports multiple encodings per user)
    face_encoding = models.TextField(null=True, blank=True)
    face_encoding_1 = models.TextField(null=True, blank=True)
    face_encoding_2 = models.TextField(null=True, blank=True)
    face_encoding_count = models.IntegerField(default=0)
    face_encoding_version = models.CharField(max_length=10, default='2.0')

    # Security and user metadata
    security_clearance = models.CharField(
        max_length=20,
        choices=SECURITY_LEVELS,
        default='RESTRICTED'
    )
    department = models.CharField(max_length=100, blank=True)
    rank = models.CharField(max_length=50, blank=True)
    service_number = models.CharField(
        max_length=20, blank=True, unique=True, null=True)

    # Biometric metadata
    last_face_update = models.DateTimeField(null=True, blank=True)
    enrollment_quality_score = models.FloatField(null=True, blank=True)
    last_verification = models.DateTimeField(null=True, blank=True)
    verification_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} Profile"

    def get_face_encodings(self):
        """Get all face encodings for this user"""
        encodings = []
        if self.face_encoding:
            encodings.append(self.face_encoding)
        if self.face_encoding_1:
            encodings.append(self.face_encoding_1)
        if self.face_encoding_2:
            encodings.append(self.face_encoding_2)
        return encodings

    def increment_verification_count(self):
        """Increment verification count and update last verification"""
        self.verification_count += 1
        self.last_verification = timezone.now()
        self.save()

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        indexes = [
            models.Index(fields=['face_enrolled']),
            models.Index(fields=['security_clearance']),
            models.Index(fields=['service_number']),
            models.Index(fields=['last_verification']),
        ]


class AccessLog(models.Model):
    LOGIN_METHODS = [
        ('Password', 'Password'),
        ('Face Recognition', 'Face Recognition'),
        ('Smart Card', 'Smart Card'),
        ('Biometric', 'Biometric'),
        ('Registration', 'Registration'),
        ('Admin Action', 'Admin Action'),
        ('Logout', 'Logout'),
        ('System', 'System'),
    ]

    STATUS_CHOICES = [
        ('Success', 'Success'),
        ('Failed', 'Failed'),
        ('Pending', 'Pending'),
        ('Blocked', 'Blocked'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL,
                             null=True, blank=True, related_name='access_logs')
    login_method = models.CharField(max_length=20, choices=LOGIN_METHODS)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    confidence_score = models.FloatField(null=True, blank=True)
    details = models.TextField(blank=True)
    session_duration = models.DurationField(null=True, blank=True)

    # Security flags
    is_suspicious = models.BooleanField(default=False)
    flagged_reason = models.TextField(blank=True)
    geolocation = models.CharField(max_length=100, blank=True)
    device_fingerprint = models.CharField(max_length=255, blank=True)

    # Additional metadata
    attempt_number = models.IntegerField(default=1)
    response_time = models.FloatField(null=True, blank=True)  # in milliseconds

    def __str__(self):
        username = self.user.username if self.user else 'Unknown'
        return f"{username} - {self.login_method} - {self.status} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    def mark_suspicious(self, reason):
        """Mark this log entry as suspicious"""
        self.is_suspicious = True
        self.flagged_reason = reason
        self.save()

        # Create security alert if multiple suspicious activities
        recent_suspicious = AccessLog.objects.filter(
            ip_address=self.ip_address,
            is_suspicious=True,
            timestamp__gte=timezone.now() - timedelta(hours=24)
        ).count()

        if recent_suspicious >= 3:
            SecurityAlert.objects.create(
                title=f"Multiple suspicious activities from {self.ip_address}",
                description=f"IP address {self.ip_address} has {recent_suspicious} suspicious activities in 24 hours.",
                alert_type='SUSPICIOUS_LOGIN',
                alert_level='HIGH',
                related_log=self
            )

    class Meta:
        verbose_name = "Access Log"
        verbose_name_plural = "Access Logs"
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['login_method', 'status']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['is_suspicious']),
            models.Index(fields=['confidence_score']),
        ]
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'


class SystemSettings(models.Model):
    DATA_TYPES = [
        ('string', 'String'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('json', 'JSON'),
    ]

    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    data_type = models.CharField(
        max_length=20, choices=DATA_TYPES, default='string')
    description = models.TextField(blank=True)
    is_public = models.BooleanField(default=False)
    is_encrypted = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True)

    def get_value(self):
        """Get the typed value"""
        if self.data_type == 'integer':
            return int(self.value)
        elif self.data_type == 'float':
            return float(self.value)
        elif self.data_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.data_type == 'json':
            try:
                return json.loads(self.value)
            except json.JSONDecodeError:
                return {}
        else:
            return self.value

    def set_value(self, value, user=None):
        """Set the value with proper type handling"""
        if self.data_type == 'json':
            self.value = json.dumps(value)
        else:
            self.value = str(value)

        if user:
            self.updated_by = user

        self.save()
        self.clear_cache()

    def clear_cache(self):
        """Clear cached settings"""
        cache.delete(f'system_setting_{self.key}')

    @classmethod
    def get_setting(cls, key, default=None):
        """Get a system setting with caching"""
        cache_key = f'system_setting_{key}'
        cached_value = cache.get(cache_key)

        if cached_value is not None:
            return cached_value

        try:
            setting = cls.objects.get(key=key)
            value = setting.get_value()
            cache.set(cache_key, value, 300)  # Cache for 5 minutes
            return value
        except cls.DoesNotExist:
            return default

    def __str__(self):
        return f"{self.key} = {self.value}"

    class Meta:
        verbose_name = "System Setting"
        verbose_name_plural = "System Settings"
        indexes = [
            models.Index(fields=['key']),
            models.Index(fields=['is_public']),
        ]


class SecurityAlert(models.Model):
    ALERT_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]

    ALERT_TYPES = [
        ('SUSPICIOUS_LOGIN', 'Suspicious Login'),
        ('MULTIPLE_FAILURES', 'Multiple Failures'),
        ('UNUSUAL_LOCATION', 'Unusual Location'),
        ('SYSTEM_SECURITY', 'System Security'),
        ('BIOMETRIC_ISSUE', 'Biometric Issue'),
        ('DATA_BREACH', 'Data Breach'),
        ('UNAUTHORIZED_ACCESS', 'Unauthorized Access'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    alert_level = models.CharField(max_length=10, choices=ALERT_LEVELS)

    # Related entities
    related_user = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_alerts')
    related_log = models.ForeignKey(
        AccessLog, on_delete=models.SET_NULL, null=True, blank=True, related_name='security_alerts')

    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_alerts')
    resolution_notes = models.TextField(blank=True)

    # Alert metadata
    created_at = models.DateTimeField(auto_now_add=True)
    acknowledged = models.BooleanField(default=False)
    acknowledged_at = models.DateTimeField(null=True, blank=True)
    acknowledged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='acknowledged_alerts')

    def __str__(self):
        return f"{self.alert_level}: {self.title}"

    def resolve(self, user, notes=""):
        """Resolve this alert"""
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = user
        self.resolution_notes = notes
        self.save()

    def acknowledge(self, user):
        """Acknowledge this alert"""
        self.acknowledged = True
        self.acknowledged_at = timezone.now()
        self.acknowledged_by = user
        self.save()

    def get_alert_color(self):
        """Get Bootstrap color class for alert level"""
        color_map = {
            'LOW': 'info',
            'MEDIUM': 'warning',
            'HIGH': 'danger',
            'CRITICAL': 'dark'
        }
        return color_map.get(self.alert_level, 'secondary')

    class Meta:
        verbose_name = "Security Alert"
        verbose_name_plural = "Security Alerts"
        indexes = [
            models.Index(fields=['alert_level']),
            models.Index(fields=['alert_type']),
            models.Index(fields=['is_resolved']),
            models.Index(fields=['created_at']),
            models.Index(fields=['acknowledged']),
        ]
        ordering = ['-created_at']


class FaceEncodingArchive(models.Model):
    """Archive for old face encodings for audit purposes"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='face_archives')
    face_encoding = models.TextField()  # Encrypted encoding
    encoding_version = models.CharField(max_length=10)
    quality_score = models.FloatField(null=True, blank=True)
    # Update, Corruption, etc.
    reason = models.CharField(max_length=100, default='Update')

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    archived_at = models.DateTimeField(default=timezone.now)
    archived_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='archived_encodings')

    def __str__(self):
        return f"{self.user.username} - {self.archived_at.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "Face Encoding Archive"
        verbose_name_plural = "Face Encoding Archives"
        indexes = [
            models.Index(fields=['user', 'archived_at']),
            models.Index(fields=['archived_at']),
        ]
        ordering = ['-archived_at']


class SystemHealth(models.Model):
    """System health monitoring data"""
    timestamp = models.DateTimeField(default=timezone.now)
    cpu_usage = models.FloatField()  # Percentage
    memory_usage = models.FloatField()  # Percentage
    disk_usage = models.FloatField()  # Percentage
    active_users = models.IntegerField()
    request_count = models.IntegerField()
    average_response_time = models.FloatField()  # milliseconds

    # Service status
    database_status = models.BooleanField(default=True)
    face_recognition_status = models.BooleanField(default=True)
    storage_status = models.BooleanField(default=True)

    # Security metrics
    failed_logins = models.IntegerField(default=0)
    security_alerts = models.IntegerField(default=0)

    def __str__(self):
        return f"System Health - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = "System Health"
        verbose_name_plural = "System Health Records"
        indexes = [
            models.Index(fields=['timestamp']),
        ]
        ordering = ['-timestamp']
        get_latest_by = 'timestamp'

# Signal handlers


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create user profile when a new user is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save user profile when user is saved"""
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=AccessLog)
def check_suspicious_activity(sender, instance, created, **kwargs):
    """Check for suspicious activity patterns"""
    if created and instance.status == 'Failed':
        # Check for multiple failures from same IP
        recent_failures = AccessLog.objects.filter(
            ip_address=instance.ip_address,
            status='Failed',
            timestamp__gte=timezone.now() - timedelta(minutes=30)
        ).count()

        if recent_failures >= 5:
            instance.mark_suspicious(
                f"Multiple failed attempts ({recent_failures}) in 30 minutes")

            # Create security alert
            SecurityAlert.objects.create(
                title=f"Brute force attempt detected from {instance.ip_address}",
                description=f"IP address {instance.ip_address} has {recent_failures} failed login attempts in 30 minutes.",
                alert_type='MULTIPLE_FAILURES',
                alert_level='HIGH',
                related_log=instance
            )

from django.db import models
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


class FaceVerificationSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username} - {self.session_id}"


class AccessLog(models.Model):
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

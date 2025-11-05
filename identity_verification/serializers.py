from rest_framework import serializers
from .models import FaceVerificationSession, AccessLog


class FaceVerificationSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = FaceVerificationSession
        fields = '__all__'


class AccessLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    security_number = serializers.CharField(
        source='user.security_number', read_only=True)

    class Meta:
        model = AccessLog
        fields = '__all__'

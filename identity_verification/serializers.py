from rest_framework import serializers
from .models import FaceVerificationSession, AccessLog


class FaceVerificationSessionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source='user.get_full_name', read_only=True)

    class Meta:
        model = FaceVerificationSession
        fields = '__all__'


class AccessLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(
        source='user.get_full_name', read_only=True)
    visitor_name = serializers.CharField(
        source='visitor.full_name', read_only=True)

    class Meta:
        model = AccessLog
        fields = '__all__'


class FaceVerificationRequestSerializer(serializers.Serializer):
    security_number = serializers.CharField(max_length=20)
    verification_type = serializers.ChoiceField(choices=['login', 'logout'])


class FaceCaptureSerializer(serializers.Serializer):
    session_id = serializers.CharField(max_length=100)
    image = serializers.CharField()

from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    recipient_name = serializers.CharField(
        source='recipient.get_full_name', read_only=True)
    visitor_name = serializers.CharField(
        source='related_visitor.full_name', read_only=True)

    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

from rest_framework import serializers
from .models import CustomUser, Visitor
from django.contrib.auth.password_validation import validate_password


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'first_name', 'last_name', 'email',
                  'user_type', 'security_number', 'phone_number', 'unit',
                  'is_verified', 'date_joined')
        read_only_fields = ('id', 'date_joined')


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'password', 'password_confirm', 'email',
                  'first_name', 'last_name', 'user_type', 'security_number',
                  'phone_number', 'unit')

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords don't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = CustomUser.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


class VisitorSerializer(serializers.ModelSerializer):
    host_member_name = serializers.CharField(
        source='host_member.get_full_name', read_only=True)
    created_by_name = serializers.CharField(
        source='created_by.get_full_name', read_only=True)

    class Meta:
        model = Visitor
        fields = '__all__'
        read_only_fields = ('visitor_id', 'created_at')

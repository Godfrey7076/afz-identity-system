from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, Visitor
from .serializers import UserSerializer, UserCreateSerializer, VisitorSerializer
import logging

logger = logging.getLogger(__name__)


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'commander':
            return CustomUser.objects.all()
        elif user.user_type == 'supervisor':
            return CustomUser.objects.filter(unit=user.unit)
        else:
            return CustomUser.objects.filter(id=user.id)

    def perform_create(self, serializer):
        user = serializer.save()
        # Send welcome email with security number
        try:
            send_mail(
                'Welcome to AFZ Identity Verification System',
                f'''Welcome to the Air Force of Zimbabwe Identity Verification System!

Your account has been created successfully.

Login Details:
Username: {user.username}
Security Number: {user.security_number}
Temporary Password: Use the password set by administrator

Please log in and change your password immediately.

System URL: http://localhost:8000/

Regards,
AFZ Security Team''',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=True,
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")

    @action(detail=False, methods=['post'], permission_classes=[permissions.AllowAny])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return Response({
                    'message': 'Login successful',
                    'user': UserSerializer(user).data,
                    'user_type': user.user_type
                })
            else:
                return Response({'error': 'Account is disabled'}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

    @action(detail=False, methods=['post'])
    def logout(self, request):
        logout(request)
        return Response({'message': 'Logout successful'})

    @action(detail=False, methods=['get'])
    def profile(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not user.check_password(old_password):
            return Response({'error': 'Wrong old password'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'message': 'Password updated successfully'})

    @action(detail=True, methods=['post'])
    def verify_user(self, request, pk=None):
        user = self.get_object()
        user.is_verified = True
        user.save()
        return Response({'message': 'User verified successfully'})


class VisitorViewSet(viewsets.ModelViewSet):
    queryset = Visitor.objects.all()
    serializer_class = VisitorSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['commander', 'supervisor']:
            return Visitor.objects.all()
        else:
            return Visitor.objects.filter(created_by=user)

    def perform_create(self, serializer):
        visitor = serializer.save(created_by=self.request.user)

        # Create notification for host member
        from notifications.models import Notification
        Notification.objects.create(
            recipient=visitor.host_member,
            notification_type='visitor_approval',
            title=f'Visitor Approval Required - {visitor.full_name}',
            message=f'Visitor {visitor.full_name} is waiting for approval. Purpose: {visitor.purpose_of_visit}',
            related_visitor=visitor,
            priority='high'
        )

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django.db.models import Count, Q
from django.contrib.auth import authenticate, login, logout
from datetime import datetime, timedelta
import json
from django.utils import timezone

from .models import FaceVerificationSession, AccessLog
from .serializers import FaceVerificationSessionSerializer, AccessLogSerializer
from .face_utils import face_system
from users.models import CustomUser, Visitor
import base64
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class RealTimeDataMixin:
    """Mixin for real-time data updates"""

    def get_real_time_stats(self):
        """Get real-time statistics"""
        now = timezone.now()
        today = now.date()
        hour_ago = now - timezone.timedelta(hours=1)

        return {
            'current_active_users': CustomUser.objects.filter(
                last_login__gte=hour_ago
            ).count(),
            'recent_logins': AccessLog.objects.filter(
                timestamp__gte=hour_ago
            ).count(),
            'system_uptime': '99.8%',
            'alerts_count': AccessLog.objects.filter(
                timestamp__gte=hour_ago,
                success=False
            ).count(),
        }


class FaceVerificationViewSet(viewsets.ViewSet):
    """ViewSet for handling face verification operations"""

    @action(detail=False, methods=['post'])
    def verify_face(self, request):
        """Verify face against stored encoding with enhanced logging"""
        try:
            security_number = request.data.get('security_number')
            image_data = request.data.get('image')

            if not security_number or not image_data:
                return Response({
                    'success': False,
                    'message': 'Security number and image are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get user by security number
            try:
                user = CustomUser.objects.get(security_number=security_number)
            except CustomUser.DoesNotExist:
                logger.warning(
                    f"Failed login attempt - User not found: {security_number}")
                return Response({
                    'success': False,
                    'message': 'Personnel not found in system'
                }, status=status.HTTP_404_NOT_FOUND)

            # Decode base64 image
            try:
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                image_data = base64.b64decode(image_data)
                nparr = np.frombuffer(image_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    return Response({
                        'success': False,
                        'message': 'Invalid image data received'
                    }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                logger.error(f"Image decoding error: {e}")
                return Response({
                    'success': False,
                    'message': 'Invalid image format'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if user has face registered
            if not user.face_encoding:
                logger.warning(
                    f"Face not registered for user: {user.username}")
                return Response({
                    'success': False,
                    'message': 'Biometric data not registered. Please contact administration.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Capture and encode face from current frame
            encoding, message = face_system.capture_and_encode_face(frame)

            if encoding is not None:
                # Verify against stored encoding
                is_match, distance = face_system.verify_face(
                    encoding, user.face_encoding)

                confidence = (1 - distance) * 100

                if is_match and distance < 0.6:  # Distance threshold
                    # Create access log
                    AccessLog.objects.create(
                        user=user,
                        verification_method='face',
                        success=True,
                        confidence_score=confidence
                    )

                    logger.info(
                        f"Successful face verification - User: {user.username}, Confidence: {confidence:.2f}%")

                    return Response({
                        'success': True,
                        'message': 'Biometric verification successful',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'security_number': user.security_number,
                            'unit': user.unit
                        },
                        'confidence': confidence
                    })
                else:
                    # Log failed attempt
                    AccessLog.objects.create(
                        user=user,
                        verification_method='face',
                        success=False,
                        confidence_score=confidence
                    )

                    logger.warning(
                        f"Failed face verification - User: {user.username}, Confidence: {confidence:.2f}%")

                    return Response({
                        'success': False,
                        'message': f'Biometric verification failed. Confidence: {confidence:.1f}%'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Face verification system error: {e}")
            return Response({
                'success': False,
                'message': 'System error. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def register_face(self, request):
        """Register a new face for a user with enhanced validation"""
        user_id = request.data.get('user_id')
        image_data = request.data.get('image')

        if not user_id or not image_data:
            return Response({
                'success': False,
                'message': 'User ID and image are required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(id=user_id)

            # Decode base64 image
            try:
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                image_data = base64.b64decode(image_data)
                nparr = np.frombuffer(image_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    return Response({
                        'success': False,
                        'message': 'Invalid image data'
                    }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                logger.error(f"Image decoding error during registration: {e}")
                return Response({
                    'success': False,
                    'message': 'Invalid image format'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Capture and encode face
            encoding, message = face_system.capture_and_encode_face(frame)

            if encoding is not None:
                # Convert encoding to string for storage
                encoding_str = ','.join(str(x) for x in encoding)
                user.face_encoding = encoding_str
                user.is_verified = True
                user.save()

                # Log the registration
                AccessLog.objects.create(
                    user=user,
                    verification_method='registration',
                    success=True,
                    confidence_score=1.0
                )

                logger.info(
                    f"Successfully registered face for user: {user.username}")

                return Response({
                    'success': True,
                    'message': 'Biometric data registered successfully',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'security_number': user.security_number
                    }
                })
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)

        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Personnel record not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Face registration system error: {e}")
            return Response({
                'success': False,
                'message': 'Registration system error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def check_registration(self, request):
        """Check if a user has face registered"""
        security_number = request.GET.get('security_number')

        if not security_number:
            return Response({
                'success': False,
                'message': 'Security number is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = CustomUser.objects.get(security_number=security_number)
            return Response({
                'success': True,
                'registered': bool(user.face_encoding),
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'security_number': user.security_number,
                    'unit': user.unit
                }
            })
        except CustomUser.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Personnel not found in system'
            }, status=status.HTTP_404_NOT_FOUND)


class AccessLogViewSet(viewsets.ModelViewSet):
    """ViewSet for accessing access logs"""
    queryset = AccessLog.objects.all().order_by('-timestamp')
    serializer_class = AccessLogSerializer

    def get_queryset(self):
        """Filter logs based on user permissions"""
        queryset = super().get_queryset()

        # If user is staff, show all logs
        if self.request.user.is_staff:
            return queryset

        # Otherwise, only show user's own logs
        return queryset.filter(user=self.request.user)


# Authentication Views
def admin_login_view(request):
    """Admin login view with enhanced security"""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            logger.info(f"Staff login successful: {user.username}")
            return redirect('dashboard')
        else:
            logger.warning(f"Failed staff login attempt: {username}")
            messages.error(
                request, 'Invalid credentials or insufficient permissions.')

    return render(request, 'login.html')


def admin_logout_view(request):
    """Admin logout view"""
    if request.user.is_authenticated:
        logger.info(f"Staff logout: {request.user.username}")
    logout(request)
    return redirect('admin_login')


# Dashboard Views
@method_decorator(login_required, name='dispatch')
class DashboardView(RealTimeDataMixin, TemplateView):
    template_name = 'dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(
                request, 'Access denied. Command staff permissions required.')
            return redirect('admin_login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Get date ranges
        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        hour_ago = timezone.now() - timedelta(hours=1)

        # Enhanced dashboard statistics
        total_face_logins = AccessLog.objects.filter(
            verification_method='face').count()
        successful_face_logins = AccessLog.objects.filter(
            verification_method='face', success=True).count()

        context.update({
            'total_users': CustomUser.objects.count(),
            'verified_users': CustomUser.objects.filter(is_verified=True).count(),
            'pending_verification': CustomUser.objects.filter(is_verified=False).count(),
            'today_logs': AccessLog.objects.filter(timestamp__date=today).count(),
            'weekly_logs': AccessLog.objects.filter(timestamp__date__gte=week_ago).count(),
            'monthly_logs': AccessLog.objects.filter(timestamp__date__gte=month_ago).count(),
            'hourly_logs': AccessLog.objects.filter(timestamp__gte=hour_ago).count(),
            'successful_logins': successful_face_logins,
            'failed_logins': AccessLog.objects.filter(verification_method='face', success=False).count(),
            'total_visitors': Visitor.objects.count(),
            'active_visitors': Visitor.objects.filter(status='active').count(),
            'pending_visitors': Visitor.objects.filter(status='pending').count(),
        })

        # Recent activity (last 15 entries)
        context['recent_activity'] = AccessLog.objects.select_related(
            'user').order_by('-timestamp')[:15]

        # User type breakdown
        context['user_types'] = CustomUser.objects.values('user_type').annotate(
            count=Count('user_type')
        ).order_by('-count')

        # Recent visitors
        context['recent_visitors'] = Visitor.objects.select_related(
            'host_member').order_by('-created_at')[:5]

        # Real-time data
        context.update(self.get_real_time_stats())

        # Enhanced success rate calculation
        if total_face_logins > 0:
            context['success_rate'] = round(
                (successful_face_logins / total_face_logins * 100), 1)
        else:
            context['success_rate'] = 0

        # System status
        context['system_status'] = 'operational'
        context['last_update'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')

        return context


@login_required
def user_management_view(request):
    """Enhanced user management page"""
    if not request.user.is_staff:
        messages.error(
            request, 'Access denied. Command staff permissions required.')
        return redirect('admin_login')

    users = CustomUser.objects.all().order_by('-date_joined')

    # Enhanced filtering
    user_type = request.GET.get('user_type', '')
    verified = request.GET.get('verified', '')
    search = request.GET.get('search', '')

    if user_type:
        users = users.filter(user_type=user_type)
    if verified:
        if verified == 'true':
            users = users.filter(is_verified=True)
        elif verified == 'false':
            users = users.filter(is_verified=False)
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(security_number__icontains=search) |
            Q(unit__icontains=search)
        )

    context = {
        'users': users,
        'user_types': CustomUser.USER_TYPES,
        'current_filters': {
            'user_type': user_type,
            'verified': verified,
            'search': search,
        }
    }
    return render(request, 'user_management.html', context)


@login_required
def visitor_management_view(request):
    """Enhanced visitor management page"""
    if not request.user.is_staff:
        messages.error(
            request, 'Access denied. Command staff permissions required.')
        return redirect('admin_login')

    visitors = Visitor.objects.all().order_by('-created_at')

    # Enhanced filtering
    status_filter = request.GET.get('status', '')
    host_filter = request.GET.get('host', '')
    search = request.GET.get('search', '')

    if status_filter:
        visitors = visitors.filter(status=status_filter)
    if host_filter:
        visitors = visitors.filter(
            host_member__username__icontains=host_filter)
    if search:
        visitors = visitors.filter(
            Q(full_name__icontains=search) |
            Q(visitor_id__icontains=search) |
            Q(id_number__icontains=search)
        )

    context = {
        'visitors': visitors,
        'status_choices': Visitor.VISITOR_STATUS,
        'current_filters': {
            'status': status_filter,
            'host': host_filter,
            'search': search,
        }
    }
    return render(request, 'visitor_management.html', context)


@staff_member_required
def admin_face_registration(request, user_id):
    """Enhanced admin view for face registration"""
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'admin/face_registration.html', {'user': user})


def face_login_view(request):
    """Enhanced face login interface"""
    return render(request, 'face_login.html')


def face_verification_status(request):
    """Check face verification status for a user"""
    security_number = request.GET.get('security_number')

    if not security_number:
        return JsonResponse({
            'success': False,
            'message': 'Security number is required'
        })

    try:
        user = CustomUser.objects.get(security_number=security_number)
        return JsonResponse({
            'success': True,
            'registered': bool(user.face_encoding),
            'username': user.username,
            'unit': user.unit
        })
    except CustomUser.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Personnel not found'
        })


# Real-time Data API
@method_decorator(login_required, name='dispatch')
class RealTimeDataView(RealTimeDataMixin, View):
    """API endpoint for real-time data"""

    def get(self, request):
        data = {
            'real_time_stats': self.get_real_time_stats(),
            'timestamp': timezone.now().isoformat(),
            'status': 'operational',
            'system_health': {
                'database': 'connected',
                'face_recognition': 'active',
                'webcam': 'available',
                'authentication': 'operational'
            }
        }
        return JsonResponse(data)


def api_info(request):
    """Provide enhanced API information"""
    info = {
        'system': 'Air Force Zimbabwe Identity Verification System',
        'version': '2.0.0',
        'description': 'Advanced biometric authentication and personnel management system',
        'endpoints': {
            'face_login': '/verification/login/',
            'face_verification': '/verification/api/verification/verify_face/',
            'face_registration': '/verification/api/verification/register_face/',
            'check_registration': '/verification/api/verification/check_registration/',
            'admin_registration': '/verification/admin/register-face/<user_id>/',
            'access_logs': '/verification/api/access-logs/',
            'dashboard': '/verification/dashboard/',
            'user_management': '/verification/user-management/',
            'visitor_management': '/verification/visitor-management/',
            'realtime_data': '/verification/api/realtime-data/',
        },
        'authentication_methods': [
            'Biometric Face Recognition',
            'Security Number Verification',
            'Staff Credentials'
        ],
        'security_features': [
            'Real-time face detection',
            'Biometric data encryption',
            'Access logging and monitoring',
            'Role-based access control'
        ]
    }
    return JsonResponse(info)

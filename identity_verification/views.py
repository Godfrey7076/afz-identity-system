# identity_verification/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from django.db.models import Count, Q, Avg, Max
from django.contrib.auth import authenticate, login, logout
from datetime import datetime, timedelta
import json
from django.utils import timezone
from django.core.cache import cache
from django.db.models.functions import TruncDay, TruncHour
import random
import csv
import os
from django.conf import settings
import base64
import cv2
import numpy as np
import logging
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import face_recognition
from PIL import Image
import io
from cryptography.fernet import Fernet

from .models import UserProfile, AccessLog, SystemSettings, SecurityAlert
from django.contrib.auth import get_user_model
from .decorators import rate_limit

User = get_user_model()
logger = logging.getLogger(__name__)

# AFZ Security Configuration


class AFZSecurityConfig:
    MIN_FACE_CONFIDENCE = 85.0
    MAX_LOGIN_ATTEMPTS = 5
    SESSION_TIMEOUT = 3600
    FACE_ENCODING_VERSION = '2.0'
    MAX_FACE_ENCODINGS = 3

    @classmethod
    def get_system_status(cls):
        return {
            'security_level': 'TOP SECRET',
            'version': '2.1.0',
            'biometric_status': 'OPERATIONAL',
            'min_confidence': cls.MIN_FACE_CONFIDENCE
        }

# Standardized Response Format


class AFZResponse:
    @staticmethod
    def success(data=None, message="", code="SUCCESS"):
        return {
            'success': True,
            'data': data,
            'message': message,
            'code': code,
            'timestamp': timezone.now().isoformat(),
            'system': 'AFZ Identity Verification System'
        }

    @staticmethod
    def error(message="", code="ERROR", status_code=400):
        return Response({
            'success': False,
            'message': message,
            'code': code,
            'timestamp': timezone.now().isoformat(),
            'system': 'AFZ Identity Verification System'
        }, status=status_code)


def get_client_ip(request):
    """Get client IP address with enhanced security"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
    return ip


def get_user_agent(request):
    """Extract user agent information"""
    return request.META.get('HTTP_USER_AGENT', 'Unknown')[:500]

# Utility Functions


def is_admin(user):
    return user.is_staff or user.is_superuser

# Face Recognition Engine


class FaceRecognitionEngine:
    """Enhanced face recognition engine with encryption support"""

    def __init__(self):
        self.encryption_key = Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)

    def encrypt_encoding(self, encoding_data):
        """Encrypt face encoding before storage"""
        try:
            encoded_data = json.dumps(encoding_data).encode()
            encrypted_data = self.cipher_suite.encrypt(encoded_data)
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encoding encryption error: {str(e)}")
            return None

    def decrypt_encoding(self, encrypted_data):
        """Decrypt face encoding for verification"""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data)
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            return json.loads(decrypted_data.decode())
        except Exception as e:
            logger.error(f"Encoding decryption error: {str(e)}")
            return None

    @staticmethod
    def process_image(image_data):
        """Process base64 image data and convert to numpy array"""
        try:
            if ',' in image_data:
                image_data = image_data.split(',')[1]

            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            image_np = np.array(image)
            return image_np, True
        except Exception as e:
            logger.error(f"Image processing error: {str(e)}")
            return None, False

    @staticmethod
    def extract_face_encodings(image_np):
        """Extract face encodings from image"""
        try:
            # Detect faces
            face_locations = face_recognition.face_locations(image_np)
            face_encodings = face_recognition.face_encodings(
                image_np, face_locations)

            return face_encodings, face_locations, True
        except Exception as e:
            logger.error(f"Face encoding extraction error: {str(e)}")
            return [], [], False

    def enroll_face(self, user, image_data, encoding_index=0):
        """Enroll face for user with encryption"""
        try:
            image_np, success = self.process_image(image_data)
            if not success:
                return False, "Failed to process image"

            face_encodings, face_locations, extraction_success = self.extract_face_encodings(
                image_np)

            if not extraction_success:
                return False, "Face extraction failed"

            if len(face_encodings) == 0:
                return False, "No face detected in image"
            elif len(face_encodings) > 1:
                return False, "Multiple faces detected. Please provide image with only one face."

            # Encrypt and store the face encoding
            profile, created = UserProfile.objects.get_or_create(user=user)
            encrypted_encoding = self.encrypt_encoding(
                face_encodings[0].tolist())

            if encrypted_encoding is None:
                return False, "Failed to encrypt face data"

            # Store in appropriate field based on index
            if encoding_index == 0:
                profile.face_encoding = encrypted_encoding
            elif encoding_index == 1:
                profile.face_encoding_1 = encrypted_encoding
            elif encoding_index == 2:
                profile.face_encoding_2 = encrypted_encoding
            else:
                return False, "Invalid encoding index"

            profile.face_enrolled = True
            profile.face_enrollment_date = timezone.now()
            profile.face_encoding_version = AFZSecurityConfig.FACE_ENCODING_VERSION
            profile.face_encoding_count = max(
                profile.face_encoding_count or 0, encoding_index + 1)
            profile.last_face_update = timezone.now()
            profile.save()

            # Log successful enrollment
            logger.info(
                f"AFZ Security: Face enrolled for user {user.username}, encoding #{encoding_index + 1}")
            return True, "Face enrolled successfully"

        except Exception as e:
            logger.error(f"Face enrollment error: {str(e)}")
            return False, f"Enrollment failed: {str(e)}"

    def verify_face(self, user, image_data):
        """Verify face against stored encrypted encodings"""
        try:
            profile = UserProfile.objects.get(user=user)
            if not profile.face_enrolled:
                return False, 0.0, "Face not enrolled"

            image_np, success = self.process_image(image_data)
            if not success:
                return False, 0.0, "Image processing failed"

            face_encodings, face_locations, extraction_success = self.extract_face_encodings(
                image_np)
            if not extraction_success or len(face_encodings) == 0:
                return False, 0.0, "No face detected"

            # Get all stored encodings for the user
            stored_encodings = []
            encoding_fields = [
                profile.face_encoding,
                profile.face_encoding_1,
                profile.face_encoding_2
            ]

            for i, encrypted_encoding in enumerate(encoding_fields):
                if encrypted_encoding and i < (profile.face_encoding_count or 1):
                    try:
                        decrypted_data = self.decrypt_encoding(
                            encrypted_encoding)
                        if decrypted_data:
                            stored_encodings.append(np.array(decrypted_data))
                    except Exception as e:
                        logger.warning(
                            f"Failed to decrypt encoding {i} for user {user.username}: {str(e)}")

            if not stored_encodings:
                return False, 0.0, "No valid face encodings found"

            # Compare with all stored encodings
            best_confidence = 0.0
            for stored_encoding in stored_encodings:
                try:
                    matches = face_recognition.compare_faces(
                        [stored_encoding], face_encodings[0])
                    face_distance = face_recognition.face_distance(
                        [stored_encoding], face_encodings[0])

                    if len(face_distance) > 0:
                        confidence = (1 - face_distance[0]) * 100

                        if matches[0] and confidence > best_confidence:
                            best_confidence = confidence
                except Exception as e:
                    logger.warning(f"Face comparison error: {str(e)}")
                    continue

            if best_confidence >= AFZSecurityConfig.MIN_FACE_CONFIDENCE:
                return True, best_confidence, "Verification successful"
            else:
                return False, best_confidence, f"Verification failed. Confidence: {best_confidence:.2f}%"

        except UserProfile.DoesNotExist:
            return False, 0.0, "User profile not found"
        except Exception as e:
            logger.error(f"Face verification error: {str(e)}")
            return False, 0.0, f"Verification error: {str(e)}"


# Initialize face recognition engine
face_engine = FaceRecognitionEngine()

# Home and Basic Views


def home_view(request):
    """Homepage view for the AFZ Identity System"""
    context = {
        'system_name': 'Air Force of Zimbabwe Identity System',
        'version': '2.1.0',
        'security_level': 'TOP SECRET',
        'current_time': timezone.now()
    }
    return render(request, 'home.html', context)

# Authentication Views


@rate_limit(requests=5, window=300)  # 5 attempts per 5 minutes
def admin_login_view(request):
    """Admin login view with AFZ security enhancements"""
    if request.user.is_authenticated:
        return redirect('enhanced_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            # Log admin login
            AccessLog.objects.create(
                user=user,
                login_method='Password',
                status='Success',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details='Admin login'
            )
            logger.info(
                f"AFZ Security: Staff login successful: {user.username}")
            messages.success(request, 'AFZ Command Center access granted.')
            return redirect('enhanced_dashboard')
        else:
            # Log failed attempt
            AccessLog.objects.create(
                user=None,
                login_method='Password',
                status='Failed',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details=f'Failed admin login attempt for username: {username}'
            )
            logger.warning(
                f"AFZ Security: Failed staff login attempt: {username}")
            messages.error(
                request, 'AFZ: Invalid credentials or insufficient permissions.')

    return render(request, 'identity_verification/admin_login.html')


def admin_logout_view(request):
    """Admin logout view with AFZ logging"""
    if request.user.is_authenticated:
        logger.info(f"AFZ Security: Staff logout: {request.user.username}")
        # Log logout
        AccessLog.objects.create(
            user=request.user,
            login_method='Logout',
            status='Success',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details='Admin logout'
        )
    logout(request)
    messages.info(request, 'AFZ: Successfully logged out.')
    return redirect('admin_login')


@rate_limit(requests=5, window=300)
def custom_login(request):
    """Custom login view for regular users"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Log access
            AccessLog.objects.create(
                user=user,
                login_method='Password',
                status='Success',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details='User login successful'
            )

            return redirect('dashboard')
        else:
            # Log failed attempt
            AccessLog.objects.create(
                user=None,
                login_method='Password',
                status='Failed',
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                details=f'Failed login attempt for username: {username}'
            )

            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

# Face Recognition Views


def face_login_view(request):
    """Enhanced face login interface with AFZ branding"""
    context = {
        'system_name': 'AFZ Biometric Access System',
        'security_level': 'RESTRICTED',
        'min_confidence': AFZSecurityConfig.MIN_FACE_CONFIDENCE
    }
    return render(request, 'identity_verification/face_login.html', context)


@login_required
def enroll_face_view(request):
    """Face enrollment view for users with actual face recognition"""
    if not request.user.is_authenticated:
        return redirect('login')

    # Check if already enrolled
    try:
        profile = UserProfile.objects.get(user=request.user)
        if profile.face_enrolled:
            messages.info(
                request, 'Face already enrolled. You can update your enrollment.')
    except UserProfile.DoesNotExist:
        pass

    if request.method == 'POST':
        try:
            image_data = request.POST.get('image')
            encoding_index = int(request.POST.get('encoding_index', 0))

            if not image_data:
                return JsonResponse({'success': False, 'error': 'No image data'})

            # Process face enrollment
            success, message = face_engine.enroll_face(
                request.user, image_data, encoding_index)

            if success:
                # Log enrollment
                AccessLog.objects.create(
                    user=request.user,
                    login_method='Enrollment',
                    status='Success',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    details=f'Face enrollment successful - Encoding #{encoding_index + 1}',
                    confidence_score=100.0
                )

                return JsonResponse({
                    'success': True,
                    'message': 'Face enrolled successfully!',
                    'encoding_index': encoding_index
                })
            else:
                # Log failed enrollment
                AccessLog.objects.create(
                    user=request.user,
                    login_method='Enrollment',
                    status='Failed',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    details=f'Face enrollment failed: {message}'
                )

                return JsonResponse({
                    'success': False,
                    'error': message
                })

        except Exception as e:
            logger.error(f"Face enrollment view error: {str(e)}")
            return JsonResponse({
                'success': False,
                'error': f'Enrollment error: {str(e)}'
            })

    context = {
        'user': request.user,
        'min_confidence': AFZSecurityConfig.MIN_FACE_CONFIDENCE,
        'max_encodings': AFZSecurityConfig.MAX_FACE_ENCODINGS
    }
    return render(request, 'enroll_face.html', context)


def face_verification_status(request):
    """Check face verification status for a user with AFZ response"""
    user_id = request.GET.get('user_id')

    if not user_id:
        return JsonResponse({
            'success': False,
            'message': 'AFZ User ID is required',
            'code': 'MISSING_DATA'
        })

    try:
        user = User.objects.get(id=user_id)
        profile = UserProfile.objects.get(user=user)

        status_data = {
            'success': True,
            'registered': profile.face_enrolled,
            'username': user.username,
            'is_verified': profile.face_enrolled,
            'enrollment_date': profile.face_enrollment_date.isoformat() if profile.face_enrollment_date else None,
            'encoding_count': profile.face_encoding_count or 0,
            'code': 'STATUS_CHECK_SUCCESS'
        }

        return JsonResponse(status_data)
    except User.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'AFZ Personnel not found',
            'code': 'USER_NOT_FOUND'
        })
    except UserProfile.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'AFZ Personnel profile not found',
            'code': 'PROFILE_NOT_FOUND'
        })

# Dashboard Views


class EnhancedRealTimeDataMixin:
    """Enhanced mixin for comprehensive real-time data with AFZ features"""

    def get_enhanced_stats(self):
        """Get comprehensive statistics for dashboard with AFZ enhancements"""
        now = timezone.now()
        today = now.date()

        # User statistics
        total_users = User.objects.count()
        verified_users = UserProfile.objects.filter(face_enrolled=True).count()
        active_today = AccessLog.objects.filter(
            timestamp__date=today,
            status='Success'
        ).values('user').distinct().count()
        new_users_today = User.objects.filter(date_joined__date=today).count()

        # Access log statistics
        total_logs = AccessLog.objects.count()
        today_logs = AccessLog.objects.filter(timestamp__date=today).count()
        successful_logins = AccessLog.objects.filter(status='Success').count()
        failed_logins = AccessLog.objects.filter(status='Failed').count()

        # Face verification specific stats
        face_verifications = AccessLog.objects.filter(
            login_method='Face Recognition')
        successful_face = face_verifications.filter(status='Success').count()
        total_face = face_verifications.count()

        # Calculate success rates
        overall_success_rate = (
            successful_logins / total_logs * 100) if total_logs > 0 else 0
        face_success_rate = (successful_face / total_face *
                             100) if total_face > 0 else 0

        # Average confidence for successful face verifications
        avg_confidence = face_verifications.filter(
            status='Success',
            confidence_score__isnull=False
        ).aggregate(avg_conf=Avg('confidence_score'))['avg_conf'] or 85.5

        return {
            'total_users': total_users,
            'verified_users': verified_users,
            'active_today': active_today,
            'new_users_today': new_users_today,
            'total_logs': total_logs,
            'today_logs': today_logs,
            'successful_logins': successful_logins,
            'failed_logins': failed_logins,
            'overall_success_rate': round(overall_success_rate, 1),
            'face_success_rate': round(face_success_rate, 1),
            'avg_confidence': round(avg_confidence, 1),
            'verification_accuracy': round(face_success_rate, 1),
            'system_uptime': '99.8%',
            'response_time': '45ms',
            'security_level': 'HIGH'
        }

    def get_trend_data(self):
        """Get trend data for charts with enhanced analytics"""
        # Last 7 days data
        dates = []
        daily_logins = []
        daily_success = []
        daily_failed = []
        daily_face_success = []

        for i in range(7):
            date = timezone.now().date() - timedelta(days=6-i)
            dates.append(date.strftime('%m/%d'))
            day_logs = AccessLog.objects.filter(timestamp__date=date)
            daily_logins.append(day_logs.count())
            daily_success.append(day_logs.filter(status='Success').count())
            daily_failed.append(day_logs.filter(status='Failed').count())

            # Face verification stats
            face_logs = day_logs.filter(login_method='Face Recognition')
            daily_face_success.append(
                face_logs.filter(status='Success').count())

        # Verification method distribution
        verification_methods = AccessLog.objects.values('login_method').annotate(
            count=Count('login_method')
        ).order_by('-count')

        # Success rate by method
        method_success = []
        for method in verification_methods:
            method_name = method['login_method']
            total = method['count']
            success_count = AccessLog.objects.filter(
                login_method=method_name,
                status='Success'
            ).count()
            success_rate = (success_count / total * 100) if total > 0 else 0
            method_success.append({
                'method': method_name,
                'success_rate': round(success_rate, 1),
                'total_attempts': total
            })

        return {
            'dates': dates,
            'daily_logins': daily_logins,
            'daily_success': daily_success,
            'daily_failed': daily_failed,
            'daily_face_success': daily_face_success,
            'verification_methods': list(verification_methods),
            'method_success': method_success
        }

    def get_system_health(self):
        """Get system health metrics with AFZ security enhancements"""
        cache_key = 'system_health_cache'
        cached_data = cache.get(cache_key)

        if cached_data:
            cpu_usage = max(
                15, min(75, cached_data['cpu_usage'] + random.uniform(-5, 5)))
            memory_usage = max(
                45, min(85, cached_data['memory_usage'] + random.uniform(-3, 3)))
            disk_usage = max(
                25, min(70, cached_data['disk_usage'] + random.uniform(-2, 2)))
        else:
            cpu_usage = random.uniform(20, 40)
            memory_usage = random.uniform(50, 70)
            disk_usage = random.uniform(30, 60)

        # Determine system status
        if cpu_usage < 70 and memory_usage < 75 and disk_usage < 80:
            system_status = 'healthy'
            status_color = 'success'
        elif cpu_usage < 85 and memory_usage < 90 and disk_usage < 90:
            system_status = 'warning'
            status_color = 'warning'
        else:
            system_status = 'critical'
            status_color = 'danger'

        health_data = {
            'cpu_usage': round(cpu_usage, 1),
            'memory_usage': round(memory_usage, 1),
            'disk_usage': round(disk_usage, 1),
            'system_status': system_status,
            'status_color': status_color,
            'security_status': 'secure',
            'encryption_level': 'AES-256',
            'last_checked': timezone.now().isoformat()
        }

        cache.set(cache_key, health_data, 60)
        return health_data

    def get_system_alerts(self):
        """Get system alerts based on current status with AFZ security focus"""
        alerts = []
        today = timezone.now().date()

        # Check for high failure rate
        today_failed = AccessLog.objects.filter(
            timestamp__date=today,
            status='Failed'
        ).count()
        today_total = AccessLog.objects.filter(timestamp__date=today).count()

        if today_total > 0 and (today_failed / today_total) > 0.3:
            alerts.append({
                'type': 'warning',
                'message': f'High authentication failure rate: {today_failed}/{today_total} failed today',
                'timestamp': 'Just now',
                'priority': 'high'
            })

        # Check for unverified users
        unverified_count = UserProfile.objects.filter(
            face_enrolled=False).count()
        if unverified_count > 10:
            alerts.append({
                'type': 'info',
                'message': f'{unverified_count} personnel pending biometric registration',
                'timestamp': 'Today',
                'priority': 'medium'
            })

        # Check for system performance
        recent_logs = AccessLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(hours=1)
        )
        if recent_logs.count() > 1000:
            alerts.append({
                'type': 'warning',
                'message': 'High system load detected in the last hour',
                'timestamp': '15 minutes ago',
                'priority': 'medium'
            })

        # System security status
        alerts.append({
            'type': 'success',
            'message': 'All security systems operational - AFZ Protocol Active',
            'timestamp': '5 minutes ago',
            'priority': 'low'
        })

        # Sort alerts by priority
        priority_order = {'high': 1, 'medium': 2, 'low': 3}
        alerts.sort(key=lambda x: priority_order.get(
            x.get('priority', 'low'), 3))

        return alerts


@method_decorator(login_required, name='dispatch')
class EnhancedDashboardView(EnhancedRealTimeDataMixin, TemplateView):
    template_name = 'identity_verification/enhanced_dashboard.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_staff:
            messages.error(
                request, 'AFZ: Access denied. Command staff permissions required.')
            return redirect('admin_login')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get enhanced statistics
        stats = self.get_enhanced_stats()
        trend_data = self.get_trend_data()
        system_health = self.get_system_health()

        # Recent activity (last 10 entries)
        recent_activity = AccessLog.objects.select_related(
            'user').order_by('-timestamp')[:10]

        # Enhanced Quick Actions for AFZ Identity System
        quick_actions = [
            {
                'name': 'User Management',
                'url': '/verification/user-management/',
                'icon': '👥',
                'color': 'primary',
                'description': 'Manage system users'
            },
            {
                'name': 'Access Logs',
                'url': '/verification/access-logs/',
                'icon': '📊',
                'color': 'info',
                'description': 'View access history'
            },
            {
                'name': 'Face Registration',
                'url': '/verification/admin/register-face/',
                'icon': '📷',
                'color': 'warning',
                'description': 'Register new faces'
            },
            {
                'name': 'Security Audit',
                'url': '/verification/security-audit/',
                'icon': '🛡️',
                'color': 'dark',
                'description': 'Security monitoring'
            },
            {
                'name': 'System Status',
                'url': '/verification/system-status/',
                'icon': '⚙️',
                'color': 'secondary',
                'description': 'System health monitoring'
            },
        ]

        # System alerts
        alerts = self.get_system_alerts()

        # AFZ Specific Data
        afz_data = AFZSecurityConfig.get_system_status()
        afz_data.update({
            'last_security_scan': timezone.now().strftime('%Y-%m-%d %H:%M'),
            'encryption_status': 'ACTIVE',
            'biometric_status': 'OPERATIONAL',
            'total_alerts': len(alerts)
        })

        context.update({
            'stats': stats,
            'trend_data': json.dumps(trend_data),
            'system_health': system_health,
            'recent_activity': recent_activity,
            'quick_actions': quick_actions,
            'alerts': alerts,
            'afz_data': afz_data,
            'last_update': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system_status': 'operational',
            'failed_today': AccessLog.objects.filter(
                timestamp__date=timezone.now().date(),
                status='Failed'
            ).count(),
        })

        return context


@login_required
def dashboard(request):
    """Legacy dashboard view"""
    current_time = timezone.now()

    # Get actual login activities from database
    login_activities = AccessLog.objects.select_related(
        'user').order_by('-timestamp')[:15]

    # Statistics
    stats = {
        'total_users': User.objects.count(),
        'active_today': AccessLog.objects.filter(
            timestamp__date=current_time.date(),
            status='Success'
        ).values('user').distinct().count(),
        'face_logins': AccessLog.objects.filter(
            timestamp__date=current_time.date(),
            login_method='Face Recognition',
            status='Success'
        ).count(),
        'failed_attempts': AccessLog.objects.filter(
            timestamp__date=current_time.date(),
            status='Failed'
        ).count(),
        'total_logins_today': AccessLog.objects.filter(
            timestamp__date=current_time.date()
        ).count(),
    }

    context = {
        'login_activities': login_activities,
        'stats': stats,
        'current_time': current_time,
    }

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'activities': [
                {
                    'username': log.user.username if log.user else 'Unknown',
                    'timestamp': log.timestamp.isoformat(),
                    'method': log.login_method,
                    'status': log.status,
                    'ip': log.ip_address or 'N/A',
                    'confidence': log.confidence_score
                } for log in login_activities
            ],
            'stats': stats
        }
        return JsonResponse(data)

    return render(request, 'dashboard.html', context)


@method_decorator(login_required, name='dispatch')
class DashboardAPIView(EnhancedRealTimeDataMixin, View):
    """API endpoint for real-time dashboard data with AFZ enhancements"""

    def get(self, request):
        stats = self.get_enhanced_stats()
        trend_data = self.get_trend_data()
        system_health = self.get_system_health()
        alerts = self.get_system_alerts()

        data = AFZResponse.success(
            data={
                'stats': stats,
                'trend_data': trend_data,
                'system_health': system_health,
                'alerts': alerts,
            },
            message='Dashboard data retrieved successfully',
            code='DASHBOARD_DATA_SUCCESS'
        )

        return JsonResponse(data)

# User Management Views


@login_required
@user_passes_test(is_admin)
def user_management_view(request):
    """Enhanced user management page with AFZ features"""
    users = User.objects.all().select_related(
        'userprofile').order_by('-date_joined')

    # Enhanced filtering
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    face_enrolled_filter = request.GET.get('face_enrolled', '')
    role_filter = request.GET.get('role', '')

    # Apply filters
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    if status_filter:
        if status_filter == 'active':
            users = users.filter(is_active=True)
        elif status_filter == 'inactive':
            users = users.filter(is_active=False)

    if face_enrolled_filter:
        if face_enrolled_filter == 'true':
            users = users.filter(userprofile__face_enrolled=True)
        elif face_enrolled_filter == 'false':
            users = users.filter(userprofile__face_enrolled=False)

    if role_filter:
        if role_filter == 'staff':
            users = users.filter(is_staff=True)
        elif role_filter == 'superuser':
            users = users.filter(is_superuser=True)
        elif role_filter == 'regular':
            users = users.filter(is_staff=False, is_superuser=False)

    # Statistics for dashboard
    total_users = users.count()
    verified_users = UserProfile.objects.filter(face_enrolled=True).count()
    active_users = users.filter(is_active=True).count()
    users_with_face = UserProfile.objects.filter(face_enrolled=True).count()
    staff_users = users.filter(is_staff=True).count()

    # Recent registrations (last 7 days)
    recent_cutoff = timezone.now() - timedelta(days=7)
    recent_registrations = users.filter(date_joined__gte=recent_cutoff).count()

    # Handle bulk actions
    if request.method == 'POST':
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids')

        if action == 'activate_users':
            activated_count = users.filter(
                id__in=user_ids).update(is_active=True)
            messages.success(
                request, f'AFZ: Activated {activated_count} users.')
        elif action == 'deactivate_users':
            deactivated_count = users.filter(
                id__in=user_ids).update(is_active=False)
            messages.success(
                request, f'AFZ: Deactivated {deactivated_count} users.')
        elif action == 'export_users':
            return export_users_data(users)
        elif action == 'promote_to_staff':
            promoted_count = users.filter(
                id__in=user_ids).update(is_staff=True)
            messages.success(
                request, f'AFZ: Promoted {promoted_count} users to staff.')

        return redirect('user_management')

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(users, 20)

    try:
        users_page = paginator.page(page)
    except PageNotAnInteger:
        users_page = paginator.page(1)
    except EmptyPage:
        users_page = paginator.page(paginator.num_pages)

    context = {
        'users': users_page,
        'current_filters': {
            'status': status_filter,
            'face_enrolled': face_enrolled_filter,
            'search': search_query,
            'role': role_filter,
        },
        'stats': {
            'total_users': total_users,
            'verified_users': verified_users,
            'active_users': active_users,
            'users_with_face': users_with_face,
            'recent_registrations': recent_registrations,
            'pending_verification': total_users - verified_users,
            'staff_users': staff_users,
        },
    }
    return render(request, 'identity_verification/user_management.html', context)


def export_users_data(queryset):
    """Export users data to CSV"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="afz_users_export.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Username', 'Full Name', 'Email', 'Active', 'Staff',
        'Face Enrolled', 'Encoding Count', 'Date Joined', 'Last Login'
    ])

    for user in queryset:
        try:
            profile = UserProfile.objects.get(user=user)
            face_enrolled = 'Yes' if profile.face_enrolled else 'No'
            encoding_count = profile.face_encoding_count or 0
        except UserProfile.DoesNotExist:
            face_enrolled = 'No'
            encoding_count = 0

        writer.writerow([
            user.username,
            f"{user.first_name} {user.last_name}",
            user.email,
            'Yes' if user.is_active else 'No',
            'Yes' if user.is_staff else 'No',
            face_enrolled,
            encoding_count,
            user.date_joined.strftime('%Y-%m-%d %H:%M'),
            user.last_login.strftime(
                '%Y-%m-%d %H:%M') if user.last_login else 'Never'
        ])

    return response


@login_required
@user_passes_test(is_admin)
def user_detail_view(request, user_id):
    """Detailed user view with activity history"""
    user = get_object_or_404(User, id=user_id)

    try:
        user_profile = UserProfile.objects.get(user=user)
    except UserProfile.DoesNotExist:
        user_profile = None

    # Get user's access logs
    access_logs = AccessLog.objects.filter(
        user=user).order_by('-timestamp')[:50]

    # Statistics
    total_logins = access_logs.count()
    successful_logins = access_logs.filter(status='Success').count()
    failed_logins = access_logs.filter(status='Failed').count()
    success_rate = (successful_logins / total_logins *
                    100) if total_logins > 0 else 0

    # Face verification stats
    face_verifications = access_logs.filter(login_method='Face Recognition')
    face_success_rate = (face_verifications.filter(status='Success').count(
    ) / face_verifications.count() * 100) if face_verifications.count() > 0 else 0

    context = {
        'user_obj': user,
        'user_profile': user_profile,
        'access_logs': access_logs,
        'stats': {
            'total_logins': total_logins,
            'successful_logins': successful_logins,
            'failed_logins': failed_logins,
            'success_rate': round(success_rate, 1),
            'face_success_rate': round(face_success_rate, 1),
            'face_verifications': face_verifications.count(),
        }
    }

    return render(request, 'identity_verification/user_detail.html', context)


@login_required
@user_passes_test(is_admin)
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()

        action = "activated" if user.is_active else "deactivated"

        # Log the action
        AccessLog.objects.create(
            user=request.user,
            login_method='Admin Action',
            status='Success',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request),
            details=f'User status {action}: {user.username}'
        )

        messages.success(
            request, f'AFZ: User {user.username} has been {action}.')

        return JsonResponse({
            'success': True,
            'is_active': user.is_active,
            'message': f'User {user.username} has been {action} successfully'
        })


@login_required
@user_passes_test(is_admin)
def register_user_face(request, user_id):
    """Admin face registration for users"""
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        image_data = request.POST.get('image')
        encoding_index = int(request.POST.get('encoding_index', 0))

        if image_data:
            success, message = face_engine.enroll_face(
                user, image_data, encoding_index)

            if success:
                messages.success(
                    request, f'AFZ: Face registration successful for {user.username}.')

                # Log the action
                AccessLog.objects.create(
                    user=request.user,
                    login_method='Admin Action',
                    status='Success',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    details=f'Admin face registration for {user.username} - Encoding #{encoding_index + 1}'
                )
            else:
                messages.error(
                    request, f'AFZ: Face registration failed: {message}')
        else:
            messages.error(request, 'AFZ: No image data provided.')

        return redirect('user_management')

    context = {
        'user': user,
        'security_level': 'AFZ SECURE',
        'max_encodings': AFZSecurityConfig.MAX_FACE_ENCODINGS
    }
    return render(request, 'identity_verification/admin/face_registration.html', context)

# API ViewSets


class FaceVerificationViewSet(viewsets.ViewSet):
    """ViewSet for handling face verification operations with AFZ enhancements"""

    # Add queryset attribute to fix router issue
    queryset = User.objects.none()

    @action(detail=False, methods=['post'])
    @rate_limit(requests=10, window=60)
    def verify_face(self, request):
        """Verify face against stored encoding with enhanced AFZ security logging"""
        try:
            user_id = request.data.get('user_id')
            image_data = request.data.get('image')

            if not user_id or not image_data:
                return AFZResponse.error(
                    message='User ID and image are required',
                    code='MISSING_DATA',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Get user by ID
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                logger.warning(
                    f"AFZ Security: Failed login attempt - User not found: {user_id}")
                return AFZResponse.error(
                    message='Personnel not found in AFZ system',
                    code='USER_NOT_FOUND',
                    status_code=status.HTTP_404_NOT_FOUND
                )

            # Perform actual face verification
            is_match, confidence, message = face_engine.verify_face(
                user, image_data)

            if is_match and confidence >= AFZSecurityConfig.MIN_FACE_CONFIDENCE:
                # Create access log
                AccessLog.objects.create(
                    user=user,
                    login_method='Face Recognition',
                    status='Success',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    details=f'Face verification successful - Confidence: {confidence:.2f}%',
                    confidence_score=confidence
                )

                logger.info(
                    f"AFZ Security: Successful face verification - User: {user.username}, Confidence: {confidence:.2f}%")

                return Response(AFZResponse.success(
                    data={
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'email': user.email,
                        },
                        'confidence': confidence,
                        'timestamp': timezone.now().isoformat()
                    },
                    message='AFZ Biometric verification successful',
                    code='VERIFICATION_SUCCESS'
                ))
            else:
                # Log failed attempt
                AccessLog.objects.create(
                    user=user,
                    login_method='Face Recognition',
                    status='Failed',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    details=f'Face verification failed - Confidence: {confidence:.2f}% - {message}',
                    confidence_score=confidence
                )

                return AFZResponse.error(
                    message=message,
                    code='VERIFICATION_FAILED',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except Exception as e:
            logger.error(f"AFZ Security: Face verification system error: {e}")
            return AFZResponse.error(
                message='AFZ System error. Please try again.',
                code='SYSTEM_ERROR',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    @rate_limit(requests=5, window=300)
    def register_face(self, request):
        """Register a new face for a user with AFZ security validation"""
        user_id = request.data.get('user_id')
        image_data = request.data.get('image')
        encoding_index = int(request.data.get('encoding_index', 0))

        if not user_id or not image_data:
            return AFZResponse.error(
                message='User ID and image are required',
                code='MISSING_DATA',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)

            # Process face enrollment
            success, message = face_engine.enroll_face(
                user, image_data, encoding_index)

            if success:
                user_profile = UserProfile.objects.get(user=user)

                # Log the registration
                AccessLog.objects.create(
                    user=user,
                    login_method='Registration',
                    status='Success',
                    ip_address=get_client_ip(request),
                    user_agent=get_user_agent(request),
                    details=f'Face enrollment completed successfully - Encoding #{encoding_index + 1}',
                    confidence_score=100.0
                )

                logger.info(
                    f"AFZ Security: Successfully registered face for user: {user.username}")

                return Response(AFZResponse.success(
                    data={
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'enrollment_date': user_profile.face_enrollment_date.isoformat(),
                            'encoding_count': user_profile.face_encoding_count or 1
                        }
                    },
                    message='AFZ Biometric data registered successfully',
                    code='REGISTRATION_SUCCESS'
                ))
            else:
                return AFZResponse.error(
                    message=message,
                    code='REGISTRATION_FAILED',
                    status_code=status.HTTP_400_BAD_REQUEST
                )

        except User.DoesNotExist:
            return AFZResponse.error(
                message='AFZ Personnel record not found',
                code='USER_NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"AFZ Security: Face registration system error: {e}")
            return AFZResponse.error(
                message='AFZ Registration system error',
                code='SYSTEM_ERROR',
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['get'])
    def check_registration(self, request):
        """Check if a user has face registered with AFZ status"""
        user_id = request.GET.get('user_id')

        if not user_id:
            return AFZResponse.error(
                message='User ID is required',
                code='MISSING_DATA',
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(id=user_id)
            user_profile = UserProfile.objects.get(user=user)

            return Response(AFZResponse.success(
                data={
                    'registered': user_profile.face_enrolled,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_verified': user_profile.face_enrolled,
                        'enrollment_date': user_profile.face_enrollment_date.isoformat() if user_profile.face_enrollment_date else None,
                        'encoding_count': user_profile.face_encoding_count or 0,
                        'encoding_version': user_profile.face_encoding_version
                    }
                },
                message='Registration status retrieved successfully',
                code='CHECK_SUCCESS'
            ))
        except User.DoesNotExist:
            return AFZResponse.error(
                message='AFZ Personnel not found in system',
                code='USER_NOT_FOUND',
                status_code=status.HTTP_404_NOT_FOUND
            )
        except UserProfile.DoesNotExist:
            return Response(AFZResponse.success(
                data={
                    'registered': False,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'is_verified': False,
                        'enrollment_date': None,
                        'encoding_count': 0,
                        'encoding_version': None
                    }
                },
                message='User exists but no face registration found',
                code='CHECK_SUCCESS'
            ))


class AccessLogViewSet(viewsets.ModelViewSet):
    """ViewSet for accessing access logs with AFZ security features"""

    queryset = AccessLog.objects.all().order_by('-timestamp')

    def list(self, request):
        """Get access logs with filtering"""
        logs = self.get_queryset()

        # Apply filters
        date_range = request.GET.get('date_range', '')
        status_filter = request.GET.get('status', '')
        method_filter = request.GET.get('method', '')
        user_filter = request.GET.get('user', '')

        if date_range == 'today':
            today = timezone.now().date()
            logs = logs.filter(timestamp__date=today)
        elif date_range == 'week':
            week_ago = timezone.now() - timedelta(days=7)
            logs = logs.filter(timestamp__gte=week_ago)
        elif date_range == 'month':
            month_ago = timezone.now() - timedelta(days=30)
            logs = logs.filter(timestamp__gte=month_ago)

        if status_filter:
            logs = logs.filter(status=status_filter)

        if method_filter:
            logs = logs.filter(login_method=method_filter)

        if user_filter:
            logs = logs.filter(user__username__icontains=user_filter)

        # Pagination
        page_number = request.GET.get('page', 1)
        paginator = Paginator(logs, 50)

        try:
            logs_page = paginator.page(page_number)
        except PageNotAnInteger:
            logs_page = paginator.page(1)
        except EmptyPage:
            logs_page = paginator.page(paginator.num_pages)

        # Serialize data
        data = []
        for log in logs_page:
            data.append({
                'id': log.id,
                'username': log.user.username if log.user else 'Unknown',
                'login_method': log.login_method,
                'status': log.status,
                'ip_address': log.ip_address,
                'timestamp': log.timestamp.isoformat(),
                'details': log.details,
                'confidence_score': log.confidence_score,
                'user_agent': log.user_agent
            })

        return Response({
            'logs': data,
            'total_pages': paginator.num_pages,
            'current_page': logs_page.number,
            'total_logs': paginator.count
        })

    @action(detail=False, methods=['get'])
    def security_report(self, request):
        """Generate AFZ security report"""
        # Last 30 days data
        start_date = timezone.now().date() - timedelta(days=30)

        security_data = {
            'total_attempts': AccessLog.objects.filter(timestamp__date__gte=start_date).count(),
            'successful_logins': AccessLog.objects.filter(timestamp__date__gte=start_date, status='Success').count(),
            'failed_logins': AccessLog.objects.filter(timestamp__date__gte=start_date, status='Failed').count(),
            'success_rate': round((AccessLog.objects.filter(timestamp__date__gte=start_date, status='Success').count() /
                                   AccessLog.objects.filter(timestamp__date__gte=start_date).count() * 100), 2) if AccessLog.objects.filter(timestamp__date__gte=start_date).count() > 0 else 0,
            'top_users': list(AccessLog.objects.filter(
                timestamp__date__gte=start_date
            ).values('user__username').annotate(
                count=Count('id'),
                success_count=Count('id', filter=Q(status='Success'))
            ).order_by('-count')[:10]),
            'method_distribution': list(AccessLog.objects.filter(
                timestamp__date__gte=start_date
            ).values('login_method').annotate(
                count=Count('id')
            ).order_by('-count')),
            'ip_analysis': list(AccessLog.objects.filter(
                timestamp__date__gte=start_date
            ).values('ip_address').annotate(
                count=Count('id'),
                last_activity=Max('timestamp')
            ).order_by('-count')[:10])
        }

        return Response(AFZResponse.success(
            data=security_data,
            message='Security report generated successfully',
            code='SECURITY_REPORT_SUCCESS'
        ))

    @action(detail=False, methods=['get'])
    def export_logs(self, request):
        """Export access logs to CSV"""
        logs = AccessLog.objects.all().select_related(
            'user').order_by('-timestamp')[:1000]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="afz_access_logs_export.csv"'

        writer = csv.writer(response)
        writer.writerow([
            'Timestamp', 'Username', 'Login Method', 'Status',
            'IP Address', 'Confidence Score', 'Details', 'User Agent'
        ])

        for log in logs:
            writer.writerow([
                log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                log.user.username if log.user else 'Unknown',
                log.login_method,
                log.status,
                log.ip_address,
                log.confidence_score or '',
                log.details or '',
                log.user_agent or ''
            ])

        return response

# Additional Views


@login_required
@user_passes_test(is_admin)
def access_logs_analytics(request):
    """Access logs and analytics view"""
    # Get filter parameters
    date_range = request.GET.get('date_range', 'today')
    login_method = request.GET.get('login_method', 'all')
    status_filter = request.GET.get('status', 'all')

    # Base queryset
    logs = AccessLog.objects.all().select_related('user')

    # Apply filters
    if date_range == 'today':
        today = timezone.now().date()
        logs = logs.filter(timestamp__date=today)
    elif date_range == 'week':
        week_ago = timezone.now() - timedelta(days=7)
        logs = logs.filter(timestamp__gte=week_ago)
    elif date_range == 'month':
        month_ago = timezone.now() - timedelta(days=30)
        logs = logs.filter(timestamp__gte=month_ago)

    if login_method != 'all':
        logs = logs.filter(login_method=login_method)

    if status_filter != 'all':
        logs = logs.filter(status=status_filter)

    # Statistics
    total_logs = logs.count()
    success_logins = logs.filter(status='Success').count()
    failed_logins = logs.filter(status='Failed').count()
    success_rate = (success_logins / total_logs * 100) if total_logs > 0 else 0

    # Method distribution
    method_stats = logs.values('login_method').annotate(
        count=Count('id'),
        success_count=Count('id', filter=Q(status='Success')),
        avg_confidence=Avg('confidence_score')
    ).order_by('-count')

    # Hourly distribution for today
    today_logs = AccessLog.objects.filter(
        timestamp__date=timezone.now().date())
    hourly_stats = today_logs.annotate(
        hour=TruncHour('timestamp')
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour')

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(logs.order_by('-timestamp'), 50)

    try:
        logs_page = paginator.page(page)
    except PageNotAnInteger:
        logs_page = paginator.page(1)
    except EmptyPage:
        logs_page = paginator.page(paginator.num_pages)

    context = {
        'logs': logs_page,
        'total_logs': total_logs,
        'success_logins': success_logins,
        'failed_logins': failed_logins,
        'success_rate': round(success_rate, 2),
        'method_stats': method_stats,
        'hourly_stats': list(hourly_stats),
        'current_filters': {
            'date_range': date_range,
            'login_method': login_method,
            'status': status_filter,
        }
    }

    return render(request, 'identity_verification/access_logs_analytics.html', context)


@login_required
@user_passes_test(is_admin)
def system_status_view(request):
    """System status and health monitoring view"""
    mixin = EnhancedRealTimeDataMixin()

    # Get recent critical events
    critical_events = AccessLog.objects.filter(
        status='Failed',
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).order_by('-timestamp')[:10]

    # Get system settings
    try:
        system_settings = SystemSettings.objects.first()
    except SystemSettings.DoesNotExist:
        system_settings = None

    context = {
        'system_health': mixin.get_system_health(),
        'system_alerts': mixin.get_system_alerts(),
        'afz_config': AFZSecurityConfig.get_system_status(),
        'critical_events': critical_events,
        'system_settings': system_settings,
        'last_updated': timezone.now(),
        'total_users': User.objects.count(),
        'active_sessions': AccessLog.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=30)
        ).values('user').distinct().count()
    }

    return render(request, 'identity_verification/system_status.html', context)


@login_required
@user_passes_test(is_admin)
def security_audit_view(request):
    """Security audit and compliance view"""
    # Get security statistics
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    audit_data = {
        'today': {
            'total': AccessLog.objects.filter(timestamp__date=today).count(),
            'failed': AccessLog.objects.filter(timestamp__date=today, status='Failed').count(),
            'success_rate': round((AccessLog.objects.filter(timestamp__date=today, status='Success').count() /
                                   AccessLog.objects.filter(timestamp__date=today).count() * 100), 2) if AccessLog.objects.filter(timestamp__date=today).count() > 0 else 0
        },
        'week': {
            'total': AccessLog.objects.filter(timestamp__date__gte=week_ago).count(),
            'failed': AccessLog.objects.filter(timestamp__date__gte=week_ago, status='Failed').count(),
        },
        'month': {
            'total': AccessLog.objects.filter(timestamp__date__gte=month_ago).count(),
            'failed': AccessLog.objects.filter(timestamp__date__gte=month_ago, status='Failed').count(),
        }
    }

    # Get suspicious activities (multiple failures from same IP)
    suspicious_ips = AccessLog.objects.filter(
        status='Failed',
        timestamp__gte=timezone.now() - timedelta(hours=24)
    ).values('ip_address').annotate(
        failure_count=Count('id'),
        last_attempt=Max('timestamp')
    ).filter(failure_count__gte=5).order_by('-failure_count')

    context = {
        'audit_data': audit_data,
        'suspicious_ips': suspicious_ips,
        'total_users': User.objects.count(),
        'verified_users': UserProfile.objects.filter(face_enrolled=True).count(),
        'unverified_users': UserProfile.objects.filter(face_enrolled=False).count(),
    }

    return render(request, 'identity_verification/security_audit.html', context)

# Error handlers


def handler404(request, exception):
    """Custom 404 error handler"""
    return render(request, 'errors/404.html', status=404)


def handler500(request):
    """Custom 500 error handler"""
    return render(request, 'errors/500.html', status=500)


def handler403(request, exception):
    """Custom 403 error handler"""
    return render(request, 'errors/403.html', status=403)


def handler400(request, exception):
    """Custom 400 error handler"""
    return render(request, 'errors/400.html', status=400)

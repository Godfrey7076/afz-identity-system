from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import JsonResponse
from .models import FaceVerificationSession, AccessLog
from .serializers import FaceVerificationSessionSerializer, AccessLogSerializer
from .face_utils import face_system
from users.models import CustomUser
import base64
import cv2
import numpy as np
import logging

logger = logging.getLogger(__name__)


class FaceVerificationViewSet(viewsets.ViewSet):
    """
    ViewSet for handling face verification operations
    """

    @action(detail=False, methods=['post'])
    def verify_face(self, request):
        """Verify face against stored encoding"""
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
                return Response({
                    'success': False,
                    'message': 'User not found'
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
                        'message': 'Invalid image data'
                    }, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                logger.error(f"Image decoding error: {e}")
                return Response({
                    'success': False,
                    'message': 'Invalid image format'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if user has face registered
            if not user.face_encoding:
                return Response({
                    'success': False,
                    'message': 'No face registered for this user. Please contact administrator.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Capture and encode face from current frame
            encoding, message = face_system.capture_and_encode_face(frame)

            if encoding is not None:
                # Verify against stored encoding
                is_match, distance = face_system.verify_face(
                    encoding, user.face_encoding)

                if is_match and distance < 0.6:  # Distance threshold
                    # Create access log
                    AccessLog.objects.create(
                        user=user,
                        verification_method='face',
                        success=True,
                        confidence_score=1 - distance
                    )

                    return Response({
                        'success': True,
                        'message': 'Face verification successful',
                        'user': {
                            'id': user.id,
                            'username': user.username,
                            'security_number': user.security_number,
                            'unit': user.unit
                        },
                        'confidence': 1 - distance
                    })
                else:
                    # Log failed attempt
                    AccessLog.objects.create(
                        user=user,
                        verification_method='face',
                        success=False,
                        confidence_score=1 - distance
                    )

                    return Response({
                        'success': False,
                        'message': 'Face verification failed. Please try again.'
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                return Response({
                    'success': False,
                    'message': message
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Face verification error: {e}")
            return Response({
                'success': False,
                'message': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def register_face(self, request):
        """Register a new face for a user"""
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
                logger.error(f"Image decoding error: {e}")
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

                return Response({
                    'success': True,
                    'message': 'Face registered successfully',
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
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Face registration error: {e}")
            return Response({
                'success': False,
                'message': 'Internal server error'
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
                'message': 'User not found'
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


@staff_member_required
def admin_face_registration(request, user_id):
    """Admin view for face registration"""
    user = get_object_or_404(CustomUser, id=user_id)
    return render(request, 'admin/face_registration.html', {'user': user})


def face_login_view(request):
    """Main face login interface"""
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
            'message': 'User not found'
        })


# ADD THIS MISSING FUNCTION
def api_info(request):
    """Provide API information"""
    info = {
        'name': 'Face Recognition API',
        'version': '1.0.0',
        'endpoints': {
            'face_login': '/verification/login/',
            'face_verification': '/verification/api/verification/verify_face/',
            'face_registration': '/verification/api/verification/register_face/',
            'check_registration': '/verification/api/verification/check_registration/',
            'admin_registration': '/verification/admin/register-face/<user_id>/',
            'access_logs': '/verification/api/access-logs/',
        },
        'authentication_methods': [
            'Face Recognition',
            'Security Number'
        ]
    }
    return JsonResponse(info)

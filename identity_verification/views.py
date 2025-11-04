import json
import base64
import cv2
import numpy as np
from django.http import JsonResponse
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import FaceVerificationSession, AccessLog
from .serializers import (
    FaceVerificationSessionSerializer,
    AccessLogSerializer,
    FaceVerificationRequestSerializer,
    FaceCaptureSerializer
)
from .face_utils import face_system
from users.models import CustomUser
import logging

logger = logging.getLogger(__name__)


class FaceVerificationViewSet(viewsets.ViewSet):

    @action(detail=False, methods=['post'], permission_classes=[])
    def start_verification(self, request):
        serializer = FaceVerificationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        security_number = serializer.validated_data['security_number']
        verification_type = serializer.validated_data['verification_type']

        try:
            user = CustomUser.objects.get(security_number=security_number)

            # Create verification session
            session = FaceVerificationSession.objects.create(
                user=user,
                security_number=security_number,
                verification_type=verification_type
            )

            # Load face encodings if not already loaded
            if not face_system.known_face_encodings:
                users_with_faces = CustomUser.objects.exclude(face_encoding='')
                face_system.load_user_face_encodings(users_with_faces)

            return Response({
                'session_id': str(session.session_id),
                'message': 'Face verification session started. Please look at the camera.',
                'user': user.username
            })
        except CustomUser.DoesNotExist:
            return Response({'error': 'Invalid security number'}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[])
    def verify_face(self, request):
        serializer = FaceCaptureSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = serializer.validated_data['session_id']
        image_data = serializer.validated_data['image']

        try:
            session = FaceVerificationSession.objects.get(
                session_id=session_id)

            if session.status != 'pending':
                return Response({'error': 'Session already completed'}, status=status.HTTP_400_BAD_REQUEST)

            # Decode base64 image
            try:
                if ',' in image_data:
                    image_data = image_data.split(',')[1]
                image_data = base64.b64decode(image_data)
                nparr = np.frombuffer(image_data, np.uint8)
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

                if frame is None:
                    return Response({'error': 'Invalid image data'}, status=status.HTTP_400_BAD_REQUEST)

            except Exception as e:
                logger.error(f"Image decoding error: {e}")
                return Response({'error': 'Invalid image format'}, status=status.HTTP_400_BAD_REQUEST)

            # Verify face
            is_verified, message, confidence = face_system.verify_face(
                frame, session.user)

            if is_verified:
                session.status = 'success'
                session.confidence_score = confidence
                session.save()

                # Log access
                AccessLog.objects.create(
                    user=session.user,
                    action=session.verification_type,
                    verified_by_face=True,
                    location='Webcam Station'
                )

                return Response({
                    'verified': True,
                    'message': message,
                    'user': session.user.username,
                    'user_type': session.user.user_type,
                    'confidence': confidence
                })
            else:
                session.status = 'failed'
                session.confidence_score = confidence
                session.save()
                return Response({
                    'verified': False,
                    'message': message,
                    'confidence': confidence
                }, status=status.HTTP_400_BAD_REQUEST)

        except FaceVerificationSession.DoesNotExist:
            return Response({'error': 'Invalid session'}, status=status.HTTP_400_BAD_REQUEST)


class AccessLogViewSet(viewsets.ModelViewSet):
    queryset = AccessLog.objects.all().order_by('-timestamp')
    serializer_class = AccessLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.user_type in ['commander', 'supervisor']:
            return AccessLog.objects.all()
        else:
            return AccessLog.objects.filter(user=user)

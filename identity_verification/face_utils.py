import face_recognition
import cv2
import numpy as np
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import os
import logging

logger = logging.getLogger(__name__)


class FaceRecognitionSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_users = []
        self.watermark_path = os.path.join('static', 'images', 'watermark.png')

    def load_user_face_encodings(self, users):
        """Load face encodings from user database"""
        self.known_face_encodings = []
        self.known_face_users = []

        for user in users:
            if user.face_encoding and user.face_encoding.strip():
                try:
                    encoding = np.fromstring(user.face_encoding, sep=',')
                    self.known_face_encodings.append(encoding)
                    self.known_face_users.append(user)
                    logger.info(
                        f"Loaded face encoding for user: {user.username}")
                except Exception as e:
                    logger.error(
                        f"Error loading face encoding for user {user.username}: {e}")

    def add_watermark(self, image):
        """Add Air Force Zimbabwe watermark to image"""
        try:
            if os.path.exists(self.watermark_path):
                watermark = Image.open(self.watermark_path)

                # Convert OpenCV image to PIL if needed
                if isinstance(image, np.ndarray):
                    image = Image.fromarray(
                        cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

                # Resize watermark to 10% of image width
                watermark_size = int(image.width * 0.1)
                watermark = watermark.resize(
                    (watermark_size, watermark_size), Image.LANCZOS)

                # Create transparent layer for watermark
                transparent = Image.new('RGBA', image.size, (0, 0, 0, 0))

                # Position watermark in bottom right corner
                position = (image.width - watermark_size - 10,
                            image.height - watermark_size - 10)
                transparent.paste(watermark, position, watermark)

                # Convert base image to RGBA and composite with watermark
                image_rgba = image.convert('RGBA')
                result = Image.alpha_composite(image_rgba, transparent)

                return cv2.cvtColor(np.array(result), cv2.COLOR_RGBA2BGR)
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")

        return image

    def verify_face(self, frame, user):
        """Verify if face matches the user"""
        try:
            # Convert frame to RGB
            rgb_frame = frame[:, :, ::-1]

            # Find all face locations and encodings
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_frame, face_locations)

            if not face_encodings:
                return False, "No face detected", 0.0

            if not user.face_encoding or not user.face_encoding.strip():
                return False, "No face data registered for user", 0.0

            # Compare with user's face encoding
            user_encoding = np.fromstring(user.face_encoding, sep=',')

            matches = face_recognition.compare_faces(
                [user_encoding], face_encodings[0], tolerance=0.6)
            face_distance = face_recognition.face_distance(
                [user_encoding], face_encodings[0])

            confidence = (1 - face_distance[0]) * 100

            if matches[0] and confidence > 60:  # 60% confidence threshold
                return True, f"Face verified successfully (Confidence: {confidence:.2f}%)", confidence
            else:
                return False, f"Face verification failed (Confidence: {confidence:.2f}%)", confidence

        except Exception as e:
            logger.error(f"Face verification error: {e}")
            return False, f"Verification error: {str(e)}", 0.0

    def capture_and_encode_face(self, frame):
        """Capture face and return encoding"""
        try:
            rgb_frame = frame[:, :, ::-1]
            face_locations = face_recognition.face_locations(rgb_frame)
            face_encodings = face_recognition.face_encodings(
                rgb_frame, face_locations)

            if face_encodings:
                return face_encodings[0], "Face captured successfully"
            else:
                return None, "No face detected"
        except Exception as e:
            logger.error(f"Face capture error: {e}")
            return None, f"Capture error: {str(e)}"

    def register_new_face(self, frame, user):
        """Register new face for user"""
        try:
            encoding, message = self.capture_and_encode_face(frame)
            if encoding is not None:
                # Convert encoding to string for storage
                encoding_str = ','.join(str(x) for x in encoding)
                user.face_encoding = encoding_str
                user.is_verified = True
                user.save()
                return True, "Face registered successfully"
            else:
                return False, message
        except Exception as e:
            logger.error(f"Face registration error: {e}")
            return False, f"Registration error: {str(e)}"


# Global instance
face_system = FaceRecognitionSystem()

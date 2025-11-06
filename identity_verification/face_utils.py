import face_recognition
import cv2
import numpy as np
import base64
from PIL import Image, ImageDraw, ImageFont
import io
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class FaceRecognitionSystem:
    def __init__(self):
        self.known_face_encodings = []
        self.known_face_users = []
        self.watermark_path = os.path.join('static', 'images', 'watermark.png')
        self.face_detection_model = "hog"  # or "cnn" for better accuracy

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
                        f"Loaded face encoding for personnel: {user.username}")
                except Exception as e:
                    logger.error(
                        f"Error loading face encoding for personnel {user.username}: {e}")

    def capture_and_encode_face(self, frame):
        """Capture face and return encoding with enhanced validation"""
        try:
            # Convert frame to RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Find all face locations and encodings with enhanced detection
            face_locations = face_recognition.face_locations(
                rgb_frame,
                model=self.face_detection_model,
                number_of_times_to_upsample=1
            )
            face_encodings = face_recognition.face_encodings(
                rgb_frame, face_locations)

            if not face_encodings:
                return None, "No face detected. Please ensure face is clearly visible with good lighting."

            if len(face_encodings) > 1:
                return None, "Multiple faces detected. Please ensure only one person is in frame."

            # Validate face quality
            face_quality = self._validate_face_quality(
                frame, face_locations[0])
            if not face_quality["valid"]:
                return None, face_quality["message"]

            # Return the first face encoding
            return face_encodings[0], "Face captured successfully"

        except Exception as e:
            logger.error(f"Face capture system error: {e}")
            return None, f"Face capture system error: {str(e)}"

    def _validate_face_quality(self, frame, face_location):
        """Validate face quality for better recognition"""
        try:
            top, right, bottom, left = face_location
            face_height = bottom - top
            face_width = right - left

            # Check face size
            if face_height < 100 or face_width < 100:
                return {
                    "valid": False,
                    "message": "Face too small. Please move closer to the camera."
                }

            # Check face aspect ratio
            aspect_ratio = face_width / face_height
            if aspect_ratio < 0.6 or aspect_ratio > 1.4:
                return {
                    "valid": False,
                    "message": "Please face the camera directly for better recognition."
                }

            # Check brightness (simple check)
            face_region = frame[top:bottom, left:right]
            gray_face = cv2.cvtColor(face_region, cv2.COLOR_BGR2GRAY)
            brightness = np.mean(gray_face)

            if brightness < 50:
                return {
                    "valid": False,
                    "message": "Low lighting detected. Please improve lighting conditions."
                }
            elif brightness > 200:
                return {
                    "valid": False,
                    "message": "Too much brightness. Please adjust lighting."
                }

            return {"valid": True, "message": "Face quality acceptable"}

        except Exception as e:
            logger.error(f"Face quality validation error: {e}")
            # Continue anyway
            return {"valid": True, "message": "Quality check skipped"}

    def verify_face(self, unknown_encoding, user_face_encoding):
        """Enhanced face verification with confidence scoring"""
        try:
            if user_face_encoding:
                # Convert stored encoding back to numpy array
                stored_encoding = np.fromstring(user_face_encoding, sep=',')

                # Compare faces with enhanced tolerance
                results = face_recognition.compare_faces(
                    [stored_encoding],
                    unknown_encoding,
                    tolerance=0.55  # Slightly stricter tolerance
                )
                distance = face_recognition.face_distance(
                    [stored_encoding], unknown_encoding)

                confidence = (1 - distance[0]) * 100

                # Enhanced matching logic
                if results[0] and confidence >= 65:  # 65% confidence threshold
                    return True, distance[0], confidence
                else:
                    return False, distance[0], confidence
            return False, 1.0, 0.0
        except Exception as e:
            logger.error(f"Face verification system error: {e}")
            return False, 1.0, 0.0

    def draw_face_landmarks(self, frame, face_locations):
        """Draw enhanced real-time face landmarks on frame"""
        try:
            for (top, right, bottom, left) in face_locations:
                # Draw enhanced rectangle around face
                cv2.rectangle(frame, (left, top),
                              (right, bottom), (0, 102, 204), 3)

                # Draw face area indicator with enhanced styling
                face_width = right - left
                face_height = bottom - top

                # Quality indicators
                if face_width > 120 and face_height > 120:
                    status_color = (0, 255, 0)  # Green - excellent
                    status_text = "✓ Optimal"
                elif face_width > 90 and face_height > 90:
                    status_color = (0, 165, 255)  # Orange - acceptable
                    status_text = "✓ Good"
                else:
                    status_color = (0, 0, 255)  # Red - poor
                    status_text = "✗ Move Closer"

                # Draw enhanced status indicator
                cv2.putText(frame, status_text, (left, top - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)

                # Draw confidence circle
                center_x = left + face_width // 2
                center_y = top - 20
                cv2.circle(frame, (center_x, center_y), 8, status_color, -1)

            return frame
        except Exception as e:
            logger.error(f"Face landmarks drawing error: {e}")
            return frame

    def process_frame_for_display(self, frame):
        """Process frame for real-time display with enhanced features"""
        try:
            # Convert to RGB for face recognition
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Detect faces
            face_locations = face_recognition.face_locations(
                rgb_frame, model="hog")

            # Draw enhanced landmarks
            processed_frame = self.draw_face_landmarks(frame, face_locations)

            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(processed_frame, timestamp, (10, processed_frame.shape[0] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            return processed_frame, len(face_locations)

        except Exception as e:
            logger.error(f"Frame processing error: {e}")
            return frame, 0

    def get_face_detection_status(self, frame):
        """Get detailed face detection status"""
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(
                rgb_frame, model="hog")

            if not face_locations:
                return {
                    "faces_detected": 0,
                    "status": "no_face",
                    "message": "No face detected. Please position face in frame."
                }
            elif len(face_locations) > 1:
                return {
                    "faces_detected": len(face_locations),
                    "status": "multiple_faces",
                    "message": "Multiple faces detected. Please ensure only one person is visible."
                }
            else:
                # Analyze the first face
                top, right, bottom, left = face_locations[0]
                face_width = right - left
                face_height = bottom - top

                if face_width > 120 and face_height > 120:
                    status = "optimal"
                    message = "Face detected - Optimal position"
                elif face_width > 90 and face_height > 90:
                    status = "good"
                    message = "Face detected - Good position"
                else:
                    status = "too_small"
                    message = "Face detected - Please move closer"

                return {
                    "faces_detected": 1,
                    "status": status,
                    "message": message,
                    "face_size": {
                        "width": face_width,
                        "height": face_height
                    }
                }

        except Exception as e:
            logger.error(f"Face detection status error: {e}")
            return {
                "faces_detected": 0,
                "status": "error",
                "message": "Detection system error"
            }


# Global instance
face_system = FaceRecognitionSystem()

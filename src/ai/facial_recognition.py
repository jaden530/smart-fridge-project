# src/ai/facial_recognition.py

import face_recognition
import cv2
import numpy as np
import pickle
import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    """Represents a registered user with face encodings."""
    id: int
    name: str
    face_encodings: List[np.ndarray]
    preferences: Dict
    last_seen: Optional[datetime] = None
    times_recognized: int = 0


class FacialRecognitionManager:
    """
    Manages facial recognition for user identification.
    Recognizes users approaching the fridge and loads their preferences.
    """

    def __init__(self, encodings_file: str = "face_encodings.pkl", tolerance: float = 0.6):
        """
        Initialize facial recognition system.

        Args:
            encodings_file: Path to store face encodings
            tolerance: Face matching tolerance (lower = stricter, 0.6 = default)
        """
        self.encodings_file = encodings_file
        self.tolerance = tolerance
        self.known_users: Dict[int, User] = {}
        self.load_encodings()

        print("👤 Facial Recognition Manager initialized")

    def load_encodings(self):
        """Load saved face encodings from disk."""
        if os.path.exists(self.encodings_file):
            try:
                with open(self.encodings_file, 'rb') as f:
                    self.known_users = pickle.load(f)
                print(f"✅ Loaded {len(self.known_users)} user(s) from {self.encodings_file}")
            except Exception as e:
                print(f"⚠️  Error loading encodings: {e}")
                self.known_users = {}
        else:
            print("📝 No existing encodings found, starting fresh")
            self.known_users = {}

    def save_encodings(self):
        """Save face encodings to disk."""
        try:
            with open(self.encodings_file, 'wb') as f:
                pickle.dump(self.known_users, f)
            print(f"💾 Saved {len(self.known_users)} user encodings")
        except Exception as e:
            print(f"❌ Error saving encodings: {e}")

    def enroll_user(
        self,
        user_id: int,
        name: str,
        image: np.ndarray,
        preferences: Dict = None
    ) -> bool:
        """
        Enroll a new user by capturing their face.

        Args:
            user_id: Unique user ID
            name: User's name
            image: Image containing the user's face
            preferences: User preferences (dietary restrictions, goals, etc.)

        Returns:
            True if enrollment successful
        """
        # Convert BGR (OpenCV) to RGB (face_recognition)
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect faces in image
        face_locations = face_recognition.face_locations(rgb_image)

        if len(face_locations) == 0:
            print("❌ No face detected in image")
            return False

        if len(face_locations) > 1:
            print("⚠️  Multiple faces detected, using first face")

        # Get face encoding
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if not face_encodings:
            print("❌ Could not encode face")
            return False

        # Create user entry
        user = User(
            id=user_id,
            name=name,
            face_encodings=[face_encodings[0]],
            preferences=preferences or {},
            last_seen=datetime.now(),
            times_recognized=0
        )

        self.known_users[user_id] = user
        self.save_encodings()

        print(f"✅ Enrolled user: {name} (ID: {user_id})")
        return True

    def add_face_sample(self, user_id: int, image: np.ndarray) -> bool:
        """
        Add additional face sample for existing user (improves accuracy).

        Args:
            user_id: User ID to add sample for
            image: Image containing user's face

        Returns:
            True if sample added successfully
        """
        if user_id not in self.known_users:
            print(f"❌ User ID {user_id} not found")
            return False

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)

        if not face_locations:
            print("❌ No face detected")
            return False

        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if not face_encodings:
            print("❌ Could not encode face")
            return False

        # Add encoding to user
        self.known_users[user_id].face_encodings.append(face_encodings[0])
        self.save_encodings()

        user_name = self.known_users[user_id].name
        total_samples = len(self.known_users[user_id].face_encodings)
        print(f"✅ Added face sample for {user_name} (total: {total_samples})")

        return True

    def recognize_user(self, image: np.ndarray) -> Optional[Tuple[User, float, Tuple[int, int, int, int]]]:
        """
        Recognize user from image.

        Args:
            image: Image captured from camera

        Returns:
            Tuple of (User, confidence, face_location) or None if no match
            confidence is 0.0-1.0 (1.0 = perfect match)
        """
        if not self.known_users:
            print("⚠️  No enrolled users to recognize")
            return None

        # Convert BGR to RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # Detect faces
        face_locations = face_recognition.face_locations(rgb_image)

        if not face_locations:
            return None

        # Get encodings for detected faces
        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)

        if not face_encodings:
            return None

        # Try to match first detected face
        test_encoding = face_encodings[0]
        face_location = face_locations[0]

        best_match_user = None
        best_distance = 1.0  # Lower is better (0.0 = perfect match)

        # Compare against all known users
        for user_id, user in self.known_users.items():
            for known_encoding in user.face_encodings:
                # Calculate face distance
                distance = face_recognition.face_distance([known_encoding], test_encoding)[0]

                if distance < best_distance and distance <= self.tolerance:
                    best_distance = distance
                    best_match_user = user

        if best_match_user:
            # Update user stats
            best_match_user.last_seen = datetime.now()
            best_match_user.times_recognized += 1
            self.save_encodings()

            # Convert distance to confidence (0.0 = no match, 1.0 = perfect)
            confidence = 1.0 - best_distance

            print(f"✅ Recognized: {best_match_user.name} (confidence: {confidence:.2%})")

            return (best_match_user, confidence, face_location)

        print("❌ No matching user found")
        return None

    def recognize_multiple_users(self, image: np.ndarray) -> List[Tuple[User, float, Tuple]]:
        """
        Recognize multiple users in a single image.

        Args:
            image: Image captured from camera

        Returns:
            List of (User, confidence, face_location) tuples
        """
        if not self.known_users:
            return []

        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_image)

        if not face_locations:
            return []

        face_encodings = face_recognition.face_encodings(rgb_image, face_locations)
        results = []

        for face_encoding, face_location in zip(face_encodings, face_locations):
            best_match_user = None
            best_distance = 1.0

            for user_id, user in self.known_users.items():
                for known_encoding in user.face_encodings:
                    distance = face_recognition.face_distance([known_encoding], face_encoding)[0]

                    if distance < best_distance and distance <= self.tolerance:
                        best_distance = distance
                        best_match_user = user

            if best_match_user:
                best_match_user.last_seen = datetime.now()
                best_match_user.times_recognized += 1

                confidence = 1.0 - best_distance
                results.append((best_match_user, confidence, face_location))

        if results:
            self.save_encodings()
            names = ", ".join([user.name for user, _, _ in results])
            print(f"✅ Recognized {len(results)} user(s): {names}")

        return results

    def draw_recognition_results(
        self,
        image: np.ndarray,
        results: List[Tuple[User, float, Tuple]]
    ) -> np.ndarray:
        """
        Draw bounding boxes and names on image.

        Args:
            image: Original image
            results: Recognition results from recognize_multiple_users()

        Returns:
            Annotated image
        """
        annotated = image.copy()

        for user, confidence, (top, right, bottom, left) in results:
            # Draw box
            cv2.rectangle(annotated, (left, top), (right, bottom), (0, 255, 0), 2)

            # Draw label
            label = f"{user.name} ({confidence:.0%})"
            cv2.rectangle(
                annotated,
                (left, bottom - 35),
                (right, bottom),
                (0, 255, 0),
                cv2.FILLED
            )
            cv2.putText(
                annotated,
                label,
                (left + 6, bottom - 6),
                cv2.FONT_HERSHEY_DUPLEX,
                0.6,
                (255, 255, 255),
                1
            )

        return annotated

    def remove_user(self, user_id: int) -> bool:
        """
        Remove a user from the system.

        Args:
            user_id: ID of user to remove

        Returns:
            True if removed successfully
        """
        if user_id in self.known_users:
            user_name = self.known_users[user_id].name
            del self.known_users[user_id]
            self.save_encodings()
            print(f"🗑️  Removed user: {user_name} (ID: {user_id})")
            return True

        print(f"❌ User ID {user_id} not found")
        return False

    def update_user_preferences(self, user_id: int, preferences: Dict) -> bool:
        """
        Update user preferences.

        Args:
            user_id: User ID
            preferences: New preferences dict

        Returns:
            True if updated
        """
        if user_id not in self.known_users:
            print(f"❌ User ID {user_id} not found")
            return False

        self.known_users[user_id].preferences.update(preferences)
        self.save_encodings()

        print(f"✅ Updated preferences for {self.known_users[user_id].name}")
        return True

    def get_user_stats(self) -> Dict:
        """Get statistics about enrolled users."""
        return {
            'total_users': len(self.known_users),
            'users': [
                {
                    'id': user.id,
                    'name': user.name,
                    'samples': len(user.face_encodings),
                    'last_seen': user.last_seen.isoformat() if user.last_seen else None,
                    'times_recognized': user.times_recognized
                }
                for user in self.known_users.values()
            ]
        }

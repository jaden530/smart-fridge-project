# src/core/smart_fridge_controller.py

"""
SMART FRIDGE MAIN CONTROLLER
============================
This is the central brain that coordinates all components.

EASY TO FIND MARKERS:
- [CAMERAS]: Camera setup and configuration
- [DOOR]: Door sensor events
- [FACE]: Facial recognition logic
- [AVATAR]: Avatar responses and animations
- [DETECTION]: Object detection and inventory
- [USER]: User interaction and confirmation
"""

import cv2
import os
import time
from datetime import datetime
from typing import Optional, Dict, List, Any

# Import all our components
from camera.multi_camera_manager import MultiCameraManager, CameraZone
from hardware.door_sensor import DoorSensorManager
from ai.facial_recognition import FacialRecognitionManager
from ai.image_comparator import ImageComparator
from ui.avatar_manager import AvatarManager
from inventory.inventory_manager import InventoryManager

# TODO: Replace with YOLOv12 when ready
from ai.object_detection import ObjectDetector


class SmartFridgeController:
    """
    Main controller that orchestrates all smart fridge components.

    This class ties together:
    - Camera system (2-13 cameras)
    - Door sensor (GPIO or simulated)
    - Facial recognition (identify users)
    - Object detection (YOLOv12)
    - Avatar (animated assistant)
    - Inventory management
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Smart Fridge system.

        Args:
            config: Configuration dictionary with camera indices, etc.
        """
        print("🚀 Initializing Smart Fridge Controller...")
        print("=" * 60)

        self.config = config or {}
        self.current_user = None
        self.before_images = {}
        self.after_images = {}

        # [CAMERAS] Initialize camera system
        print("\n📹 Setting up cameras...")
        self.camera_manager = MultiCameraManager()
        self._setup_cameras()

        # [DOOR] Initialize door sensor (simulation mode on desktop)
        print("\n🚪 Setting up door sensor...")
        self.door_sensor = DoorSensorManager()
        self._setup_door_callbacks()

        # [FACE] Initialize facial recognition
        print("\n👤 Setting up facial recognition...")
        self.face_recognizer = FacialRecognitionManager()

        # [AVATAR] Initialize animated avatar
        print("\n🤖 Setting up avatar...")
        self.avatar = AvatarManager()

        # [DETECTION] Initialize object detector (YOLOv12 ready)
        print("\n🔍 Setting up object detection...")
        self.object_detector = self._setup_object_detector()

        # Image comparison for before/after
        print("\n🖼️  Setting up image comparison...")
        self.image_comparator = ImageComparator()

        # Inventory manager
        print("\n📦 Setting up inventory manager...")
        self.inventory_manager = InventoryManager()

        # State tracking
        self.is_door_open = False
        self.session_start = None

        print("\n✅ Smart Fridge Controller initialized!")
        print("=" * 60)

    # ========================================================================
    # [CAMERAS] CAMERA SETUP
    # ========================================================================

    def _setup_cameras(self):
        """
        Setup cameras based on what's available.

        For desktop testing with 2 webcams:
        - Camera 0: External (facial recognition)
        - Camera 1: Internal (food detection)

        For production with 13 cameras:
        - Camera 0: External face
        - Camera 1: Overhead
        - Cameras 2-12: Shelf zones
        """
        # Get camera indices from config (defaults for desktop testing)
        face_camera = self.config.get('face_camera_index', 0)
        food_camera = self.config.get('food_camera_index', 1)

        print(f"   Adding external camera (index {face_camera})...")
        self.camera_manager.add_camera(
            CameraZone.EXTERNAL_FACE,
            face_camera,
            resolution=(1280, 720)
        )

        print(f"   Adding food detection camera (index {food_camera})...")
        self.camera_manager.add_camera(
            CameraZone.SHELF_1_LEFT,
            food_camera,
            resolution=(1280, 720)
        )

        # TODO: When you have more cameras, add them here:
        # self.camera_manager.add_camera(CameraZone.OVERHEAD, 2)
        # self.camera_manager.add_camera(CameraZone.SHELF_1_RIGHT, 3)
        # etc...

        print("   ✅ Cameras configured!")

    def _setup_object_detector(self):
        """
        Setup object detector.

        NOTE: Currently using YOLOv3 for testing.
        TODO: Replace with YOLOv12 (see instructions below)
        """
        # Check if YOLOv3 models exist
        model_dir = os.path.join(os.getcwd(), 'model_data')
        weights_path = os.path.join(model_dir, "yolov3.weights")
        config_path = os.path.join(model_dir, "yolov3.cfg")
        classes_path = os.path.join(model_dir, "coco.names")

        if not os.path.exists(weights_path):
            print("   ⚠️  YOLOv3 models not found - object detection disabled")
            print("   Run setup script to download models")
            return None

        try:
            detector = ObjectDetector(weights_path, config_path, classes_path)
            print("   ✅ Object detector loaded (YOLOv3 - temporary)")
            print("   📝 TODO: Upgrade to YOLOv12 for better accuracy")
            return detector
        except Exception as e:
            print(f"   ❌ Error loading detector: {e}")
            return None

    # ========================================================================
    # [DOOR] DOOR SENSOR CALLBACKS
    # ========================================================================

    def _setup_door_callbacks(self):
        """
        Register callbacks for door open/close events.

        Flow:
        1. Door opens → Capture "before" snapshots
        2. Door closes → Capture "after" snapshots → Compare → Update inventory
        """
        self.door_sensor.register_open_callback(self.on_door_open)
        self.door_sensor.register_close_callback(self.on_door_close)
        print("   ✅ Door callbacks registered!")

    def on_door_open(self, timestamp: datetime):
        """
        [DOOR] Called when door opens.

        Actions:
        1. Capture "before" images from all cameras
        2. Start overhead camera monitoring (if available)
        3. Mark session start
        """
        print(f"\n🚪 DOOR OPENED at {timestamp.strftime('%H:%M:%S')}")

        self.is_door_open = True
        self.session_start = timestamp

        # Capture "before" state
        print("📸 Capturing BEFORE snapshots...")
        self.before_images = self.camera_manager.capture_before_snapshot()
        print(f"   ✅ Captured {len(self.before_images)} images")

        # TODO: Start overhead monitoring when you have that camera
        # self.camera_manager.start_overhead_monitoring()

    def on_door_close(self, timestamp: datetime):
        """
        [DOOR] Called when door closes.

        Actions:
        1. Capture "after" images
        2. Compare before/after to detect changes
        3. Run object detection on changed regions
        4. Update inventory
        5. Avatar confirms changes
        """
        print(f"\n🚪 DOOR CLOSED at {timestamp.strftime('%H:%M:%S')}")

        self.is_door_open = False
        session_duration = (timestamp - self.session_start).total_seconds()

        # Capture "after" state
        print("📸 Capturing AFTER snapshots...")
        self.after_images = self.camera_manager.capture_after_snapshot()
        print(f"   ✅ Captured {len(self.after_images)} images")

        # Compare images to detect changes
        print("\n🔍 Analyzing changes...")
        self._analyze_and_update_inventory()

        print(f"\n✅ Session complete (duration: {session_duration:.1f}s)")

    # ========================================================================
    # [FACE] FACIAL RECOGNITION
    # ========================================================================

    def detect_user(self) -> Optional[Dict]:
        """
        [FACE] Detect and identify user from external camera.

        Returns:
            Dict with user info and avatar greeting, or None if no user detected
        """
        print("\n👤 Detecting user...")

        # Capture from external camera
        face_image = self.camera_manager.capture_facial_recognition()

        if face_image is None:
            print("   ❌ No image from facial recognition camera")
            return None

        # Try to recognize user
        result = self.face_recognizer.recognize_user(face_image)

        if result is None:
            print("   ❓ No recognized user - showing as guest")
            # [AVATAR] Greet guest
            avatar_state = self.avatar.greet_user("Guest", self._get_time_of_day())
            return {
                'user': None,
                'is_guest': True,
                'avatar_state': avatar_state
            }

        user, confidence, face_location = result

        print(f"   ✅ Recognized: {user.name} ({confidence:.0%} confidence)")

        # [AVATAR] Greet recognized user
        avatar_state = self.avatar.greet_user(user.name, self._get_time_of_day())

        # Store current user
        self.current_user = user

        return {
            'user': user,
            'confidence': confidence,
            'is_guest': False,
            'avatar_state': avatar_state
        }

    def enroll_new_user(self, name: str, preferences: Dict = None) -> bool:
        """
        [FACE] Enroll a new user with facial recognition.

        Args:
            name: User's name
            preferences: Dietary preferences, goals, etc.

        Returns:
            True if enrollment successful
        """
        print(f"\n👤 Enrolling new user: {name}")
        print("   📸 Please look at the camera...")

        # Capture from external camera
        face_image = self.camera_manager.capture_facial_recognition()

        if face_image is None:
            print("   ❌ No image captured")
            return False

        # Generate user ID
        user_id = len(self.face_recognizer.known_users) + 1

        # Enroll user
        success = self.face_recognizer.enroll_user(
            user_id=user_id,
            name=name,
            image=face_image,
            preferences=preferences or {}
        )

        if success:
            # [AVATAR] Welcome new user
            self.avatar.speak(
                f"Welcome {name}! I've learned your face. Nice to meet you!",
                emotion='excited'
            )

        return success

    # ========================================================================
    # [DETECTION] OBJECT DETECTION & INVENTORY
    # ========================================================================

    def _analyze_and_update_inventory(self):
        """
        [DETECTION] Compare before/after images and update inventory.

        Process:
        1. Compare images to find changed regions
        2. Run object detection on changed regions only
        3. Determine if items added or removed
        4. Update inventory
        5. Avatar confirms changes
        """
        if not self.before_images or not self.after_images:
            print("   ⚠️  Missing before/after images")
            return

        # Compare all camera zones
        comparison_results = self.image_comparator.compare_all_zones(
            self.before_images,
            self.after_images
        )

        all_changes = []

        for zone_name, (changes, viz) in comparison_results.items():
            if changes:
                print(f"   📍 {zone_name}: {len(changes)} change(s) detected")
                all_changes.extend(changes)

        if not all_changes:
            print("   ℹ️  No significant changes detected")
            # [AVATAR] Inform user
            self.avatar.speak("No changes detected. Just browsing?", emotion='neutral')
            return

        # Filter significant changes (high confidence)
        significant = self.image_comparator.filter_significant_changes(
            all_changes,
            min_confidence=0.6
        )

        print(f"\n🔍 Found {len(significant)} significant change(s)")

        # Run object detection on changed regions
        detected_items = self._detect_items_in_regions(significant)

        if not detected_items:
            # [USER] Ask user what changed (low confidence)
            print("   ❓ Could not identify items - requesting user confirmation")
            self.avatar.speak(
                "I noticed something changed, but I'm not sure what. Can you help me?",
                emotion='thinking'
            )
            return

        # Update inventory
        self._update_inventory_with_detections(detected_items)

    def _detect_items_in_regions(self, change_regions: List) -> List[Dict]:
        """
        [DETECTION] Run object detection on specific regions.

        Args:
            change_regions: List of ChangeRegion objects

        Returns:
            List of detected items with confidence scores
        """
        if not self.object_detector:
            print("   ⚠️  Object detector not available")
            return []

        detected_items = []

        # Use after images for detection
        for zone_name, after_image in self.after_images.items():
            # Find changes in this zone
            zone_changes = [c for c in change_regions if c.zone == zone_name]

            if not zone_changes:
                continue

            # Run detection on full image (TODO: optimize to crop regions)
            detections = self.object_detector.detect(after_image)

            for detection in detections:
                # Check if detection overlaps with change region
                # TODO: Implement overlap checking

                detected_items.append({
                    'item': detection['class'],
                    'confidence': detection['confidence'],
                    'zone': zone_name,
                    'type': 'addition'  # or 'removal' based on before/after brightness
                })

        return detected_items

    def _update_inventory_with_detections(self, detected_items: List[Dict]):
        """
        [DETECTION] Update inventory based on detected changes.

        Args:
            detected_items: List of items detected with confidence scores
        """
        user_id = self.current_user.id if self.current_user else 0

        for item in detected_items:
            item_name = item['item']
            item_type = item['type']
            confidence = item['confidence']

            if item_type == 'addition':
                print(f"   ➕ Adding: {item_name} ({confidence:.0%} confidence)")

                if confidence > 0.8:
                    # High confidence - auto-add
                    self.inventory_manager.add_item(user_id, item_name)

                    # [AVATAR] Confirm
                    avatar_state = self.avatar.respond_to_action(
                        'item_added',
                        {'item': item_name}
                    )

                else:
                    # Medium confidence - ask for confirmation
                    # [AVATAR] Ask user
                    self.avatar.respond_to_action(
                        'low_confidence',
                        {'item': item_name}
                    )
                    # TODO: Add to pending confirmations

            elif item_type == 'removal':
                print(f"   ➖ Removing: {item_name} ({confidence:.0%} confidence)")

                self.inventory_manager.remove_item(user_id, item_name)

                # [AVATAR] Confirm
                self.avatar.respond_to_action(
                    'item_removed',
                    {'item': item_name}
                )

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _get_time_of_day(self) -> str:
        """Get current time of day for contextual greetings."""
        hour = datetime.now().hour

        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'

    def simulate_door_cycle(self):
        """
        [TESTING] Simulate a door open/close cycle for testing.
        """
        print("\n" + "=" * 60)
        print("🧪 SIMULATING DOOR CYCLE")
        print("=" * 60)

        self.door_sensor.simulate_door_open()
        time.sleep(3)  # Simulate user interaction
        self.door_sensor.simulate_door_close()

    def get_system_status(self) -> Dict:
        """Get current system status for dashboard."""
        return {
            'cameras': self.camera_manager.get_camera_info(),
            'door_open': self.is_door_open,
            'current_user': self.current_user.name if self.current_user else 'Guest',
            'enrolled_users': len(self.face_recognizer.known_users),
            'inventory_items': len(self.inventory_manager.get_inventory(
                self.current_user.id if self.current_user else 0
            ))
        }

    def cleanup(self):
        """Cleanup resources on shutdown."""
        print("\n🧹 Cleaning up...")
        self.camera_manager.release_all()
        self.door_sensor.cleanup()
        print("✅ Cleanup complete")


# ========================================================================
# USAGE EXAMPLE (for testing)
# ========================================================================

if __name__ == "__main__":
    # Desktop testing configuration
    config = {
        'face_camera_index': 0,  # Your first webcam
        'food_camera_index': 1,  # Your second webcam
    }

    # Initialize controller
    controller = SmartFridgeController(config)

    # Test facial recognition
    print("\n" + "=" * 60)
    print("Testing Facial Recognition...")
    print("=" * 60)
    result = controller.detect_user()

    # Test door cycle
    controller.simulate_door_cycle()

    # Cleanup
    controller.cleanup()

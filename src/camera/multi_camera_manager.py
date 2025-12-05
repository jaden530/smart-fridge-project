# src/camera/multi_camera_manager.py

import cv2
import os
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from threading import Thread, Lock
from enum import Enum


class CameraZone(Enum):
    """Predefined camera zones for smart fridge layout."""
    EXTERNAL_FACE = "external_face"  # Door-mounted facial recognition
    OVERHEAD = "overhead"  # Top-down view for hand tracking
    SHELF_1_LEFT = "shelf_1_left"
    SHELF_1_RIGHT = "shelf_1_right"
    SHELF_2_LEFT = "shelf_2_left"
    SHELF_2_RIGHT = "shelf_2_right"
    SHELF_3_LEFT = "shelf_3_left"
    SHELF_3_RIGHT = "shelf_3_right"
    SHELF_4_LEFT = "shelf_4_left"
    SHELF_4_RIGHT = "shelf_4_right"
    DOOR_SHELF_1 = "door_shelf_1"
    DOOR_SHELF_2 = "door_shelf_2"
    DRAWER = "drawer"


class MultiCameraManager:
    """
    Manages multiple cameras for comprehensive fridge monitoring.
    Supports simultaneous capture from up to 13 cameras.
    """

    def __init__(self, snapshot_dir: str = "snapshots"):
        self.cameras: Dict[str, dict] = {}
        self.snapshot_dir = snapshot_dir
        self.capture_lock = Lock()
        self.active_overhead = False

        # Create snapshot directory structure
        os.makedirs(os.path.join(snapshot_dir, "before"), exist_ok=True)
        os.makedirs(os.path.join(snapshot_dir, "after"), exist_ok=True)
        os.makedirs(os.path.join(snapshot_dir, "overhead"), exist_ok=True)
        os.makedirs(os.path.join(snapshot_dir, "faces"), exist_ok=True)

        print("📹 Multi-Camera Manager initialized")

    def add_camera(
        self,
        zone: CameraZone,
        source: any,
        resolution: Tuple[int, int] = (1280, 720),
        fps: int = 30
    ) -> bool:
        """
        Add a camera to the system.

        Args:
            zone: CameraZone enum specifying camera location
            source: Camera source (int for USB index, str for URL/path)
            resolution: Desired resolution (width, height)
            fps: Frames per second

        Returns:
            True if camera added successfully
        """
        zone_name = zone.value

        if zone_name in self.cameras:
            print(f"⚠️  Camera already exists for zone: {zone_name}")
            return False

        self.cameras[zone_name] = {
            'zone': zone,
            'source': source,
            'resolution': resolution,
            'fps': fps,
            'cap': None,
            'last_frame': None,
            'last_capture_time': None,
            'is_active': False
        }

        print(f"✅ Camera registered for zone: {zone_name}")
        return True

    def initialize_camera(self, zone: CameraZone) -> bool:
        """
        Initialize/open a specific camera.

        Args:
            zone: CameraZone to initialize

        Returns:
            True if successful
        """
        zone_name = zone.value

        if zone_name not in self.cameras:
            print(f"❌ Camera not registered for zone: {zone_name}")
            return False

        camera_info = self.cameras[zone_name]

        try:
            cap = cv2.VideoCapture(camera_info['source'])

            if not cap.isOpened():
                print(f"❌ Failed to open camera: {zone_name}")
                return False

            # Set camera properties
            width, height = camera_info['resolution']
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_FPS, camera_info['fps'])

            camera_info['cap'] = cap
            camera_info['is_active'] = True

            print(f"✅ Camera initialized: {zone_name} @ {width}x{height}")
            return True

        except Exception as e:
            print(f"❌ Error initializing camera {zone_name}: {e}")
            return False

    def capture_single(self, zone: CameraZone) -> Optional[np.ndarray]:
        """
        Capture a single frame from specified camera.

        Args:
            zone: CameraZone to capture from

        Returns:
            Numpy array of image or None if failed
        """
        zone_name = zone.value

        if zone_name not in self.cameras:
            print(f"❌ Camera not found: {zone_name}")
            return None

        camera_info = self.cameras[zone_name]

        # Initialize camera if not already active
        if not camera_info['is_active']:
            if not self.initialize_camera(zone):
                return None

        cap = camera_info['cap']

        try:
            ret, frame = cap.read()

            if not ret or frame is None:
                print(f"❌ Failed to capture from: {zone_name}")
                return None

            camera_info['last_frame'] = frame
            camera_info['last_capture_time'] = datetime.now()

            return frame

        except Exception as e:
            print(f"❌ Error capturing from {zone_name}: {e}")
            return None

    def capture_all_simultaneously(
        self,
        exclude_zones: List[CameraZone] = None
    ) -> Dict[str, np.ndarray]:
        """
        Capture from all cameras simultaneously using threading.

        Args:
            exclude_zones: List of zones to skip (e.g., external camera)

        Returns:
            Dictionary mapping zone names to captured images
        """
        exclude_zones = exclude_zones or []
        exclude_names = [z.value for z in exclude_zones]

        results = {}
        threads = []

        def capture_thread(zone_name):
            zone = self.cameras[zone_name]['zone']
            frame = self.capture_single(zone)
            if frame is not None:
                results[zone_name] = frame

        with self.capture_lock:
            for zone_name in self.cameras:
                if zone_name not in exclude_names:
                    thread = Thread(target=capture_thread, args=(zone_name,))
                    thread.start()
                    threads.append(thread)

            # Wait for all captures to complete
            for thread in threads:
                thread.join(timeout=5.0)

        print(f"📸 Captured from {len(results)}/{len(self.cameras)} cameras")
        return results

    def capture_before_snapshot(self) -> Dict[str, np.ndarray]:
        """
        Capture 'before' snapshot from all interior cameras.
        Excludes external facial recognition camera.

        Returns:
            Dictionary of captured images
        """
        print("📸 Capturing BEFORE snapshot...")

        exclude = [CameraZone.EXTERNAL_FACE]
        images = self.capture_all_simultaneously(exclude_zones=exclude)

        # Save images
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for zone_name, image in images.items():
            filename = f"before_{zone_name}_{timestamp}.jpg"
            path = os.path.join(self.snapshot_dir, "before", filename)
            cv2.imwrite(path, image)

        return images

    def capture_after_snapshot(self) -> Dict[str, np.ndarray]:
        """
        Capture 'after' snapshot from all interior cameras.

        Returns:
            Dictionary of captured images
        """
        print("📸 Capturing AFTER snapshot...")

        exclude = [CameraZone.EXTERNAL_FACE]
        images = self.capture_all_simultaneously(exclude_zones=exclude)

        # Save images
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        for zone_name, image in images.items():
            filename = f"after_{zone_name}_{timestamp}.jpg"
            path = os.path.join(self.snapshot_dir, "after", filename)
            cv2.imwrite(path, image)

        return images

    def start_overhead_monitoring(self) -> bool:
        """
        Start continuous monitoring from overhead camera for hand tracking.

        Returns:
            True if started successfully
        """
        if self.active_overhead:
            print("⚠️  Overhead monitoring already active")
            return False

        overhead_zone = CameraZone.OVERHEAD

        if overhead_zone.value not in self.cameras:
            print("❌ Overhead camera not registered")
            return False

        self.active_overhead = True
        print("👁️  Overhead camera monitoring ACTIVE")

        return True

    def stop_overhead_monitoring(self):
        """Stop overhead camera monitoring."""
        self.active_overhead = False
        print("👁️  Overhead camera monitoring STOPPED")

    def capture_overhead_frame(self) -> Optional[np.ndarray]:
        """
        Capture single frame from overhead camera (for hand detection).

        Returns:
            Image frame or None
        """
        if not self.active_overhead:
            print("⚠️  Overhead monitoring not active")
            return None

        return self.capture_single(CameraZone.OVERHEAD)

    def capture_facial_recognition(self) -> Optional[np.ndarray]:
        """
        Capture from external facial recognition camera.

        Returns:
            Image frame for face detection
        """
        frame = self.capture_single(CameraZone.EXTERNAL_FACE)

        if frame is not None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"face_{timestamp}.jpg"
            path = os.path.join(self.snapshot_dir, "faces", filename)
            cv2.imwrite(path, frame)

        return frame

    def get_camera_info(self) -> Dict:
        """
        Get information about all registered cameras.

        Returns:
            Dictionary with camera status
        """
        info = {}
        for zone_name, camera in self.cameras.items():
            info[zone_name] = {
                'zone': camera['zone'].value,
                'resolution': camera['resolution'],
                'is_active': camera['is_active'],
                'last_capture': camera['last_capture_time']
            }
        return info

    def release_camera(self, zone: CameraZone):
        """Release a specific camera resource."""
        zone_name = zone.value

        if zone_name in self.cameras:
            camera_info = self.cameras[zone_name]
            if camera_info['cap'] is not None:
                camera_info['cap'].release()
                camera_info['is_active'] = False
                print(f"🔌 Released camera: {zone_name}")

    def release_all(self):
        """Release all camera resources."""
        for zone_name in self.cameras:
            camera_info = self.cameras[zone_name]
            if camera_info['cap'] is not None:
                camera_info['cap'].release()
                camera_info['is_active'] = False

        print("🔌 All cameras released")

    def __del__(self):
        """Cleanup on deletion."""
        self.release_all()

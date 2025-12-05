# src/hardware/door_sensor.py

import time
from typing import Callable, Optional
from datetime import datetime

try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except ImportError:
    GPIO_AVAILABLE = False
    print("⚠️  RPi.GPIO not available - running in simulation mode")


class DoorSensorManager:
    """
    Manages fridge door sensor with GPIO integration.
    Triggers events when door opens/closes for before/after image capture.
    """

    def __init__(self, door_pin: int = 17, debounce_time: float = 0.5):
        """
        Initialize door sensor manager.

        Args:
            door_pin: GPIO pin number for door sensor (default: GPIO17)
            debounce_time: Minimum time between door events in seconds
        """
        self.door_pin = door_pin
        self.debounce_time = debounce_time
        self.is_open = False
        self.last_event_time = 0
        self.simulation_mode = not GPIO_AVAILABLE

        # Event callbacks
        self.on_door_open_callbacks = []
        self.on_door_close_callbacks = []

        if not self.simulation_mode:
            self._setup_gpio()
        else:
            print("🔧 Door sensor running in simulation mode (no hardware)")

    def _setup_gpio(self):
        """Configure GPIO pins for door sensor."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.door_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Add event detection with debouncing
        GPIO.add_event_detect(
            self.door_pin,
            GPIO.BOTH,
            callback=self._handle_door_event,
            bouncetime=int(self.debounce_time * 1000)
        )

        print(f"✅ Door sensor initialized on GPIO{self.door_pin}")

    def _handle_door_event(self, channel):
        """Internal GPIO callback handler."""
        current_time = time.time()

        # Additional software debouncing
        if current_time - self.last_event_time < self.debounce_time:
            return

        self.last_event_time = current_time
        door_state = GPIO.input(self.door_pin)

        # Sensor logic: LOW (0) = door open, HIGH (1) = door closed
        # (Adjust based on your actual sensor type - magnetic reed switch)
        if door_state == GPIO.LOW and not self.is_open:
            self.is_open = True
            self._trigger_door_open()
        elif door_state == GPIO.HIGH and self.is_open:
            self.is_open = False
            self._trigger_door_close()

    def _trigger_door_open(self):
        """Trigger all door open callbacks."""
        timestamp = datetime.now()
        print(f"🚪 Door OPENED at {timestamp.strftime('%H:%M:%S')}")

        for callback in self.on_door_open_callbacks:
            try:
                callback(timestamp)
            except Exception as e:
                print(f"❌ Error in door open callback: {e}")

    def _trigger_door_close(self):
        """Trigger all door close callbacks."""
        timestamp = datetime.now()
        print(f"🚪 Door CLOSED at {timestamp.strftime('%H:%M:%S')}")

        for callback in self.on_door_close_callbacks:
            try:
                callback(timestamp)
            except Exception as e:
                print(f"❌ Error in door close callback: {e}")

    def register_open_callback(self, callback: Callable):
        """
        Register a callback for door open events.

        Args:
            callback: Function to call when door opens, receives timestamp

        Example:
            def on_door_open(timestamp):
                print(f"Capturing BEFORE snapshot at {timestamp}")
                camera_manager.capture_all_cameras("before")

            door_sensor.register_open_callback(on_door_open)
        """
        self.on_door_open_callbacks.append(callback)
        print(f"✅ Registered door open callback: {callback.__name__}")

    def register_close_callback(self, callback: Callable):
        """
        Register a callback for door close events.

        Args:
            callback: Function to call when door closes, receives timestamp

        Example:
            def on_door_close(timestamp):
                print(f"Capturing AFTER snapshot at {timestamp}")
                camera_manager.capture_all_cameras("after")
                compare_and_update_inventory()

            door_sensor.register_close_callback(on_door_close)
        """
        self.on_door_close_callbacks.append(callback)
        print(f"✅ Registered door close callback: {callback.__name__}")

    def simulate_door_open(self):
        """Manually trigger door open (for testing without hardware)."""
        if not self.is_open:
            self.is_open = True
            self._trigger_door_open()

    def simulate_door_close(self):
        """Manually trigger door close (for testing without hardware)."""
        if self.is_open:
            self.is_open = False
            self._trigger_door_close()

    def get_door_state(self) -> bool:
        """
        Get current door state.

        Returns:
            True if door is open, False if closed
        """
        if not self.simulation_mode:
            self.is_open = (GPIO.input(self.door_pin) == GPIO.LOW)
        return self.is_open

    def cleanup(self):
        """Clean up GPIO resources."""
        if not self.simulation_mode:
            GPIO.cleanup(self.door_pin)
            print("🧹 Door sensor GPIO cleaned up")


class DoorEventLogger:
    """Optional utility to log all door events for analytics."""

    def __init__(self, log_file: str = "door_events.log"):
        self.log_file = log_file
        self.open_count = 0
        self.close_count = 0
        self.session_start = datetime.now()

    def log_open(self, timestamp):
        """Log door open event."""
        self.open_count += 1
        self._write_log(f"OPEN,{timestamp.isoformat()}")

    def log_close(self, timestamp):
        """Log door close event."""
        self.close_count += 1
        duration = (timestamp - self.session_start).total_seconds()
        self._write_log(f"CLOSE,{timestamp.isoformat()},{duration:.2f}s")

    def _write_log(self, entry: str):
        """Write log entry to file."""
        with open(self.log_file, 'a') as f:
            f.write(f"{entry}\n")

    def get_stats(self):
        """Get door usage statistics."""
        return {
            'total_opens': self.open_count,
            'total_closes': self.close_count,
            'session_duration': (datetime.now() - self.session_start).total_seconds()
        }

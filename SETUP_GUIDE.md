# Smart Fridge Setup Guide

Complete installation and configuration guide for the Smart Fridge system.

---

## 📋 Prerequisites

### Hardware (Minimum for Testing)
- Raspberry Pi 5 (4GB) OR any Linux/Mac/Windows computer
- 2x USB webcams (one for testing now, plan for more later)
- Magnetic door sensor (optional for testing)
- MicroSD card (32GB+) if using Pi
- Optional: 7" touchscreen display
- Optional: Google Coral USB Accelerator ($60 - 10x faster AI)

### Software Requirements
- Python 3.9+
- pip
- Git

---

## 🚀 Quick Start (Development Mode - Any Computer)

###Step 1: Clone and Install

```bash
# Clone repository
git clone https://github.com/jaden530/smart-fridge-project.git
cd smart-fridge-project

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create `.env` file in project root:

```env
# API Keys (optional for testing)
SPOONACULAR_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
NUTRITIONIX_APP_ID=your_id_here
NUTRITIONIX_API_KEY=your_key_here

# Database
DATABASE_URL=sqlite:///smartfridge.db
SECRET_KEY=your-secret-key-change-this-in-production
```

### Step 3: Run the Application

```bash
cd src
python main.py
```

Open browser: `http://localhost:8080`

**Default login:**
- Username: `testuser`
- Password: `testpassword`

---

## 🧪 Testing with 2 Cameras

### Camera Setup

```python
# Edit src/main.py to configure your cameras

from camera.multi_camera_manager import MultiCameraManager, CameraZone

camera_mgr = MultiCameraManager()

# Camera 1: Webcam for shelf view
camera_mgr.add_camera(CameraZone.SHELF_1_LEFT, 0)  # USB camera index 0

# Camera 2: External facial recognition
camera_mgr.add_camera(CameraZone.EXTERNAL_FACE, 1)  # USB camera index 1

# Or use a test image/video file
camera_mgr.add_camera(CameraZone.SHELF_1_LEFT, "path/to/test_video.mp4")
```

### Test Facial Recognition

```python
from src.ai.facial_recognition import FacialRecognitionManager
import cv2

# Initialize
face_mgr = FacialRecognitionManager()

# Enroll yourself
cap = cv2.VideoCapture(0)
ret, frame = cap.read()

face_mgr.enroll_user(
    user_id=1,
    name="Your Name",
    image=frame,
    preferences={
        'dietary_restriction': 'vegetarian',
        'calorie_goal': 2000
    }
)

# Test recognition
ret, frame = cap.read()
result = face_mgr.recognize_user(frame)

if result:
    user, confidence, location = result
    print(f"Recognized: {user.name} ({confidence:.2%} confidence)")
```

### Test Avatar

Open browser console:

```javascript
// Make avatar speak
avatar.speak("Hello! I'm your smart fridge assistant!", "happy");

// Test greeting
avatar.greet("John", "morning");

// Test actions
avatar.respondToAction("item_added", {item: "milk"});

// Point at inventory
avatar.pointAt("right");

// Think
avatar.think("Hmm, let me check that...");
```

### Simulate Door Events

```python
from src.hardware.door_sensor import DoorSensorManager

door_sensor = DoorSensorManager()  # Runs in simulation mode without GPIO

# Register callbacks
def on_door_open(timestamp):
    print(f"Door opened at {timestamp}")
    # Trigger before snapshot

def on_door_close(timestamp):
    print(f"Door closed at {timestamp}")
    # Trigger after snapshot and comparison

door_sensor.register_open_callback(on_door_open)
door_sensor.register_close_callback(on_door_close)

# Simulate events
door_sensor.simulate_door_open()
door_sensor.simulate_door_close()
```

---

## 🍓 Raspberry Pi Production Setup

### Step 1: Prepare Pi

```bash
# SSH into your Raspberry Pi
ssh pi@smartfridge.local

# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install system dependencies
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    git \
    libatlas-base-dev \
    libopencv-dev \
    python3-opencv \
    libhdf5-dev \
    python3-h5py
```

### Step 2: Clone and Install

```bash
cd /home/pi
git clone https://github.com/jaden530/smart-fridge-project.git
cd smart-fridge-project

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Hardware

**Connect Door Sensor:**
- Door sensor signal → GPIO17
- VCC → 3.3V
- GND → Ground

**Connect Cameras:**
- Pi Camera Module → CSI port
- USB cameras → USB 3.0 ports

**Optional: Coral USB Accelerator:**
- Plug into USB 3.0 port (blue port)
- Install Edge TPU runtime:

```bash
echo "deb https://packages.cloud.google.com/apt coral-edgetpu-stable main" | sudo tee /etc/apt/sources.list.d/coral-edgetpu.list
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo apt-key add -
sudo apt-get update
sudo apt-get install libedgetpu1-std python3-pycoral
```

### Step 4: Enable Kiosk Mode

```bash
cd /home/pi/smart-fridge-project/setup
chmod +x kiosk_setup.sh
./kiosk_setup.sh
```

This will:
- Configure auto-login
- Start Flask app on boot
- Launch fullscreen browser
- Disable screen blanking
- Configure touchscreen
- Create systemd service

### Step 5: Reboot

```bash
sudo reboot
```

Pi will boot directly into the Smart Fridge interface!

---

## 🔧 Kiosk Management

### Useful Commands

```bash
# Restart application
./restart-kiosk.sh

# Exit kiosk mode (for debugging)
./exit-kiosk.sh

# Toggle development mode (disables kiosk)
./toggle-dev-mode.sh

# View application logs
journalctl -u smartfridge.service -f

# Manual start/stop
sudo systemctl start smartfridge.service
sudo systemctl stop smartfridge.service
sudo systemctl restart smartfridge.service
```

### Debug Mode

To temporarily disable kiosk and access desktop:

```bash
./toggle-dev-mode.sh
sudo reboot
```

Re-enable:

```bash
./toggle-dev-mode.sh
sudo reboot
```

---

## 👤 User Enrollment

### Via Web Interface (Coming Soon)

1. Navigate to Settings → Users
2. Click "Enroll New User"
3. Enter name and preferences
4. Look at camera
5. Click "Capture Face"
6. Add 2-3 more samples from different angles

### Via Python (Manual)

```python
from src.ai.facial_recognition import FacialRecognitionManager
from src.camera.multi_camera_manager import MultiCameraManager, CameraZone
import cv2

face_mgr = FacialRecognitionManager()
camera_mgr = MultiCameraManager()
camera_mgr.add_camera(CameraZone.EXTERNAL_FACE, 0)

# Capture and enroll
image = camera_mgr.capture_single(CameraZone.EXTERNAL_FACE)

face_mgr.enroll_user(
    user_id=1,
    name="Alice",
    image=image,
    preferences={
        'dietary_restriction': 'vegan',
        'calorie_goal': 1800,
        'protein_goal': 60
    }
)

# Add more samples
for i in range(3):
    input("Press Enter to capture another sample...")
    image = camera_mgr.capture_single(CameraZone.EXTERNAL_FACE)
    face_mgr.add_face_sample(1, image)

print("Enrollment complete!")
```

---

## 📊 Performance Optimization

### With Google Coral USB Accelerator

1. Convert model to TensorFlow Lite:

```bash
# Coming soon - instructions for converting YOLOv3 to TFLite
```

2. Update code to use Edge TPU:

```python
# In src/ai/object_detection.py
# Instructions coming soon
```

**Expected performance:**
- Object detection: 3-5s → 0.3s
- Face recognition: 0.5s → 0.1s
- Before/after comparison (12 cameras): 60s → 4s

---

## 🔒 Security

### Update Dependencies

```bash
# Check for vulnerabilities
pip list --outdated

# Update all packages
pip install -U -r requirements.txt
```

### Production Checklist

- [ ] Change `SECRET_KEY` in `.env`
- [ ] Remove default test user
- [ ] Enable HTTPS (use nginx reverse proxy)
- [ ] Set up firewall
- [ ] Disable SSH password auth (use keys)
- [ ] Regular backups of `smartfridge.db` and `face_encodings.pkl`
- [ ] Monitor system logs
- [ ] Update Raspberry Pi OS monthly

---

## 🐛 Troubleshooting

### Camera Not Detected

```bash
# List connected cameras
v4l2-ctl --list-devices

# Test camera
ffplay /dev/video0
```

### GPIO Permissions Error

```bash
sudo usermod -a -G gpio $USER
# Logout and login again
```

### Face Recognition Slow

- Reduce image resolution before processing
- Use Google Coral USB Accelerator
- Process frames every 0.5s instead of every frame

### Database Locked

```bash
# Stop application
sudo systemctl stop smartfridge.service

# Check for locks
lsof smartfridge.db

# Restart
sudo systemctl start smartfridge.service
```

### High CPU Usage

- Enable Coral USB Accelerator
- Reduce camera resolution
- Increase time between object detections
- Use event-driven capture (door sensor) instead of continuous

---

## 📚 Next Steps

1. **Test with 2 cameras** - Validate before/after detection works
2. **Enroll family members** - Test multi-user recognition
3. **Train food model** - Improve object detection accuracy
4. **Replace APIs** - Eliminate monthly costs with local models
5. **Build production UI** - Polish touchscreen interface
6. **Create setup wizard** - Make customer installation easy

---

## 💡 Tips

- Start simple: Test with 1-2 cameras before scaling to 12
- Use simulation mode for development (no hardware needed)
- The avatar improves user engagement significantly
- Facial recognition works best with good lighting
- Train custom food detection model for 10x better accuracy
- Google Coral USB is worth the $60 investment

---

## 📞 Support

For issues or questions:
- Check logs: `journalctl -u smartfridge.service -f`
- Review code: GitHub repository
- Test individual components before integration

**Happy building!** 🚀

# 🪟 Windows Desktop Quick Start Guide

**Get the Smart Fridge running on your Windows desktop with 2 webcams in under 10 minutes!**

---

## ✅ What You Need

- ✅ Windows 10/11 computer
- ✅ 2x USB webcams (or 1 webcam for limited testing)
- ✅ Python 3.9+ installed ([Download](https://www.python.org/downloads/))
- ✅ 30 minutes for first-time setup

---

## 🚀 Option 1: Quick Start (Windows .exe - Easiest!)

### Step 1: Build the Executable

Open Command Prompt or PowerShell:

```cmd
cd C:\path\to\smart-fridge-project

REM Install PyInstaller
pip install pyinstaller

REM Build the .exe
pyinstaller build_exe.spec

REM This creates: dist\SmartFridge.exe
```

### Step 2: Run It!

```cmd
cd dist
SmartFridge.exe
```

**That's it!** The app will:
1. Check your cameras
2. Start the server
3. Open your browser automatically

**Default login:**
- Username: `testuser`
- Password: `testpassword`

---

## 🐍 Option 2: Python Development Mode (More Control)

### Step 1: Clone Repository

```cmd
REM If you haven't cloned yet
git clone https://github.com/jaden530/smart-fridge-project.git
cd smart-fridge-project
```

### Step 2: Create Virtual Environment

```cmd
REM Create venv
python -m venv venv

REM Activate it
venv\Scripts\activate

REM You should see (venv) in your prompt now
```

### Step 3: Install Dependencies

```cmd
REM Install everything
pip install -r requirements.txt

REM This might take 5-10 minutes for first install
REM Grab a coffee! ☕
```

**Troubleshooting:**
- If `dlib` fails to install:
  ```cmd
  pip install cmake
  pip install dlib
  ```
- If `face_recognition` fails:
  ```cmd
  pip install --upgrade pip
  pip install face_recognition
  ```

### Step 4: Install YOLOv12 (Optional but Recommended)

```cmd
pip install ultralytics
```

This gives you 10x faster object detection!

### Step 5: Configure Cameras

Edit `src/main.py` around line 75:

```python
# [CAMERAS] Configure your webcam indices

config = {
    'face_camera_index': 0,  # Your first webcam (facial recognition)
    'food_camera_index': 1,  # Your second webcam (food detection)
}

# If you only have 1 camera, use the same index for both:
# config = {
#     'face_camera_index': 0,
#     'food_camera_index': 0,
# }
```

### Step 6: Run the Application

```cmd
cd src
python launcher.py
```

The launcher will:
1. ✅ Check dependencies
2. ✅ Detect cameras
3. ✅ Start Flask server
4. ✅ Open browser automatically

Go to: `http://localhost:8080`

---

## 📸 Testing Your Cameras

### Test Webcam Indices

Not sure which camera is which? Run this:

```python
# test_cameras.py
import cv2

for i in range(4):
    print(f"\nTesting camera {i}...")
    cap = cv2.VideoCapture(i)

    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"  ✅ Camera {i} works!")
            cv2.imshow(f'Camera {i} (Press any key)', frame)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        cap.release()
    else:
        print(f"  ❌ Camera {i} not available")
```

Run it:
```cmd
python test_cameras.py
```

---

## 👤 Enrolling Your Face

### Via Web UI (Coming Soon)

Settings → Users → Enroll New User

### Via Python (Quick Way)

```cmd
cd src
python
```

Then in Python:

```python
from core.smart_fridge_controller import SmartFridgeController

# Initialize
controller = SmartFridgeController({
    'face_camera_index': 0,
    'food_camera_index': 1
})

# Enroll yourself (look at camera 0)
controller.enroll_new_user(
    name="Your Name",
    preferences={
        'dietary_restriction': 'none',  # or 'vegetarian', 'vegan', etc.
        'calorie_goal': 2000,
        'protein_goal': 100
    }
)

# Test recognition (look at camera again)
result = controller.detect_user()
print(result)

# Cleanup
controller.cleanup()
```

---

## 🧪 Testing the System

### Test 1: Facial Recognition

1. Run the app
2. Go to: `http://localhost:8080`
3. Open browser console (F12)
4. Run:
   ```javascript
   // Test avatar
   avatar.greet("TestUser", "morning");
   ```

### Test 2: Door Simulation

In the Python console:

```python
from core.smart_fridge_controller import SmartFridgeController

controller = SmartFridgeController()

# Simulate door cycle
controller.simulate_door_cycle()
```

This will:
1. Capture "before" images
2. Wait 3 seconds
3. Capture "after" images
4. Compare and detect changes

### Test 3: Object Detection (YOLOv12)

```python
from ai.yolov12_detector import YOLOv12Detector
import cv2

# Initialize detector
detector = YOLOv12Detector(model_size='n')  # 'n' = nano (fastest)

# Test with webcam
cap = cv2.VideoCapture(1)  # Your food camera
ret, frame = cap.read()

# Detect objects
results = detector.detect(frame)

print("Detected objects:")
for obj in results:
    print(f"  - {obj['class']}: {obj['confidence']:.2%}")

cap.release()
```

---

## 🎨 Testing the Avatar

Open the browser console (F12) and try these:

```javascript
// Make avatar speak
avatar.speak("Hello! I'm your smart fridge!", "happy");

// Test greeting
avatar.greet("Your Name", "afternoon");

// Test responses
avatar.respondToAction("item_added", {item: "milk"});
avatar.respondToAction("item_removed", {item: "apple"});

// Point at inventory
avatar.pointAt("right");

// Show thinking
avatar.think("Hmm, let me analyze that...");

// Custom emotion
avatar.speak("Something smells amazing!", "excited");
```

---

## 📋 Step-by-Step Usage Flow

### Morning Routine Test:

1. **Start the app**
   ```cmd
   cd src
   python launcher.py
   ```

2. **Enroll your face** (first time only)
   - Go to Settings (coming soon) or use Python script above

3. **Test recognition**
   - Stand in front of camera 0
   - System should recognize you: "Good morning, [Your Name]!"

4. **Test door cycle**
   - Click "Simulate Door Open" (or use Python)
   - Put an apple in front of camera 1
   - Click "Simulate Door Close"
   - System should detect: "Added apple to inventory!"

5. **Check inventory**
   - Go to Dashboard
   - See your apple listed
   - Avatar should confirm

---

## 🐛 Troubleshooting

### Camera Not Working

```cmd
# Check if camera is in use
# Close Zoom, Teams, Skype, etc.

# Test camera directly
python test_cameras.py
```

### Port 8080 Already in Use

```cmd
# Find what's using it
netstat -ano | findstr :8080

# Kill that process (replace PID with actual number)
taskkill /PID <PID> /F

# Or change port in launcher.py:
# app.run(port=8081)
```

### Face Recognition Not Working

```cmd
# Reinstall dlib
pip uninstall dlib
pip install dlib

# Or use pre-built wheels
pip install https://github.com/z-mahmud22/Dlib_Windows_Python3.x/raw/main/dlib-19.24.0-cp310-cp310-win_amd64.whl
```

### YOLOv12 Model Not Downloading

```cmd
# Manually download
# Visit: https://github.com/ultralytics/assets/releases
# Download yolov8n.pt
# Place in: C:\Users\<you>\.cache\ultralytics
```

### Avatar Not Showing

- Check browser console (F12) for errors
- Make sure JavaScript is enabled
- Try different browser (Chrome recommended)

---

## 🎯 Next Steps

Once basic testing works:

### 1. Train Custom Food Model

```python
from ai.yolov12_detector import YOLOv12Detector

detector = YOLOv12Detector()

# Train on your fridge photos
detector.train_on_custom_dataset(
    dataset_yaml='data/food_dataset.yaml',
    epochs=100
)
```

### 2. Add More Users

```python
# Enroll family members
controller.enroll_new_user("Alice", preferences={...})
controller.enroll_new_user("Bob", preferences={...})
```

### 3. Customize Avatar

Edit `src/ui/avatar_manager.py`:
- Change greeting messages
- Add custom responses
- Adjust personality traits

### 4. Build for Production

```cmd
# Build Windows installer
pyinstaller build_exe.spec

# Test the .exe
dist\SmartFridge.exe
```

---

## 📊 Performance Expectations

**On typical Windows desktop:**

| Task | With CPU | With Google Coral USB |
|------|----------|----------------------|
| Face Recognition | 0.5s | 0.1s |
| Object Detection (YOLOv12) | 1-2s | 0.3s |
| Before/After Comparison | 3-5s | 1s |
| Avatar Response | Instant | Instant |

**Recommendations:**
- **For testing:** CPU is fine
- **For production:** Get Google Coral USB ($60) - 10x faster

---

## 💡 Tips for Success

1. **Good Lighting:** Face recognition works best with even, frontal lighting
2. **Camera Angles:** Mount cameras at eye level for facial recognition
3. **Background:** Plain backgrounds improve object detection
4. **Training Data:** Take 100+ photos of your actual fridge for best accuracy
5. **Start Simple:** Test with 1-2 items before filling the fridge

---

## 🎓 Learning Resources

### Understanding the Code

Main files with **[EASY TO FIND]** markers:

1. **`src/core/smart_fridge_controller.py`** - Main brain
   - Look for `[CAMERAS]` - Camera setup
   - Look for `[DOOR]` - Door events
   - Look for `[FACE]` - Facial recognition
   - Look for `[AVATAR]` - Avatar responses
   - Look for `[DETECTION]` - Object detection

2. **`src/ai/yolov12_detector.py`** - Object detection
3. **`src/ai/facial_recognition.py`** - Face recognition
4. **`src/ui/avatar_manager.py`** - Avatar personality
5. **`templates/components/avatar.html`** - Avatar visuals

### Modifying the System

**To change camera indices:**
→ Edit `src/main.py` line 75

**To change avatar responses:**
→ Edit `src/ui/avatar_manager.py` lines 30-80

**To add custom object classes:**
→ Train YOLOv12 on your dataset (see above)

**To change UI colors:**
→ Edit `templates/base.html` CSS section

---

## 🚀 You're Ready!

**Start here:**
```cmd
cd smart-fridge-project
venv\Scripts\activate
cd src
python launcher.py
```

**Browser opens** → **Login** → **Start testing!**

**Having issues?** Check troubleshooting section above or review the code comments (they're detailed!).

**Working?** Celebrate! 🎉 You just broke your 1-year stagnation!

---

## 📞 Quick Reference

| Task | Command |
|------|---------|
| Start app | `python src/launcher.py` |
| Build .exe | `pyinstaller build_exe.spec` |
| Test cameras | `python test_cameras.py` |
| Enroll face | See "Enrolling Your Face" section |
| Test avatar | Browser console (F12) → `avatar.speak("Hi!", "happy")` |
| View logs | Check console output |
| Stop server | Ctrl+C in terminal |

**You've got this!** 💪

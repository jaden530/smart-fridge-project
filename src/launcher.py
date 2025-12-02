#!/usr/bin/env python3
"""
SMART FRIDGE LAUNCHER
====================
Simple launcher for desktop testing with 2 webcams.

Double-click to run!
"""

import sys
import os
import webbrowser
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ['FLASK_ENV'] = 'development'

def print_banner():
    """Print welcome banner."""
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                            ║
║              🧊 SMART FRIDGE SYSTEM 🧊                     ║
║                                                            ║
║  AI-Powered Kitchen Management with Facial Recognition    ║
║                                                            ║
╚════════════════════════════════════════════════════════════╝
    """)

def check_cameras():
    """Check if webcams are available."""
    import cv2

    print("\n📹 Checking for webcams...")

    available_cameras = []
    for i in range(4):  # Check first 4 indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                available_cameras.append(i)
                print(f"   ✅ Camera {i}: Available")
            cap.release()

    if len(available_cameras) == 0:
        print("   ⚠️  No cameras detected!")
        print("   💡 The system will still run, but camera features won't work")
        return False
    elif len(available_cameras) == 1:
        print(f"\n   ℹ️  Only 1 camera detected (need 2 for full features)")
        print("   💡 System will use camera 0 for both face and food detection")
        return True
    else:
        print(f"\n   ✅ {len(available_cameras)} cameras detected - perfect for testing!")
        return True

def check_dependencies():
    """Check if all required packages are installed."""
    print("\n📦 Checking dependencies...")

    required = {
        'flask': 'Flask',
        'cv2': 'opencv-python',
        'face_recognition': 'face-recognition',
        'numpy': 'numpy',
    }

    optional = {
        'ultralytics': 'ultralytics (for YOLOv12)',
    }

    missing = []

    for module, package in required.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - REQUIRED")
            missing.append(package)

    for module, package in optional.items():
        try:
            __import__(module)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ⚠️  {package} - OPTIONAL (install for better performance)")

    if missing:
        print("\n❌ Missing required packages!")
        print("\n💡 Install with:")
        print(f"   pip install {' '.join(missing)}")
        return False

    return True

def run_system():
    """Run the Smart Fridge system."""
    print("\n🚀 Starting Smart Fridge System...")
    print("=" * 60)

    try:
        # Import main app
        from main import app

        # Auto-open browser after short delay
        def open_browser():
            time.sleep(2)
            print("\n🌐 Opening browser...")
            webbrowser.open('http://localhost:8080')

        import threading
        threading.Thread(target=open_browser, daemon=True).start()

        # Run Flask app
        print("\n✅ Server starting at http://localhost:8080")
        print("\n📝 Default Login:")
        print("   Username: testuser")
        print("   Password: testpassword")
        print("\n💡 Press Ctrl+C to stop")
        print("=" * 60)

        app.run(
            host='0.0.0.0',
            port=8080,
            debug=False,  # Set to False for .exe
            use_reloader=False  # Must be False for .exe
        )

    except KeyboardInterrupt:
        print("\n\n👋 Shutting down...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Check that:")
        print("   1. All dependencies are installed")
        print("   2. Cameras are connected")
        print("   3. Port 8080 is not in use")
        input("\nPress Enter to exit...")
        sys.exit(1)

def main():
    """Main entry point."""
    print_banner()

    # Check dependencies
    if not check_dependencies():
        input("\nPress Enter to exit...")
        sys.exit(1)

    # Check cameras
    check_cameras()

    print("\n" + "=" * 60)
    input("Press Enter to start the Smart Fridge system...")

    # Run system
    run_system()

if __name__ == "__main__":
    main()

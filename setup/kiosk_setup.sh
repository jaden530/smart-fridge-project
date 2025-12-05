#!/bin/bash
# Smart Fridge Kiosk Mode Setup Script
# Configures Raspberry Pi to boot directly into the smart fridge interface

set -e  # Exit on error

echo "🚀 Smart Fridge Kiosk Mode Setup"
echo "=================================="
echo ""

# Check if running on Raspberry Pi
if [ ! -f /proc/device-tree/model ]; then
    echo "⚠️  Warning: This doesn't appear to be a Raspberry Pi"
    echo "Continuing anyway for testing purposes..."
fi

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install required packages
echo "📦 Installing kiosk dependencies..."
sudo apt-get install -y \
    chromium-browser \
    unclutter \
    xdotool \
    x11-xserver-utils \
    matchbox-window-manager \
    xautomation \
    sed

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
cd /home/pi/smart-fridge-project
pip3 install -r requirements.txt

# Create autostart directory if it doesn't exist
mkdir -p /home/pi/.config/lxsession/LXDE-pi

# Create autostart file for kiosk mode
echo "📝 Configuring autostart..."
cat > /home/pi/.config/lxsession/LXDE-pi/autostart << 'EOF'
# Disable screen blanking
@xset s noblank
@xset s off
@xset -dpms

# Hide mouse cursor when idle
@unclutter -idle 0.5 -root

# Start window manager
@matchbox-window-manager -use_titlebar no

# Wait for network
@bash -c 'while ! ping -c1 google.com &>/dev/null; do sleep 1; done'

# Start Smart Fridge Flask app in background
@bash -c 'cd /home/pi/smart-fridge-project && python3 src/main.py > /tmp/smartfridge.log 2>&1 &'

# Wait for Flask to start
@bash -c 'sleep 10'

# Start Chromium in kiosk mode
@chromium-browser --kiosk \
    --noerrdialogs \
    --disable-infobars \
    --no-first-run \
    --ozone-platform=wayland \
    --enable-features=OverlayScrollbar \
    --start-fullscreen \
    --disable-translate \
    --disable-features=TranslateUI \
    --disable-save-password-bubble \
    --touch-events=enabled \
    http://localhost:8080
EOF

# Disable screen saver
echo "🖥️  Disabling screen saver..."
sudo raspi-config nonint do_blanking 1

# Set auto-login
echo "🔐 Configuring auto-login..."
sudo raspi-config nonint do_boot_behaviour B4

# Create systemd service for Flask app (alternative approach)
echo "📝 Creating systemd service..."
sudo tee /etc/systemd/system/smartfridge.service > /dev/null << 'EOF'
[Unit]
Description=Smart Fridge Application
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/smart-fridge-project
ExecStart=/usr/bin/python3 /home/pi/smart-fridge-project/src/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable the service
echo "⚙️  Enabling Smart Fridge service..."
sudo systemctl daemon-reload
sudo systemctl enable smartfridge.service

# Configure GPIO permissions
echo "🔧 Setting up GPIO permissions..."
sudo usermod -a -G gpio pi
sudo usermod -a -G video pi

# Create startup script for quick refresh
cat > /home/pi/restart-kiosk.sh << 'EOF'
#!/bin/bash
# Quick restart script for development

echo "Restarting Smart Fridge kiosk..."
sudo systemctl restart smartfridge.service
sleep 3
DISPLAY=:0 xdotool key F5  # Refresh browser
echo "Done!"
EOF

chmod +x /home/pi/restart-kiosk.sh

# Create exit kiosk script (for debugging)
cat > /home/pi/exit-kiosk.sh << 'EOF'
#!/bin/bash
# Exit kiosk mode temporarily for debugging

pkill -f chromium-browser
echo "Exited kiosk mode. Run 'startx' to restart X11 or reboot."
EOF

chmod +x /home/pi/exit-kiosk.sh

# Optimize for touchscreen
echo "👆 Configuring touchscreen..."
if [ ! -f /etc/X11/xorg.conf.d/99-calibration.conf ]; then
    sudo mkdir -p /etc/X11/xorg.conf.d
    sudo tee /etc/X11/xorg.conf.d/99-touchscreen.conf > /dev/null << 'EOF'
Section "InputClass"
    Identifier "calibration"
    MatchProduct "touchscreen"
    Option "Calibration" "0 0 800 480"
    Option "SwapAxes" "0"
EndSection
EOF
fi

# Create development mode toggle
cat > /home/pi/toggle-dev-mode.sh << 'EOF'
#!/bin/bash
# Toggle between kiosk and development mode

if [ -f /home/pi/.kiosk-disabled ]; then
    rm /home/pi/.kiosk-disabled
    echo "✅ Kiosk mode ENABLED - will start on next boot"
    sudo systemctl enable smartfridge.service
else
    touch /home/pi/.kiosk-disabled
    echo "🛠️  Development mode ENABLED - kiosk disabled on next boot"
    sudo systemctl disable smartfridge.service
fi
EOF

chmod +x /home/pi/toggle-dev-mode.sh

# Create splash screen
echo "🎨 Setting up splash screen..."
sudo apt-get install -y fbi
# TODO: Add custom splash image

# Configure boot options for faster startup
echo "⚡ Optimizing boot time..."
sudo raspi-config nonint do_boot_splash 1  # Disable splash
sudo systemctl disable bluetooth  # Disable if not needed
sudo systemctl disable hciuart   # Disable if not needed

# Set hostname
echo "🏷️  Setting hostname..."
sudo raspi-config nonint do_hostname smartfridge

echo ""
echo "✅ Kiosk mode setup complete!"
echo ""
echo "📋 Quick Reference:"
echo "  • Restart kiosk:   ./restart-kiosk.sh"
echo "  • Exit kiosk:      ./exit-kiosk.sh"
echo "  • Toggle dev mode: ./toggle-dev-mode.sh"
echo "  • View logs:       journalctl -u smartfridge.service -f"
echo "  • Manual start:    sudo systemctl start smartfridge.service"
echo ""
echo "🔄 Reboot now to start kiosk mode? (y/n)"
read -r response

if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    echo "Rebooting in 5 seconds..."
    sleep 5
    sudo reboot
else
    echo "Skipped reboot. Run 'sudo reboot' when ready."
fi

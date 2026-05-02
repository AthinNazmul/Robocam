# 🔧 RoboNeT Camera Tool — Troubleshooting Guide

## ❌ Segmentation Fault on RPi 4 / Ubuntu 22

### NEW: Stack Smashing / TTK Theme Crash (FIXED!)
- Symptom: `*** stack smashing detected ***: terminated` or ttk::ThemeChanged error
- Why: Tkinter theme system has bugs on ARM/Pi that corrupt memory
- Fix: Already applied in latest version! Just reinstall:
  ```bash
  cd ~/Robocam
  bash install.sh
  ```
- Details: See [PI_CRASH_FIX.md](PI_CRASH_FIX.md)

### Root Causes (Other)

**Cause 1: Missing Display Server (Most Common)**
- Symptom: `Segmentation fault (core dumped)` when running `python3 robocam.py`
- Why: Tkinter requires an X11 display server. Headless RPi doesn't have one.
- Solution: Use SSH with X11 forwarding, or install a desktop environment.

**Cause 2: Missing Tkinter Package**
- Symptom: ImportError OR segfault during Tk initialization
- Why: Python3-tk must be installed via apt (not pip)
- Solution: Run `sudo apt install python3-tk`

**Cause 3: OpenCV / GStreamer Backend Issues**
- Symptom: Crash after GUI loads, when connecting to camera
- Why: libcamera/GStreamer not properly initialized, or missing codec libs
- Solution: Install support libraries (see below)

---

## ✅ Full Setup Instructions (RPi 4 / Ubuntu 22.04)

### Step 1: System Dependencies
```bash
# Update package manager
sudo apt update && sudo apt upgrade -y

# Install Python and Tkinter (CRITICAL — not available via pip!)
sudo apt install python3 python3-pip python3-tk -y

# Install camera support libraries
sudo apt install v4l-utils libcamera-apps libcamera0 -y

# Install GStreamer codecs (needed for video)
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base \
                 gstreamer1.0-plugins-good gstreamer1.0-plugins-bad -y
```

### Step 2: Python Dependencies
```bash
cd ~/Robocam
pip install -r requirements.txt
```

### Step 3: Run with X11 Display

**Option A: SSH with X11 Forwarding (Recommended for Remote)**
```bash
# On your desktop/laptop:
ssh -X pi@<your-pi-ip>

# Then on the Pi:
cd ~/Robocam/src
python3 robocam.py
```

**Option B: Local Display (HDMI + Keyboard)**
```bash
# On the Pi directly:
cd ~/Robocam/src
python3 robocam.py
```

**Option C: Virtual Display (Headless)**
```bash
# Install Xvfb (virtual framebuffer)
sudo apt install xvfb -y

# Run with virtual display
DISPLAY=:1 xvfb-run -a python3 robocam.py &
```

---

## 🐛 Specific Error Messages & Fixes

### "Segmentation fault (core dumped)"
```bash
# Fix 1: Install Tkinter
sudo apt install python3-tk -y

# Fix 2: Use X11 forwarding
ssh -X pi@<ip>

# Fix 3: Check core dump (if available)
coredumpctl dump python3
```

### "ImportError: No module named 'cv2'"
```bash
pip install opencv-python>=4.8.0
```

### "ImportError: No module named 'PIL'"
```bash
pip install Pillow>=10.0.0
```

### "No cameras found"
```bash
# Check connected cameras
v4l2-ctl --list-devices
libcamera-hello --list-cameras

# Try direct test
python3 -c "import cv2; cap = cv2.VideoCapture(0); print('OK' if cap.isOpened() else 'FAIL')"
```

### "Failed to open camera"
```bash
# Fix permissions
sudo usermod -a -G video $USER

# Then logout and login again, or:
newgrp video

# Test:
v4l2-ctl --list-devices
```

### "GStreamer error" / "libcamera pipeline error"
```bash
# Install missing GStreamer plugins
sudo apt install gstreamer1.0-libcamera gstreamer1.0-plugins-bad -y

# Test pipeline manually
gst-launch-1.0 libcamerasrc ! video/x-raw,width=640,height=480 ! videoconvert ! autovideosink
```

---

## 📋 Pre-Flight Checklist

Before reporting a bug, verify:

- [ ] Tkinter installed: `python3 -c "import tkinter; print('OK')"`
- [ ] OpenCV installed: `python3 -c "import cv2; print(cv2.__version__)"`
- [ ] Pillow installed: `python3 -c "from PIL import Image; print('OK')"`
- [ ] Camera detected: `v4l2-ctl --list-devices`
- [ ] X11 display available: `echo $DISPLAY` (if SSH)
- [ ] User in video group: `groups | grep video`
- [ ] libcamera working: `libcamera-hello --list-cameras`

---

## 🔗 Useful Commands for Debugging

```bash
# List all cameras with full device info
v4l2-ctl --list-devices

# List libcamera cameras (Pi Camera / IMX219)
libcamera-hello --list-cameras

# Test OpenCV camera capture
python3 << 'EOF'
import cv2
for i in range(5):
    cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
    if cap.isOpened():
        print(f"Camera {i}: OK")
        cap.release()
    else:
        print(f"Camera {i}: UNAVAILABLE")
EOF

# Check for GStreamer issues
gst-inspect-1.0 | grep libcamera
gst-launch-1.0 libcamerasrc ! fakesink

# View dmesg for hardware errors
dmesg | tail -20
```

---

## 🆘 If You Still Have Issues

1. Provide output from:
   ```bash
   uname -a
   python3 --version
   v4l2-ctl --list-devices
   libcamera-hello --list-cameras
   pip show opencv-python pillow
   ```

2. Run with verbose output:
   ```bash
   python3 -u robocam.py 2>&1 | tee debug.log
   ```

3. Check system logs:
   ```bash
   journalctl -e --no-pager | tail -50
   ```


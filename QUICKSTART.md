# 🚀 RoboNeT Camera Tool — Quick Start Guide

## TL;DR for RPi 4 + Ubuntu 22

```bash
# 1. Install system dependencies
sudo apt update
sudo apt install python3 python3-pip python3-tk v4l-utils libcamera-apps -y

# 2. Install Python packages
pip install opencv-python pillow

# 3. Run (via SSH with X11)
ssh -X your-username@your-pi-ip     # From your desktop
cd ~/Robocam/src
python3 robocam.py
```

---

## Why Your Script is Crashing

You're likely seeing **"Segmentation fault (core dumped)"** because:

1. **python3-tk not installed** — Tkinter must come from apt, not pip
2. **No X11 display** — Tkinter needs a display server (use SSH -X)
3. **Missing system libraries** — libcamera and GStreamer plugins missing

---

## Setup Options

### ✅ Option 1: SSH with X11 Forwarding (Recommended)
**Best for:** Remote access, no display connected

```bash
# On your desktop/laptop:
ssh -X your-username@your-pi-ip

# Then on the Pi terminal:
cd ~/Robocam/src
python3 robocam.py
```

**Advantages:**
- Easy to use
- Works remotely
- Stable on RPi

**Requirements:**
- SSH enabled on Pi (default on Ubuntu)
- X11 on your desktop (Linux/Mac have it; Windows needs [VcXsrv](https://sourceforge.net/projects/vcxsrv/))

---

### ✅ Option 2: Physical Display (HDMI + Keyboard)
**Best for:** Lab/workshop setups

```bash
# Connect HDMI monitor and keyboard to Pi, then:
cd ~/Robocam/src
python3 robocam.py
```

**Advantages:**
- Direct display, no network needed
- Lowest latency

**Requirements:**
- HDMI display
- Keyboard/mouse
- Desktop environment (Ubuntu Server doesn't have GUI by default)

To install desktop:
```bash
sudo apt install ubuntu-desktop -y
sudo reboot
```

---

### ℹ️ Option 3: VNC Remote Desktop
**Best for:** Full desktop experience

```bash
# Install VNC server on Pi
sudo apt install tigervnc-standalone-server tigervnc-common -y

# Start VNC (creates display on :1)
vncserver -geometry 1280x720 -depth 24 :1

# Connect from desktop with VNC viewer
# Then run tool in VNC session
```

---

## Full Installation (One-Liner)

```bash
cd ~/Robocam && bash install.sh
```

This script automatically detects and installs:
- Python 3.10/3.12 (detects your Ubuntu version)
- Tkinter
- v4l2 and libcamera tools  
- Python dependencies in a virtual environment

---

## Test Your Setup

Before running the full tool, verify each component:

```bash
# 1. Tkinter
python3 -c "import tkinter; print('✓ Tkinter OK')" || echo "✗ FAIL: sudo apt install python3-tk"

# 2. OpenCV
python3 -c "import cv2; print(f'✓ OpenCV {cv2.__version__}')" || echo "✗ FAIL: pip install opencv-python"

# 3. Pillow
python3 -c "from PIL import Image; print('✓ Pillow OK')" || echo "✗ FAIL: pip install pillow"

# 4. Camera Detection
v4l2-ctl --list-devices

# 5. libcamera (if CSI camera)
libcamera-hello --list-cameras
```

If any test fails, it tells you exactly what to fix.

---

## Common Issues

| Issue | Fix |
|-------|-----|
| "Segmentation fault" at startup | Install python3-tk: `sudo apt install python3-tk` |
| "Segmentation fault" just before GUI | Use SSH -X or connect physical display |
| "No cameras found" | Run `v4l2-ctl --list-devices` to check |
| "Permission denied" (camera) | Add user to video group: `sudo usermod -a -G video $USER` then logout/login |
| "GStreamer error" | Install codecs: `sudo apt install gstreamer1.0-plugins-bad` |

---

## Next Steps

Once running, you can:
- 📷 Take photos → saved in `~/robocam_output/`
- 🎬 Record video (up to 1080p on Pi 4)
- 🔌 Use USB cameras (Logitech C920, etc.)
- 🎥 Use CSI cameras (Camera Module 1.3, IMX219)

See **TROUBLESHOOTING.md** for detailed debugging.


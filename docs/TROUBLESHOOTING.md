# 🔧 Troubleshooting Guide — RoboNeT Camera Tool

## Table of Contents
1. [Camera Not Detected](#1-camera-not-detected)
2. [CSI Camera Issues (Pi 4)](#2-csi-camera-issues-pi-4)
3. [CSI Camera Issues (Pi 5)](#3-csi-camera-issues-pi-5)
4. [USB Camera Issues](#4-usb-camera-issues)
5. [GUI / Display Issues](#5-gui--display-issues)
6. [Python / Dependency Issues](#6-python--dependency-issues)
7. [Performance Issues](#7-performance-issues)

---

## 1. Camera Not Detected

**Run this first — check what Ubuntu sees:**
```bash
v4l2-ctl --list-devices
```

Expected output example:
```
mmal service 16.1 (platform:bcm2835-v4l2):
        /dev/video0

USB Camera (usb-0000:01:00.0-1.1):
        /dev/video1
```

If nothing shows up:
- Make sure the camera ribbon cable is firmly connected
- Try a different USB port (for USB cameras)
- Reboot and try again

---

## 2. CSI Camera Issues (Pi 4)

**Pi 4 uses the legacy `bcm2835` driver. Make sure it's enabled:**

```bash
# Check if camera module is loaded
lsmod | grep bcm2835

# Enable camera via raspi-config
sudo raspi-config
# → Interface Options → Camera → Enable → Finish → Reboot
```

**Or enable manually in `/boot/firmware/config.txt`:**
```bash
sudo nano /boot/firmware/config.txt
```
Add or uncomment:
```
start_x=1
gpu_mem=128
```
Then reboot:
```bash
sudo reboot
```

**Verify after reboot:**
```bash
v4l2-ctl --list-devices
# Should show: mmal service → /dev/video0
```

---

## 3. CSI Camera Issues (Pi 5)

**Pi 5 uses the new `libcamera` stack. Check with:**
```bash
libcamera-hello --list-cameras
```

Expected output:
```
Available cameras
-----------------
0 : imx219 [3280x2464] (/base/axi/...)
```

**If libcamera doesn't find the camera:**
```bash
# Check /boot/firmware/config.txt
sudo nano /boot/firmware/config.txt
```
Make sure this line exists and is NOT commented out:
```
camera_auto_detect=1
```
Then reboot.

**Test a quick capture with libcamera:**
```bash
libcamera-jpeg -o test.jpg
```
If this works but the tool still doesn't detect it, open an issue on the repo.

---

## 4. USB Camera Issues

**Check if the USB camera is visible:**
```bash
lsusb
# Look for your camera in the list

v4l2-ctl --list-devices
# Should show your USB camera with /dev/videoX
```

**Test it directly with OpenCV:**
```python
import cv2
cap = cv2.VideoCapture(0)   # try 0, 1, 2 etc.
print(cap.isOpened())
cap.release()
```

**Permission issue?**
```bash
# Add your user to the video group
sudo usermod -aG video $USER
# Then log out and log back in
```

---

## 5. GUI / Display Issues

**"cannot connect to X server" or blank window:**

The tool requires a graphical desktop session. It will NOT work over plain SSH.

Options:
- Connect a physical HDMI monitor + keyboard
- Use **VNC Viewer** from another computer

**Setting up VNC on Ubuntu:**
```bash
sudo apt install tigervnc-standalone-server -y
vncserver :1 -geometry 1280x720 -depth 24
```
Then connect from your laptop using VNC Viewer to `<pi-ip>:5901`.

**Tkinter window is tiny or huge:**
```bash
# Set display scaling before running
export GDK_SCALE=1
bash ~/robocam/run_robocam.sh
```

---

## 6. Python / Dependency Issues

**`No module named 'tkinter'`**
```bash
sudo apt install python3-tk
```

**`No module named 'cv2'`**
```bash
source ~/robocam/env/bin/activate
pip install opencv-python
```

**`No module named 'PIL'`**
```bash
source ~/robocam/env/bin/activate
pip install pillow
```

**Reinstall everything from scratch:**
```bash
rm -rf ~/robocam/env
cd /path/to/robocam-tool
bash install.sh
```

---

## 7. Performance Issues

**Low FPS or laggy preview:**
- Use a lower resolution — select `320x240` or `640x480` in the Settings panel
- The tool targets 30fps but actual FPS depends on Pi model and camera

**Pi 4 vs Pi 5 performance:**
| Resolution | Pi 4 FPS | Pi 5 FPS |
|------------|----------|----------|
| 320x240    | ~30      | ~30      |
| 640x480    | ~25      | ~30      |
| 1280x720   | ~15      | ~25      |
| 1920x1080  | ~5       | ~15      |

**Video recording stutters:**
- Lower resolution before recording
- Make sure you're recording to a fast microSD (Class 10 / A1 rated) or NVMe SSD (Pi 5)

---

## Still stuck?

Open an issue on the GitHub repo with:
1. Your Pi model (`cat /proc/device-tree/model`)
2. Your Ubuntu version (`lsb_release -a`)
3. Output of `v4l2-ctl --list-devices`
4. The exact error message from the System Log panel
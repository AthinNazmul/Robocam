# 📷 RoboNeT Camera Tool

> A lightweight GUI tool for detecting and using camera modules on Raspberry Pi running Ubuntu — built for students, makers, and anyone who has ever fought with camera setup on Linux.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python)
![Platform](https://img.shields.io/badge/Platform-Raspberry%20Pi%204%20%7C%205-red?style=flat-square)
![OS](https://img.shields.io/badge/OS-Ubuntu%2024.04-orange?style=flat-square&logo=ubuntu)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

---

## 🤔 Why This Tool?

On **Raspberry Pi OS**, camera modules (CSI & USB) work out of the box.  
On **Ubuntu 24.04**, they don't — `picamera` doesn't exist, device paths are different, and the error messages are cryptic.

**RoboNeT Camera Tool** fixes this with a single script:
- Auto-detects **every camera** connected to your Pi (CSI + USB)
- Gives you a clean **desktop GUI** for live preview, photos & video
- Works on **Pi 4** (Camera Module 1.3) and **Pi 5** (IMX219) out of the box
- No config files, no manual device paths, no headaches

---

## ✅ Supported Hardware

| Camera              | Pi Model   | Interface | Support      |
|---------------------|------------|-----------|--------------|
| Camera Module 1.3   | Pi 4       | CSI       | ✅ Full       |
| IMX219              | Pi 5       | CSI       | ✅ Full       |
| Any USB Webcam      | Pi 4 / 5   | USB       | ✅ Full       |
| Multiple cameras    | Any        | Mixed     | ✅ All listed |

---

## 🖥️ Screenshots

```
┌─────────────────────────────────────────────────────────────┐
│ 🤖 RoboNeT Camera Tool          ● Live — IMX219 Camera      │
├──────────────┬──────────────────────────────────────────────┤
│ CAMERA       │                                              │
│ DETECTION    │                                              │
│              │           [ LIVE PREVIEW ]                   │
│ 📷 [CSI]     │                                              │
│   IMX219     │                                              │
│ 🔌 [USB]     │                                              │
│   Webcam C920│                                              │
│              ├──────────────────────────────────────────────┤
│ CAMERA INFO  │  📷 Take Photo   ⏺ Start Recording  📂 Open │
│ Type:  CSI   ├──────────────────────────────────────────────┤
│ Device:/dev/ │ SYSTEM LOG                                   │
│        video0│ [10:42:01] Found 2 camera(s).               │
│ Index: 0     │ [10:42:05] Connected! IMX219 @ 640x480       │
│              │ [10:42:11] Photo saved → photo_20250502.jpg  │
└──────────────┴──────────────────────────────────────────────┘
```

---

## 🚀 Quick Start — 2 Steps

```bash
# Step 1: Run the installer (handles everything)
cd ~/Robocam
bash install.sh

# Step 2: Launch the tool (from anywhere)
robocam
```

**That's all.** Everything else is automatic.

---

## 📦 What the Installer Does Automatically

- ✅ Detects your Pi model & Ubuntu version
- ✅ Installs all system dependencies (`python3-tk`, `libcamera`, GStreamer, etc.)
- ✅ Creates a Python virtual environment
- ✅ Installs Python packages (`opencv`, `pillow`)
- ✅ Sets up camera permissions (video group)
- ✅ Creates system launcher (`robocam` command)
- ✅ Creates desktop shortcut
- ✅ Detects connected cameras
- ✅ Creates output folder

---

## 🪄 Alternative: Manual Setup (not recommended)

If you prefer to skip the installer:

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3-tk python3-pip v4l-utils libcamera-apps gstreamer1.0-plugins-bad

# Install Python packages
pip install opencv-python pillow

# Run directly
python3 src/robocam.py
```

**But we recommend using the installer** — it's smarter and handles edge cases.

---

## 🎮 How to Use

1. **Scan** → Click `🔍 Scan for Cameras` — detects all connected cameras
2. **Select** → Click a camera from the list to see its info
3. **Connect** → Click `▶ Connect Camera` to start live preview
4. **Capture** → Click `📷 Take Photo` to save a `.jpg`
5. **Record** → Click `⏺ Start Recording` to save a `.avi` video
6. **Output** → Click `📂 Open Output` to open the save folder

All outputs are saved to `~/robocam_output/` by default. Change it anytime from the Settings panel.

---

## ❓ Troubleshooting

**Camera not showing up after Scan?**
```bash
# Check what Linux sees
v4l2-ctl --list-devices

# For CSI cameras specifically
libcamera-hello --list-cameras
```

**CSI camera on Pi 4 not detected?**
```bash
# Make sure camera interface is enabled
sudo raspi-config
# → Interface Options → Camera → Enable → Reboot
```

**GUI window doesn't open?**
```
The tool requires a desktop session.
Use VNC viewer or connect a physical monitor.
It will NOT work over plain SSH.
```

**`No module named 'tkinter'`?**
```bash
sudo apt install python3-tk
```

**`No module named 'cv2'`?**
```bash
pip install opencv-python
```

---

## 📁 Project Structure

```
robocam-tool/
├── src/
│   └── robocam.py          # Main application
├── docs/
│   └── TROUBLESHOOTING.md  # Extended troubleshooting guide
├── install.sh              # One-command installer
├── requirements.txt        # Python dependencies
├── .gitignore
└── README.md
```

---

## 🤝 Contributing

Contributions are welcome! If you find a bug or want to add support for a new camera:

1. Fork the repo
2. Create a branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m 'Add support for XYZ camera'`
4. Push and open a Pull Request

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 👨‍💻 Author

**Nazmul Hasan Athin** 
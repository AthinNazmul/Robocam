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

## 🚀 Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/YOUR_USERNAME/robocam-tool.git
cd robocam-tool

# 2. Run the installer
bash install.sh

# 3. Launch the tool
bash ~/robocam/run_robocam.sh
```

That's it. The installer handles everything else.

---

## 📦 What the Installer Does

| Step | Action |
|------|--------|
| 1 | Checks Ubuntu version & Pi model |
| 2 | Installs `python3-tk`, `v4l-utils`, `libcamera-apps` via apt |
| 3 | Creates a Python virtual environment at `~/robocam/env` |
| 4 | Installs `opencv-python` and `pillow` inside the venv |
| 5 | Copies the tool to `~/robocam/` |
| 6 | Creates a launcher script `~/robocam/run_robocam.sh` |
| 7 | Creates a desktop shortcut (if Desktop folder exists) |
| 8 | Runs a live camera detection check |

---

## 🛠️ Manual Installation (without installer)

```bash
# System packages
sudo apt update
sudo apt install -y python3-tk v4l-utils libcamera-apps python3-pip

# Python packages
pip install opencv-python pillow

# Run directly
python3 src/robocam.py
```

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
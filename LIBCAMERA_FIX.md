# 🎥 Pi Camera Fix: Missing GStreamer libcamera Plugin

## Problem

You're seeing:
```
✓ Camera detected: unicam
✓ Camera opens successfully
✗ Can't read frames from camera
✗ "Camera read error" 
```

**Why:** Your Pi Camera requires the **GStreamer libcamera plugin** which wasn't installed.

---

## Solution: 2 Steps

### Step 1: Reinstall with Fixed Packages

Run the updated installer:

```bash
bash ~/Robocam/install.sh
```

This will now install:
- ✅ `libcamera0` — libcamera library
- ✅ `libcamera-dev` — development files  
- ✅ `gstreamer1.0-libcamera` — **GStreamer plugin (THIS WAS MISSING)**

### Step 2: Copy Updated Tool

```bash
cp ~/Robocam/src/robocam.py ~/robocam/robocam.py
robocam
```

---

## Try Again

1. Click "🔍 Scan for Cameras"
2. Select "unicam (libcamera)"
3. Click "▶ Connect Camera" 
4. **You should see live preview now!** 🎬

---

## If It STILL Doesn't Work

Run this and share the output:

```bash
robocam 2>&1 | tee robocam_debug.log
```

Look for lines like:
- `Found CSI camera:` — Camera detected ✓
- `Opening camera:` — Trying to connect
- `OK (libcamera/GStreamer)` — Success! ✓
- `gstreamer1.0-libcamera` — Available? 

If you see "GStreamer error", the plugin isn't installed. Try:
```bash
sudo apt install -y gstreamer1.0-libcamera libcamera-dev
```

Then run robocam again.

---

## What Changed

### Before (Broken):
- `libcamera-apps` was in the package list (often fails on Pi 4)
- GStreamer libcamera plugin was missing

### After (Fixed):
- Replaced with `libcamera-dev` 
- Added explicit `gstreamer1.0-libcamera` plugin
- Better error messages guide you to the fix

---

## Quick Check

Verify your system has what's needed:

```bash
# Check libcamera
dpkg -l | grep libcamera

# Check GStreamer plugin
gst-inspect-1.0 libcamera 2>/dev/null && echo "✓ GStreamer libcamera plugin OK"
```

If you don't have them, reinstall:
```bash
bash ~/Robocam/install.sh
```

---

**Try it now!** 🚀


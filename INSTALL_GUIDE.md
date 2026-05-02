# 🚀 Installation Guide — Super Simple

> **TL;DR:** Run `bash install.sh` → then run `robocam`. Done.

---

## Prerequisites

- **Raspberry Pi 4 or 5** with Ubuntu 22.04+ (or any Linux with similar packages)
- **Internet connection** (for package downloads)
- **Terminal access** (SSH or physical keyboard)
- **A camera** (Pi Camera OR USB webcam)

---

## Step 1: Run the Installer

```bash
cd ~/Robocam
bash install.sh
```

**What happens:**
- ✅ Checks your system (Pi model, Ubuntu version)
- ✅ Installs everything needed via `apt` and `pip`
- ✅ Sets up camera permissions
- ✅ Creates a system-wide launcher command
- ✅ Detects your cameras
- ✅ Done in ~5 minutes

**That's step 1.** Just wait for it to finish.

---

## Step 2: Run the Tool

```bash
robocam
```

**That's it.** The GUI should pop up.

---

## First Time Using It?

1. **Scan for cameras** → Click the blue "🔍 Scan for Cameras" button
2. **Select a camera** → Click it in the list
3. **Connect** → Click "▶ Connect Camera"
4. **See the preview** → Should show your camera feed
5. **Take a photo** → Click "📷 Take Photo"
6. **Find your files** → Click "📂 Open Output"

---

## Troubleshooting

### Installer fails to run
```bash
# Make it executable
chmod +x ~/Robocam/install.sh

# Try again
bash ~/Robocam/install.sh
```

### `robocam` command not found after install
```bash
# Try this
bash ~/robocam/run_robocam.sh

# Or open a new terminal (some shells cache PATH)
```

### "Segmentation fault" or GUI won't open
```bash
# Usually means missing X11 display
# If on RPi with keyboard + monitor: should work
# If over SSH: use X11 forwarding
ssh -X your-pi-ip
robocam
```

### Camera shows "No cameras found"
```bash
# Check what the system sees
v4l2-ctl --list-devices

# If CSI camera:
libcamera-hello --list-cameras

# If nothing shows up, camera may not be connected or enabled
```

### Permission denied errors
```bash
# Sometimes after install, you need to do this:
newgrp video

# Then try robocam again
robocam
```

---

## That's All

No config files to edit. No manual steps. Just install and use.

If something breaks, run the installer again:
```bash
bash ~/Robocam/install.sh
```

It will repair/update everything.

---

## Next Steps

- Read the README.md for advanced usage
- Check TROUBLESHOOTING.md if you hit issues
- Look at QUICKSTART.md for alternative launch methods


#!/bin/bash
# Verify and fix libcamera setup on Pi 4 + Ubuntu 22

echo "🔍 RoboNeT — Checking libcamera setup"
echo "===================================="
echo ""

echo "1. Checking libcamera installation..."
dpkg -l | grep -i libcamera | head -5

echo ""
echo "2. Testing libcamera command existence..."
which libcamera-still && echo "✓ libcamera-still found" || echo "✗ libcamera-still NOT found"
which libcamera-raw && echo "✓ libcamera-raw found" || echo "✗ libcamera-raw NOT found"

echo ""
echo "3. Checking GStreamer libcamera plugin..."
gst-inspect-1.0 libcamera 2>/dev/null && echo "✓ GStreamer libcamera plugin OK" || echo "✗ Plugin not available"

echo ""
echo "4. Testing if camera is accessible..."
v4l2-ctl --list-devices | grep -A2 unicam && echo "✓ Camera detected" || echo "✗ Camera not found"

echo ""
echo "5. Listing /dev/video devices..."
ls -la /dev/video* 2>/dev/null | head -5

echo ""
echo "6. Checking camera permissions..."
groups | grep video && echo "✓ User in video group" || echo "✗ User NOT in video group - run: sudo usermod -a -G video $USER"

echo ""
echo "RECOMMENDATIONS:"
echo "================================================"
echo "If libcamera is missing, try:"
echo "  sudo apt update"
echo "  sudo apt install -y libcamera0 libcamera-dev gstreamer1.0-libcamera"
echo ""
echo "If you see permission issues:"
echo "  sudo usermod -a -G video $USER"
echo "  newgrp video"
echo ""
echo "If camera is not detected:"
echo "  Check /proc/device-tree/model to verify you're on Pi 4"
echo "  Check if camera is connected to CSI port"
echo "  Try: vcgencmd get_camera"
echo ""


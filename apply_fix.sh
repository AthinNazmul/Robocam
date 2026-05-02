#!/bin/bash
# Copy this and run on your Pi to get the libcamera fix

echo "🎥 RoboNeT — Installing libcamera Support"
echo "========================================="
echo ""

echo "Step 1: Installing missing GStreamer libcamera plugin..."
sudo apt install -y gstreamer1.0-libcamera libcamera-dev 2>&1 | grep -E "(OK|already|installed|WARN)" || echo "Installation completed"
echo ""

echo "Step 2: Copying fixed robocam.py..."
cp ~/Robocam/src/robocam.py ~/robocam/robocam.py
echo "✓ Done"
echo ""

echo "Step 3: Testing..."
python3 -m py_compile ~/robocam/robocam.py && echo "✓ File OK" || echo "✗ FAILED"
echo ""

echo "Step 4: Try connecting to your camera..."
echo ""
robocam 2>&1


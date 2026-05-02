#!/bin/bash
# ============================================================
#  CSI Camera Status Check - Simple Diagnostic
#  (No installation attempts - just shows what's available)
# ============================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CSI Camera Availability Check"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check OS
if lsb_release -a 2>/dev/null | grep -q "22.04"; then
    echo "⚠️  System: Ubuntu 22.04 (ARM)"
    echo "   → libcamera NOT available in standard repos"
    echo ""
elif lsb_release -a 2>/dev/null | grep -q -E "bullseye|bookworm"; then
    echo "✓ System: Raspberry Pi OS"
    echo "  → Full camera support available"
    echo ""
else
    echo "? System: Unknown"
    lsb_release -a 2>/dev/null | sed 's/^/   /'
    echo ""
fi

# Check Pi model
if [ -f /proc/device-tree/model ]; then
    echo "Hardware: $(tr -d '\0' < /proc/device-tree/model)"
    echo ""
fi

# Check if camera exists
echo "Camera Device Status:"
if [ -e /dev/video0 ]; then
    echo "✓ /dev/video0 exists (camera device present)"
else
    echo "✗ /dev/video0 NOT found (camera not detected)"
fi
echo ""

# Check v4l2
echo "v4l2-ctl Output:"
if command -v v4l2-ctl &>/dev/null; then
    echo "✓ v4l2-ctl available"
    v4l2-ctl --list-devices 2>/dev/null | head -5 | sed 's/^/  /'
else
    echo "✗ v4l2-ctl NOT found"
fi
echo ""

# Check libcamera
echo "libcamera Status:"
if dpkg -s libcamera0 &>/dev/null 2>&1; then
    echo "✓ libcamera0 installed"
else
    echo "✗ libcamera0 NOT installed"
fi

if command -v libcamera-hello &>/dev/null; then
    echo "✓ libcamera-hello command available"
    libcamera-hello --list-cameras 2>&1 | grep -i "available\|camera" | head -3 | sed 's/^/  /'
else
    echo "✗ libcamera-hello NOT available"
fi
echo ""

# Check GStreamer
echo "GStreamer Status:"
if dpkg -s gstreamer1.0-libcamera &>/dev/null 2>&1; then
    echo "✓ GStreamer libcamera plugin installed"
else
    echo "✗ GStreamer libcamera plugin NOT available"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "SUMMARY:"
echo ""

if dpkg -s libcamera0 &>/dev/null 2>&1 && command -v libcamera-hello &>/dev/null; then
    echo "✓ libcamera is WORKING - CSI camera should work"
else
    echo "✗ libcamera NOT WORKING or NOT INSTALLED"
    echo ""
    echo "SOLUTION OPTIONS:"
    echo ""
    echo "1. Try USB Camera (to verify robocam works):"
    echo "   → Connect any USB webcam"
    echo "   → Run: robocam"
    echo ""
    echo "2. Install Raspberry Pi OS:"
    echo "   → Full camera support included"
    echo "   → Download: https://www.raspberrypi.com/software/"
    echo ""
    echo "3. Keep Ubuntu 22.04 (CSI cameras won't work):"
    echo "   → Use USB cameras instead"
    echo "   → robocam fully functional otherwise"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

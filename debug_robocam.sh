#!/bin/bash
# ============================================================
#  RoboNeT Camera Tool — Debug Launcher
#  Use this to see detailed error messages
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/robocam"
VENV_DIR="$INSTALL_DIR/env"
TOOL_PATH="$INSTALL_DIR/robocam.py"

echo "🔍 RoboNeT Camera Tool — Debug Mode"
echo "===================================="
echo ""
echo "Checking system..."
echo "Python: $(python3 --version)"
echo "Tkinter: $(python3 -c 'import tkinter; print("✓ OK")' 2>&1 || echo "✗ MISSING")"
echo "OpenCV: $(python3 -c 'import cv2; print(cv2.__version__)' 2>&1 || echo "✗ MISSING")"
echo "Pillow: $(python3 -c 'from PIL import Image; print("✓ OK")' 2>&1 || echo "✗ MISSING")"
echo ""

# Check display
if [ -z "$DISPLAY" ]; then
    echo "⚠️  WARNING: No DISPLAY set!"
    echo "   If over SSH, use: ssh -X pi@<ip>"
    echo "   Or set: export DISPLAY=:0"
    echo ""
fi

# Activate venv and run with verbose output
source "$VENV_DIR/bin/activate" 2>/dev/null || {
    echo "❌ Virtual environment not found."
    echo "   Please run: bash ~/Robocam/install.sh"
    exit 1
}

echo "🚀 Launching RoboNeT..."
echo "===================================="
echo ""

# Run with full traceback on crash
python3 -u "$TOOL_PATH" 2>&1


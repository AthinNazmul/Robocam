#!/bin/bash
# ============================================================
#  RoboNeT Camera Tool — Launcher
#  Author : Nazmul Hasan Athin | 
#  GitHub : https://github.com/AthinNazmul/Robocam
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$HOME/robocam/env"
TOOL="$HOME/src/robocam.py"

# ── If venv + installed tool exist, use them ─────────────────
if [ -f "$VENV_DIR/bin/activate" ] && [ -f "$TOOL" ]; then
    source "$VENV_DIR/bin/activate"
    python3 "$TOOL"
    exit 0
fi

# ── Fallback: run directly from repo src/ with system Python ─
# Install deps inline if needed
echo "[RoboNeT] Virtual environment not found — running from repo directly."
echo "[RoboNeT] Tip: run 'bash install.sh' first for a cleaner setup."
echo ""

# Check dependencies
MISSING=0
python3 -c "import cv2" 2>/dev/null || {
    echo "[ERROR] opencv-python not found. Installing..."
    pip3 install opencv-python --break-system-packages -q
    MISSING=1
}
python3 -c "import PIL" 2>/dev/null || {
    echo "[ERROR] pillow not found. Installing..."
    pip3 install pillow --break-system-packages -q
    MISSING=1
}
python3 -c "import tkinter" 2>/dev/null || {
    echo "[ERROR] tkinter not found."
    echo "        Fix: sudo apt install python3-tk"
    exit 1
}

# Run from repo src/
python3 "$SCRIPT_DIR/src/robocam.py"
#!/bin/bash
# ============================================================
#  CSI Camera Fix for Ubuntu 22.04 on Raspberry Pi
#  Tries multiple methods to enable CSI camera support
# ============================================================

set -e

# ── Colors ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Helpers ──────────────────────────────────────────────────
info()    { echo -e "  ${CYAN}[INFO]${NC}  $1"; }
success() { echo -e "  ${GREEN}[ OK ]${NC}  $1"; }
warn()    { echo -e "  ${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "  ${RED}[FAIL]${NC}  $1"; echo ""; exit 1; }
step()    { echo ""; echo -e "  ${BOLD}── $1${NC}"; echo ""; }

echo ""
echo -e "${CYAN}${BOLD}"
echo "  CSI Camera Fix for Ubuntu 22.04 on Pi 4"
echo -e "${NC}"
echo ""

# ── Step 1: Try to install libcamera from Raspberry Pi repos ──
step "Step 1 — Add Raspberry Pi Camera Repository"

info "Checking if RPi camera repos can be added..."

# Check if we can add the official RPi repo
if curl -s https://archive.raspberrypi.org/debian/raspberrypi.gpg.key 2>/dev/null | gpg --import 2>/dev/null; then
    info "RPi repository key available"
    if grep -q "archive.raspberrypi.org" /etc/apt/sources.list 2>/dev/null; then
        success "RPi repository already configured"
    else
        info "Adding RPi repository..."
        echo "deb https://archive.raspberrypi.org/debian/ bullseye main" | sudo tee /etc/apt/sources.list.d/raspi.list
        sudo apt update -qq 2>/dev/null || true
        success "RPi repository added"
    fi
else
    warn "Could not add RPi repository (network or server issue)"
fi

# ── Step 2: Try alternative - install from Ubuntu Mantic (newer) ──
step "Step 2 — Try Ubuntu 23.10 (Mantic) libcamera packages"

info "Checking Ubuntu 23.10 package availability..."

# Create a temporary sources entry for Mantic libcamera only
cat > /tmp/mantic-libs.list << 'EOF'
deb http://archive.ubuntu.com/ubuntu mantic main universe
EOF

info "Installing libcamera from Ubuntu 23.10..."
if sudo apt-get install -y -t mantic libcamera0 libcamera-dev 2>&1 | tail -3; then
    success "Installed libcamera from Ubuntu 23.10"
else
    warn "Could not install from Ubuntu 23.10"
fi

sudo rm -f /tmp/mantic-libs.list

# ── Step 3: Try to install gstreamer plugin ──────────────────
step "Step 3 — Install GStreamer libcamera plugin"

if sudo apt install -y gstreamer1.0-libcamera 2>&1 | grep -i "unable\|no package"; then
    info "GStreamer plugin not available in repos (expected on Ubuntu 22.04)"
else
    success "GStreamer libcamera plugin may be available"
fi

# ── Step 4: Workaround - Enable CSI camera via device tree ────
step "Step 4 — Enable CSI Camera via Device Tree (if needed)"

info "Checking /boot/firmware for device tree settings..."

if [ -f "/boot/firmware/config.txt" ]; then
    if grep -q "camera_auto_detect=1" /boot/firmware/config.txt; then
        success "CSI camera already auto-detected in boot config"
    else
        info "Enabling camera in boot config..."
        sudo bash -c 'echo "" >> /boot/firmware/config.txt'
        sudo bash -c 'echo "# Enable CSI camera auto-detection" >> /boot/firmware/config.txt'
        sudo bash -c 'echo "camera_auto_detect=1" >> /boot/firmware/config.txt'
        warn "⚠️ Camera settings added. Reboot required: sudo reboot"
    fi
elif [ -f "/boot/config.txt" ]; then
    if grep -q "camera_auto_detect=1" /boot/config.txt; then
        success "CSI camera already auto-detected in boot config"
    else
        info "Enabling camera in boot config..."
        sudo bash -c 'echo "" >> /boot/config.txt'
        sudo bash -c 'echo "# Enable CSI camera auto-detection" >> /boot/config.txt'
        sudo bash -c 'echo "camera_auto_detect=1" >> /boot/config.txt'
        warn "⚠️ Camera settings added. Reboot required: sudo reboot"
    fi
else
    info "No boot config found (may not be on official Pi setup)"
fi

# ── Step 5: Verify v4l2 can read camera ─────────────────────
step "Step 5 — Verify Camera Device Access"

if [ -e /dev/video0 ]; then
    success "/dev/video0 exists"
    
    info "Testing camera with v4l2-ctl..."
    if v4l2-ctl -d /dev/video0 --get-fmt-video 2>/dev/null; then
        success "✓ Camera responds to v4l2 commands"
    else
        warn "Camera device exists but not responding to v4l2"
    fi
else
    warn "No /dev/video0 found - camera may not be properly connected"
fi

# ── Step 6: Final verification ───────────────────────────────
step "Step 6 — Final Status Check"

echo "  System Summary:"
echo ""

if command -v libcamera-hello &>/dev/null; then
    echo "    ✓ libcamera command available"
else
    echo "    ✗ libcamera command NOT available"
fi

if dpkg -s libcamera0 &>/dev/null 2>&1; then
    echo "    ✓ libcamera0 library installed"
else
    echo "    ✗ libcamera0 NOT installed"
fi

if dpkg -s gstreamer1.0-libcamera &>/dev/null 2>&1; then
    echo "    ✓ GStreamer libcamera plugin installed"
else
    echo "    ✗ GStreamer plugin NOT available (expected)"
fi

if [ -e /dev/video0 ]; then
    echo "    ✓ Camera device /dev/video0 present"
else
    echo "    ✗ Camera device NOT detected"
fi

echo ""
echo "────────────────────────────────────────────────────────────"
echo ""
echo -e "  ${BOLD}Next Steps:${NC}"
echo ""
echo "  If camera still doesn't work:"
echo ""
echo "    ${YELLOW}Option 1: Try with USB Camera${NC}"
echo "    → Connect any USB webcam and test"
echo "    → Proves robocam works; CSI is a system limitation"
echo ""
echo "    ${YELLOW}Option 2: Reboot and test${NC}"
echo "    → ${CYAN}sudo reboot${NC}"
echo "    → ${CYAN}robocam${NC}"
echo ""
echo "    ${YELLOW}Option 3: Install Raspberry Pi OS${NC}"
echo "    → Official Pi OS has full camera support"
echo "    → Can run Ubuntu tools on top of it"
echo ""
echo "────────────────────────────────────────────────────────────"
echo ""

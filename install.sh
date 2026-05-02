#!/bin/bash
# ============================================================
#  RoboNeT Camera Tool — Installer
#  Author : FNazmul Hasan Athin| United International University
#  GitHub : https://github.com/FahimHafiz/robocam-tool
#  OS     : Ubuntu 24.04 LTS
#  Pi     : Raspberry Pi 4 & 5
# ============================================================

set -e

# ── Colors ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Banner ───────────────────────────────────────────────────
clear
echo ""
echo -e "${CYAN}${BOLD}"
echo "  ██████╗  ██████╗ ██████╗  ██████╗  ██████╗ █████╗ ███╗   ███╗"
echo "  ██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗██╔════╝██╔══██╗████╗ ████║"
echo "  ██████╔╝██║   ██║██████╔╝██║   ██║██║     ███████║██╔████╔██║"
echo "  ██╔══██╗██║   ██║██╔══██╗██║   ██║██║     ██╔══██║██║╚██╔╝██║"
echo "  ██║  ██║╚██████╔╝██████╔╝╚██████╔╝╚██████╗██║  ██║██║ ╚═╝ ██║"
echo "  ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝  ╚═════╝╚═╝  ╚═╝╚═╝     ╚═╝"
echo -e "${NC}"
echo -e "  ${BOLD}📷  Camera Tool — Installer v1.0${NC}"
echo -e "  ${CYAN}United International University · CENTER${NC}"
echo ""
echo -e "  Raspberry Pi 4 (Camera 1.3 CSI)"
echo -e "  Raspberry Pi 5 (IMX219 CSI)"
echo -e "  Any USB Camera"
echo ""
echo "────────────────────────────────────────────────────────────"

# ── Helpers ──────────────────────────────────────────────────
info()    { echo -e "  ${CYAN}[INFO]${NC}  $1"; }
success() { echo -e "  ${GREEN}[ OK ]${NC}  $1"; }
warn()    { echo -e "  ${YELLOW}[WARN]${NC}  $1"; }
error()   { echo -e "  ${RED}[FAIL]${NC}  $1"; echo ""; exit 1; }
step()    { echo ""; echo -e "  ${BOLD}── $1${NC}"; echo ""; }

# ── Locate script directory ───────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_SRC="$SCRIPT_DIR/src/robocam.py"

if [ ! -f "$TOOL_SRC" ]; then
    error "src/robocam.py not found. Make sure you cloned the full repository."
fi

# ── Step 1.5: Enable additional repositories ────────────────
step "Step 1.5 — Checking Repository Configuration"

info "Ubuntu 22.04 on Pi may need universe/multiverse repos for libcamera plugins..."
if grep -q "^deb.*universe" /etc/apt/sources.list 2>/dev/null; then
    success "universe repo already enabled"
else
    info "Enabling universe and multiverse repositories..."
    if sudo add-apt-repository -y universe multiverse -qq 2>/dev/null; then
        success "Repositories enabled"
        info "Running apt update..."
        sudo apt update -qq 2>/dev/null || true
    else
        warn "Could not enable additional repos (may still work)"
    fi
fi

# OS check
if command -v lsb_release &>/dev/null; then
    OS_VER=$(lsb_release -rs)
    OS_NAME=$(lsb_release -ds)
    if [[ "$OS_VER" == "22.04" || "$OS_VER" == "23.10" || "$OS_VER" == "24.04" ]]; then
        success "OS: $OS_NAME ✓"
    elif [[ "$OS_VER" < "22.04" ]]; then
        warn "Ubuntu $OS_VER is older than 22.04 — some features may not work."
        warn "Strongly recommend upgrading to Ubuntu 22.04 LTS or newer."
    else
        warn "Detected: $OS_NAME — proceeding."
    fi
else
    warn "Cannot detect OS version. Proceeding anyway."
fi

# Pi model
if [ -f /proc/device-tree/model ]; then
    PI_MODEL=$(tr -d '\0' < /proc/device-tree/model)
    success "Hardware: $PI_MODEL"
else
    warn "Pi model not detected. Tool will still work on non-Pi Linux systems."
fi

# Display check
if [ -z "$DISPLAY" ] && [ -z "$WAYLAND_DISPLAY" ]; then
    warn "No display environment found."
    warn "The GUI requires a desktop session (VNC or physical monitor)."
    warn "Installation will continue — launch the tool from a desktop."
else
    success "Display session: OK"
fi

# Python check
PYTHON_VER=$(python3 --version 2>&1 | awk '{print $2}')
success "Python: $PYTHON_VER"

# ── Step 2: System packages ───────────────────────────────────
step "Step 2 — Installing System Packages"

info "Running apt update..."
sudo apt update -qq 2>/dev/null

# Detect Python minor version for correct venv package name
# Ubuntu 22.04 ships Python 3.10, Ubuntu 24.04 ships Python 3.12
PYTHON_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
VENV_PKG="python3.${PYTHON_MINOR}-venv"
info "Detected Python 3.$PYTHON_MINOR — will install $VENV_PKG"

declare -A PKGS=(
    ["python3-tk"]="Tkinter GUI framework (REQUIRED)"
    ["python3-pip"]="Python package manager"
    ["python3-dev"]="Python development headers"
    ["$VENV_PKG"]="Python virtual environment"
    ["v4l-utils"]="Camera device detection (v4l2)"
    ["libcamera0"]="libcamera runtime library"
    ["libcamera-dev"]="libcamera development files"
    ["gstreamer1.0-tools"]="GStreamer tools"
    ["gstreamer1.0-plugins-base"]="GStreamer base plugins"
    ["gstreamer1.0-plugins-good"]="GStreamer good plugins"
    ["gstreamer1.0-plugins-bad"]="GStreamer bad plugins (codec support)"
    ["gstreamer1.0-libcamera"]="GStreamer libcamera plugin (for CSI)"
    ["libcamera-tools"]="libcamera command-line tools"
    ["libopenjp2-7"]="JPEG2000 codec"
)

for pkg in "${!PKGS[@]}"; do
    desc="${PKGS[$pkg]}"
    if dpkg -s "$pkg" &>/dev/null 2>&1; then
        success "$pkg — already installed"
    else
        info "Installing $pkg..."
        INSTALL_SUCCESS=false
        
        # First attempt with quiet mode
        if sudo apt install -y "$pkg" -qq 2>/dev/null; then
            INSTALL_SUCCESS=true
        # Second attempt with normal output in case of transient failures
        elif sudo apt install -y "$pkg" 2>/dev/null; then
            INSTALL_SUCCESS=true
        fi
        
        if [ "$INSTALL_SUCCESS" = true ]; then
            success "$pkg — installed"
        else
            if [[ "$desc" == *"REQUIRED"* ]]; then
                error "❌ CRITICAL: $pkg failed to install. Cannot continue."
            else
                warn "⚠️  $pkg — not available in standard repos"
                if [ "$pkg" = "gstreamer1.0-libcamera" ]; then
                    info "This is expected on Ubuntu 22.04. Tool will use alternative methods."
                fi
            fi
        fi
    fi
done

# ── Step 3: Virtual environment ───────────────────────────────
step "Step 3 — Python Virtual Environment"

INSTALL_DIR="$HOME/robocam"
VENV_DIR="$INSTALL_DIR/env"

mkdir -p "$INSTALL_DIR"

if [ -d "$VENV_DIR" ]; then
    warn "Virtual environment already exists — skipping creation."
    warn "To reinstall fresh: rm -rf $VENV_DIR and run install.sh again."
else
    info "Creating virtual environment at $VENV_DIR ..."
    python3 -m venv "$VENV_DIR"
    success "Virtual environment created"
fi

source "$VENV_DIR/bin/activate"
success "Virtual environment activated"

# ── Step 4: Python packages ───────────────────────────────────
step "Step 4 — Installing Python Packages"

info "Upgrading pip..."
pip install --upgrade pip -q

info "Installing opencv-python..."
pip install opencv-python -q
success "opencv-python installed"

info "Installing pillow..."
pip install pillow -q
success "pillow installed"

# ── Step 5: Copy tool ─────────────────────────────────────────
step "Step 5 — Installing RoboNeT Camera Tool"

cp "$TOOL_SRC" "$INSTALL_DIR/robocam.py"
success "robocam.py installed to $INSTALL_DIR"

# ── Step 6: Launcher script ───────────────────────────────────
step "Step 6 — Creating Launcher"

LAUNCHER="$INSTALL_DIR/run_robocam.sh"

cat > "$LAUNCHER" << LAUNCHER_EOF
#!/bin/bash
# RoboNeT Camera Tool — Launcher
# Generated by install.sh

source "$VENV_DIR/bin/activate"
python3 "$INSTALL_DIR/robocam.py" "\$@"
LAUNCHER_EOF

chmod +x "$LAUNCHER"
success "Launcher: $LAUNCHER"

# Desktop shortcut
DESKTOP_DIR="$HOME/Desktop"
if [ -d "$DESKTOP_DIR" ]; then
    SHORTCUT="$DESKTOP_DIR/RoboNeT Camera Tool.desktop"
    cat > "$SHORTCUT" << DESKTOP_EOF
[Desktop Entry]
Version=1.0
Name=RoboNeT Camera Tool
Comment=Detect and use cameras on Raspberry Pi Ubuntu
Exec=bash $LAUNCHER
Icon=camera-photo
Terminal=false
Type=Application
Categories=Utility;Science;
Keywords=camera;raspberry;pi;robocam;
DESKTOP_EOF
    chmod +x "$SHORTCUT"
    success "Desktop shortcut created"
else
    info "No Desktop folder — skipping desktop shortcut"
fi

# Output directory
mkdir -p "$HOME/robocam_output"
success "Output folder: ~/robocam_output/"

# ── Step 7: User permissions ─────────────────────────────────
step "Step 7 — Setting Camera Permissions"

info "Ensuring user is in video group..."
if groups "$USER" | grep -q video; then
    success "User already in video group ✓"
else
    info "Adding user to 'video' group for camera access..."
    if sudo usermod -a -G video "$USER" 2>/dev/null; then
        success "User added to video group ✓"
        warn ""
        warn "⚠️  IMPORTANT: Permissions require one of these:"
        warn "    1. Log out and back in (RECOMMENDED)"
        warn "    2. Run: newgrp video"
        warn "    3. Reboot system: sudo reboot"
        warn ""
        warn "Without relogging, camera access may fail!"
        warn ""
    else
        error "❌ Failed to add user to video group. Try: sudo usermod -a -G video $USER"
    fi
fi

# Also ensure dialout group for some camera devices
if ! groups "$USER" | grep -q dialout; then
    info "Adding user to 'dialout' group (for some camera devices)..."
    if sudo usermod -a -G dialout "$USER" 2>/dev/null; then
        success "User added to dialout group ✓"
    fi
fi

# ── Step 8: System-wide launcher ─────────────────────────────
step "Step 8 — Creating System Launcher"

LAUNCHER_BIN="/usr/local/bin/robocam"
info "Creating system launcher: $LAUNCHER_BIN"
sudo tee "$LAUNCHER_BIN" > /dev/null << LAUNCHER_BIN_EOF
#!/bin/bash
# RoboNeT Camera Tool — System Launcher
exec bash "$INSTALL_DIR/run_robocam.sh" "\$@"
LAUNCHER_BIN_EOF
sudo chmod +x "$LAUNCHER_BIN"
success "System launcher created: robocam"

# ── Step 9: Camera detection check ───────────────────────────
step "Step 9 — Verifying libcamera Setup"

info "Checking if libcamera is operational..."
if command -v libcamera-hello &>/dev/null; then
    if libcamera-hello --list-cameras &>/dev/null; then
        success "✓ libcamera is working"
    else
        warn "⚠️  libcamera installed but not responding"
        warn "This may require a system reboot to initialize properly."
    fi
else
    warn "⚠️  libcamera command tools not found"
    warn "Installing libcamera-tools..."
    if sudo apt install -y libcamera-tools -qq 2>/dev/null; then
        success "libcamera-tools installed ✓"
    else
        warn "Could not install libcamera-tools via apt"
        warn "You may need to install manually: sudo apt install -y libcamera-tools"
    fi
fi

# ── Step 10: Camera detection check ───────────────────────────
step "Step 10 — Camera Detection Test"

echo "  Scanning v4l2 devices..."
echo ""
V4L_OUT=$(v4l2-ctl --list-devices 2>/dev/null || echo "  (v4l2-ctl not available)")
if [ -z "$V4L_OUT" ]; then
    warn "No v4l2 devices found. Make sure your camera is connected."
else
    echo "$V4L_OUT" | sed 's/^/    /'
fi

echo ""
echo "  Scanning libcamera devices..."
echo ""
LIBCAM_OUT=$(libcamera-hello --list-cameras 2>&1 | grep -v "^$" | head -10 || echo "  (libcamera-hello not available)")
echo "$LIBCAM_OUT" | sed 's/^/    /'

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────"
echo -e "${GREEN}${BOLD}"
echo "  ✅  Installation Complete!"
echo -e "${NC}"
echo ""
echo -e "  ${BOLD}� What You Just Installed:${NC}"
echo ""
echo "    ✓ Python 3 with Tkinter GUI"
echo "    ✓ OpenCV camera library"
echo "    ✓ libcamera runtime & development"
echo "    ✓ GStreamer tools & plugins"
echo "    ✓ Camera device detection tools"
echo ""
echo -e "  ${BOLD}⚠️  CSI Camera Support:${NC}"
echo ""
echo "    Ubuntu 22.04 doesn't have libcamera in repos."
echo "    To enable CSI cameras, build from source:"
echo ""
echo "    → bash ~/Robocam/build_libcamera.sh (~15 minutes)"
echo "    → source ~/.bashrc"
echo "    → robocam"
echo ""
echo "    Alternative: Use Raspberry Pi OS (has full support)"
echo ""
echo -e "  ${BOLD}Next Steps (REQUIRED):${NC}"
echo ""
echo "    ${YELLOW}1. REBOOT YOUR SYSTEM:${NC}"
echo "       ${CYAN}sudo reboot${NC}"
echo ""
echo "       (This initializes camera permissions and firmware)"
echo ""
echo "    ${YELLOW}2. AFTER REBOOT, launch the tool:${NC}"
echo "       ${CYAN}robocam${NC}  (from anywhere)"
echo ""
echo "-"
echo ""
echo -e "  ${BOLD}📸 Alternative launch methods:${NC}"
echo ""
echo -e "    ${CYAN}bash ~/robocam/run_robocam.sh${NC}"
echo -e "    ${CYAN}Desktop → RoboNeT Camera Tool.desktop${NC}"
echo ""
echo -e "  ${BOLD}📁 Output location:${NC}  ${CYAN}~/robocam_output/${NC}"
echo ""
echo "────────────────────────────────────────────────────────────"
echo -e "  ${CYAN}Tip: If camera still doesn't work:${NC}"
echo "    Run: ${CYAN}bash ~/Robocam/check_libcamera.sh${NC}"
echo "────────────────────────────────────────────────────────────"
echo ""
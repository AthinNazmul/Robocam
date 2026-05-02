#!/bin/bash
# ============================================================
#  RoboNeT Camera Tool — Installer
#  Author : Fahim Hafiz | United International University
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

# ── Step 1: System check ─────────────────────────────────────
step "Step 1 — System Check"

# OS check
if command -v lsb_release &>/dev/null; then
    OS_VER=$(lsb_release -rs)
    OS_NAME=$(lsb_release -ds)
    if [[ "$OS_VER" == "24.04" ]]; then
        success "OS: $OS_NAME"
    else
        warn "Expected Ubuntu 24.04, found: $OS_NAME"
        warn "Proceeding — some packages may differ on your OS."
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

declare -A PKGS=(
    ["python3-tk"]="Tkinter GUI framework"
    ["python3-pip"]="Python package manager"
    ["python3.12-venv"]="Python virtual environment"
    ["v4l-utils"]="Camera device detection (v4l2)"
    ["libcamera-apps"]="CSI camera support (libcamera)"
)

for pkg in "${!PKGS[@]}"; do
    desc="${PKGS[$pkg]}"
    if dpkg -s "$pkg" &>/dev/null 2>&1; then
        success "$pkg — already installed  ($desc)"
    else
        info "Installing $pkg ($desc)..."
        if sudo apt install -y "$pkg" -qq 2>/dev/null; then
            success "$pkg — installed"
        else
            warn "$pkg — failed to install. Skipping. ($desc)"
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

# ── Step 7: Camera detection check ───────────────────────────
step "Step 7 — Camera Detection Check"

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
LIBCAM_OUT=$(libcamera-hello --list-cameras 2>&1 | grep -v "^$" | head -10 || echo "  (libcamera not available)")
echo "$LIBCAM_OUT" | sed 's/^/    /'

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "────────────────────────────────────────────────────────────"
echo -e "${GREEN}${BOLD}"
echo "  ✅  Installation complete!"
echo -e "${NC}"
echo -e "  ${BOLD}Launch the tool:${NC}"
echo ""
echo -e "    ${CYAN}bash ~/robocam/run_robocam.sh${NC}"
echo ""
echo -e "  ${BOLD}Or from any terminal:${NC}"
echo ""
echo -e "    ${CYAN}cd ~/robocam && source env/bin/activate && python3 robocam.py${NC}"
echo ""
echo -e "  ${BOLD}Photos & videos saved to:${NC}  ${CYAN}~/robocam_output/${NC}"
echo ""
echo -e "  ${YELLOW}⚠️  Requires a desktop session (VNC or physical monitor)${NC}"
echo -e "  ${YELLOW}   The GUI will NOT work over plain SSH.${NC}"
echo ""
echo "────────────────────────────────────────────────────────────"
echo ""
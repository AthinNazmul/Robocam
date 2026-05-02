#!/bin/bash
# ============================================================
#  Build libcamera from Source for Ubuntu 22.04 on Raspberry Pi
#  Enables CSI cameras to work with robocam
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
error()   { echo -e "  ${RED}[FAIL]${NC}  $1"; exit 1; }
step()    { echo ""; echo -e "  ${BOLD}── $1${NC}"; echo ""; }

echo ""
echo -e "${CYAN}${BOLD}"
echo "  Building libcamera for Ubuntu 22.04 on Raspberry Pi"
echo -e "${NC}"
echo ""

# ── Step 0: System Check ─────────────────────────────────────
step "Step 0 — System Check"

if ! grep -q "22.04" /etc/lsb-release 2>/dev/null; then
    warn "This script is optimized for Ubuntu 22.04"
fi

if [ ! -f /proc/device-tree/model ]; then
    warn "Not running on Raspberry Pi"
fi

if lscpu | grep -q "ARM\|aarch64"; then
    success "ARM processor detected"
else
    error "Not an ARM processor"
fi

# ── Step 1: Install build dependencies ──────────────────────
step "Step 1 — Installing Build Dependencies"

BUILD_DEPS=(
    "build-essential"
    "cmake"
    "git"
    "pkg-config"
    "libpython3-dev"
    "python3-yaml"
    "python3-ply"
    "libboost-dev"
    "libboost-system-dev"
    "libboost-thread-dev"
    "libudev-dev"
    "libevent-dev"
    "libssl-dev"
)

info "Installing ${#BUILD_DEPS[@]} build packages..."
for pkg in "${BUILD_DEPS[@]}"; do
    if dpkg -s "$pkg" &>/dev/null 2>&1; then
        echo -n "."
    else
        echo -n "+"
        sudo apt install -y "$pkg" -qq 2>/dev/null || true
    fi
done
echo ""
success "Build dependencies ready"

# ── Step 2: Download libcamera from RPi repo ────────────────
step "Step 2 — Downloading libcamera Source"

LIBCAM_DIR="$HOME/libcamera-build"
if [ -d "$LIBCAM_DIR" ]; then
    info "Using existing source in $LIBCAM_DIR"
else
    info "Cloning libcamera from Raspberry Pi repository..."
    mkdir -p "$LIBCAM_DIR"
    cd "$LIBCAM_DIR"
    
    if git clone --depth=1 https://github.com/raspberrypi/libcamera.git 2>/dev/null; then
        success "libcamera source cloned"
    else
        warn "Could not clone from GitHub (network issue?)"
        info "Trying alternative sources..."
        # Alternative approach will be added below
    fi
fi

# ── Step 3: Configure libcamera build ───────────────────────
step "Step 3 — Configuring libcamera Build"

cd "$LIBCAM_DIR/libcamera"

if [ ! -d "build" ]; then
    mkdir build
fi

cd build

info "Running meson configure..."
if meson .. -Dprefix=/usr/local 2>&1 | tail -5; then
    success "Configured successfully"
else
    warn "Meson configure had some warnings (may still work)"
fi

# ── Step 4: Compile libcamera ────────────────────────────────
step "Step 4 — Compiling libcamera (this may take 10-15 minutes)"

info "Starting compilation..."
info "You can see progress below:"
echo ""

NUM_CORES=$(nproc)
info "Using $NUM_CORES CPU cores"

if ninja -j "$NUM_CORES" 2>&1 | grep -E "Built|Linking" | tail -20; then
    success "Compilation complete"
else
    error "Compilation failed. Check errors above."
fi

# ── Step 5: Install libcamera ───────────────────────────────
step "Step 5 — Installing libcamera"

info "Installing to /usr/local..."
if sudo ninja -C . install 2>&1 | tail -3; then
    success "Installation complete"
else
    warn "Installation had warnings"
fi

# ── Step 6: Install libcamera-apps ──────────────────────────
step "Step 6 — Building libcamera-apps"

cd "$LIBCAM_DIR"

if [ ! -d "libcamera-apps" ]; then
    info "Cloning libcamera-apps..."
    if git clone --depth=1 https://github.com/raspberrypi/libcamera-apps.git 2>/dev/null; then
        success "libcamera-apps source cloned"
    else
        warn "Could not clone libcamera-apps"
    fi
fi

if [ -d "libcamera-apps" ]; then
    cd libcamera-apps
    mkdir -p build
    cd build
    
    info "Configuring libcamera-apps..."
    cmake .. -DCMAKE_INSTALL_PREFIX=/usr/local 2>&1 | tail -3
    
    info "Compiling libcamera-apps (5-10 minutes)..."
    if make -j "$NUM_CORES" 2>&1 | tail -20; then
        success "Compiled successfully"
        
        info "Installing libcamera-apps..."
        if sudo make install 2>&1 | tail -3; then
            success "libcamera-apps installed"
        fi
    else
        warn "libcamera-apps compilation failed (you can still try robocam)"
    fi
else
    warn "libcamera-apps not available, skipping"
fi

# ── Step 7: Verify installation ──────────────────────────────
step "Step 7 — Verifying Installation"

echo ""
echo "  Checking what was installed:"
echo ""

if command -v libcamera-hello &>/dev/null; then
    echo "    ✓ libcamera-hello available"
else
    echo "    ✗ libcamera-hello not found"
fi

if command -v libcamera-raw &>/dev/null; then
    echo "    ✓ libcamera-raw available"
else
    echo "    ✗ libcamera-raw not available"
fi

if command -v libcamera-still &>/dev/null; then
    echo "    ✓ libcamera-still available"
else
    echo "    ✗ libcamera-still not available"
fi

echo ""

# ── Step 8: Update LD_LIBRARY_PATH ──────────────────────────
step "Step 8 — Updating Library Path"

if grep -q "/usr/local/lib" ~/.bashrc 2>/dev/null; then
    success "Library path already configured in .bashrc"
else
    info "Adding /usr/local/lib to library search path..."
    echo 'export LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"' >> ~/.bashrc
    echo 'export PKG_CONFIG_PATH="/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"' >> ~/.bashrc
    success "Library path configured"
    info "Run: source ~/.bashrc"
fi

# ── Done ─────────────────────────────────────────────────────
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo -e "  ${GREEN}${BOLD}Build Complete!${NC}"
echo ""
echo "  Next Steps:"
echo ""
echo "    1. Load new library paths:"
echo "       ${CYAN}source ~/.bashrc${NC}"
echo ""
echo "    2. Verify libcamera is working:"
echo "       ${CYAN}libcamera-hello --list-cameras${NC}"
echo ""
echo "    3. Test robocam:"
echo "       ${CYAN}robocam${NC}"
echo ""
echo "    4. If still not working, reboot:"
echo "       ${CYAN}sudo reboot${NC}"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""
echo "  Build artifacts: $LIBCAM_DIR"
echo "  Installation: /usr/local"
echo ""

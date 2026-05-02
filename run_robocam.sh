#!/bin/bash
# ============================================================
#  RoboNeT Camera Tool — Launcher
#  Automatically handles venv activation and setup
# ============================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$HOME/robocam"
VENV_DIR="$INSTALL_DIR/env"
TOOL_PATH="$INSTALL_DIR/robocam.py"
REPO_TOOL="$SCRIPT_DIR/src/robocam.py"

# ── Colors ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC}  $1"; }
success() { echo -e "${GREEN}[ OK ]${NC}  $1"; }
error()   { echo -e "${RED}[FAIL]${NC}  $1"; exit 1; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $1"; }

# ── Check if installation is complete ───────────────────────
if [ ! -f "$VENV_DIR/bin/activate" ] || [ ! -f "$TOOL_PATH" ]; then
    echo ""
    echo -e "${BOLD}🤖  RoboNeT Camera Tool${NC}"
    echo ""
    error "Installation not complete or corrupted. Run the installer:
    
    cd ~/Robocam
    bash install.sh
    
Then come back and try: robocam"
fi

# ── Update tool if repo version is newer (fixes) ────────────
if [ -f "$REPO_TOOL" ] && [ "$REPO_TOOL" -nt "$TOOL_PATH" ]; then
    info "Updating tool from latest fixes..."
    cp "$REPO_TOOL" "$TOOL_PATH"
fi

# ── Activate virtual environment ────────────────────────────
source "$VENV_DIR/bin/activate"

# ── Run the tool ────────────────────────────────────────────
exec python3 "$TOOL_PATH" "$@"
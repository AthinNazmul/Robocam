#!/bin/bash
# ============================================================
#  RoboNeT — If It Crashes, Run This
# ============================================================

echo ""
echo "🔧 RoboNeT Camera Tool Repair"
echo "============================="
echo ""
echo "If you're seeing segmentation faults or crashes, run this to fix:"
echo ""

cd ~/Robocam

echo "Step 1: Pulling latest updates..."
git pull origin main 2>/dev/null || echo "  (Not a git repo, skipping)"

echo ""
echo "Step 2: Reinstalling (handles all fixes)..."
bash install.sh

echo ""
echo "Step 3: Try again..."
echo ""
echo "Run:  robocam"
echo ""


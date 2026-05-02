#!/bin/bash
# Copy this and run on your Pi to get the fix

echo "🔧 RoboNeT — Applying Pi TTK Fix"
echo "================================"
echo ""

# Step 1: Copy fixed file
echo "Step 1: Copying fixed robocam.py..."
cp ~/Robocam/src/robocam.py ~/robocam/robocam.py
echo "✓ Done"
echo ""

# Step 2: Test
echo "Step 2: Testing..."
python3 -m py_compile ~/robocam/robocam.py && echo "✓ File OK" || echo "✗ FAILED"
echo ""

# Step 3: Run
echo "Step 3: Launching robocam..."
echo ""
robocam


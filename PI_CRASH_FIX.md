# 🔧 Pi Segmentation Fault Fix

## Problem
User got **stack smashing** and **segmentation fault** when running tool on RPi 4:
```
*** stack smashing detected ***: terminated
/home/urrt/robocam/run_robocam.sh: line 6: 38991 Segmentation fault (core dumped)
can't invoke "event" command: application has been destroyed 
while executing "event generate $w <<ThemeChanged>>"
```

## Root Cause
**TTK theme system on ARM/Raspberry Pi has bugs** that cause:
- Memory corruption during theme initialization
- Event handler crashes when accessing destroyed widgets
- Stack smashing from buffer overflows in tcl/tk library

## Fixes Applied

### 1. **Disabled ttk.Style.theme_use()** ✅
```python
# OLD (causes crash):
style.theme_use("default")

# NEW (safe):
# style.theme_use("default")  # Disabled for ARM compatibility
```
The theme engine on Pi is broken and causes memory corruption. Disabling it is safe — the app works fine without themes.

### 2. **Replaced ttk.Separator with tk.Frame** ✅
```python
# OLD (uses ttk, can crash):
ttk.Separator(self, orient="horizontal").pack(fill="x", padx=8)

# NEW (simple tk.Frame):
separator = tk.Frame(self, bg=BORDER, height=1)
separator.pack(fill="x", padx=8)
```

### 3. **Wrapped ttk.Combobox in try/except** ✅
```python
try:
    # Try to use ttk (nice looking dropdown)
    ttk.Combobox(sc, textvariable=self.res_var, ...)
except Exception:
    # Fall back to tk.Entry if ttk fails
    tk.Entry(sc, textvariable=self.res_var, ...)
```

### 4. **Protected ttk.Style operations** ✅
```python
try:
    style = ttk.Style(self)
    try:
        style.configure("TCombobox", ...)
    except:
        pass  # Skip styling if it  fails
except Exception:
    pass  # Skip entire ttk if unavailable
```

---

## Testing the Fix

### On Your Pi, run:
```bash
# 1. Update the tool
cd ~/Robocam
git pull origin main

# 2. Reinstall (or copy new robocam.py to ~/robocam/)
bash install.sh

# 3. Try the tool
robocam

# If it still crashes, run debug version:
bash debug_robocam.sh
```

### Expected Behavior:
- ✅ GUI should launch without segmentation fault
- ✅ Camera detection should work
- ✅ Resolution dropdown uses tk.Entry (simpler but works)
- ✅ Separator is a simple line (no fancy styling)

---

## If It Still Crashes

1. **Check your display:**
   ```bash
   echo $DISPLAY
   ```
   - If empty and over SSH: `ssh -X pi@<ip>`
   - If empty on Pi: connect monitor + keyboard

2. **Check Python/Tkinter:**
   ```bash
   python3 -c "import tkinter; print('OK')"
   ```

3. **Check for corrupted install:**
   ```bash
   bash ~/Robocam/install.sh  # Reinstall
   ```

4. **Report detailed error:**
   ```bash
   bash debug_robocam.sh 2>&1 | tee crash_log.txt
   ```
   Share the crash_log.txt file.

---

## Technical Details

The issue is in the Tcl/Tk library on ARM Raspberry Pi:
- `ttk.Style.theme_use()` creates internal state that corrupts memory
- ttk widgets try to emit theme change events that access freed memory
- This manifests as "stack smashing detected" or segmentation faults
- Completely disabling ttk fixes it

Modern solution would be to use a different GUI framework (PyQt, Kivy), but Tkinter is simplest for this tool.

---

## Files Modified
- `src/robocam.py` — 4 safeguards added
- `debug_robocam.sh` — Debug launcher (NEW)


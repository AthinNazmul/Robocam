#!/usr/bin/env python3
"""
RoboNeT Camera Tool
====================
A lightweight Tkinter GUI tool for detecting and using camera modules on
Raspberry Pi running Ubuntu 22.04+. Supports:
  - CSI cameras (Pi Camera 1.3, IMX219) via libcamera / v4l2
  - USB cameras via OpenCV / v4l2
  - Auto-detection of all available camera devices
  - Live preview, photo capture, video recording

Requirements:
  pip install opencv-python pillow
  sudo apt install v4l-utils libcamera-apps -y

Author : Nazmul Hasan Athin | 
Org    : United International University — CENTER
"""

import os
import sys
import time
import threading
import queue
import subprocess
import datetime
import re

# ── Pre-Tkinter dependency checks ───────────────────────────
# These MUST succeed before importing tkinter to avoid segfaults
try:
    import cv2
except ImportError:
    print("[ERROR] OpenCV not found.")
    print("        Fix: pip install opencv-python")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
except ImportError:
    print("[ERROR] Pillow not found.")
    print("        Fix: pip install pillow")
    sys.exit(1)

# ── Check Display/Tkinter BEFORE importing tkinter ──────────
# Failure here = likely "Segmentation fault" on headless systems
try:
    import tkinter as tk
    from tkinter import filedialog
    
    # Verify Tk can initialize (requires X11 display on Linux/ARM)
    # This will fail on headless systems or missing DISPLAY
    _test_root = tk.Tk()
    _test_root.destroy()
    
    # Detect if running on Raspberry Pi/ARM
    # If yes, DON'T import ttk (causes crashes from tcl/tk bugs)
    IS_ARM_PI = False
    try:
        with open('/proc/device-tree/model', 'r') as f:
            model = f.read()
            IS_ARM_PI = 'Raspberry' in model or 'bcm' in model.lower()
    except:
        pass
    
    # Only import ttk if NOT on Pi
    if IS_ARM_PI:
        ttk = None  # Disable ttk completely
    else:
        try:
            from tkinter import ttk
        except:
            ttk = None
            
except Exception as e:
    print("[ERROR] Tkinter GUI initialization failed.")
    print("        Possible causes:")
    print("        • Tkinter package not installed (install python3-tk via apt)")
    print("        • No X11 display server (use SSH -X or set up DISPLAY)")
    print("        • Not a terminal environment")
    print(f"        • Details: {e}")
    print()
    print("[FIX] On Raspberry Pi:")
    print("     1. sudo apt install python3-tk")
    print("     2. Use SSH with X11 forwarding: ssh -X pi@<ip>")
    print("     See TROUBLESHOOTING.md for more options.")
    sys.exit(1)

# ── Force V4L2 backend on Linux (more stable on ARM) ─────────
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

# ─────────────────────────────────────────────────────────────
#  THEME & CONSTANTS
# ─────────────────────────────────────────────────────────────
BG_DARK      = "#0f1117"
BG_PANEL     = "#1a1d27"
BG_CARD      = "#22263a"
ACCENT       = "#00d4aa"
ACCENT2      = "#7c6af7"
DANGER       = "#ff4f5e"
WARNING      = "#ffb547"
TEXT_PRIMARY = "#e8eaf0"
TEXT_MUTED   = "#6b7280"
BORDER       = "#2e3347"
FONT_MONO    = ("Courier New", 10)

PREVIEW_W    = 640
PREVIEW_H    = 480
SAVE_DIR     = os.path.expanduser("~/robocam_output")


# ─────────────────────────────────────────────────────────────
#  CAMERA DETECTION
#  Pure logic — no Tkinter calls. Safe to run in any thread.
# ─────────────────────────────────────────────────────────────

def has_libcamera_support():
    """Check if libcamera is available and working."""
    try:
        result = subprocess.run(
            ["libcamera-hello", "--list-cameras"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0 and "Available cameras" in (result.stdout + result.stderr)
    except Exception:
        return False


def detect_cameras():
    """
    Scan for all connected cameras via v4l2 + libcamera.
    Returns list of dicts: {index, name, type, device}
    Filters out virtual devices (codecs, ISP processors).
    """
    cameras      = []
    seen_indices = set()
    print("[robocam] Starting camera detection...", file=sys.stderr)

    # ── v4l2 scan ────────────────────────────────────────────
    try:
        result = subprocess.run(
            ["v4l2-ctl", "--list-devices"],
            capture_output=True, text=True, timeout=5
        )
        current_name = "Unknown Camera"
        
        # Devices to SKIP (not real cameras)
        skip_devices = ["bcm2835-codec", "bcm2835-isp", "rpivid", "bcm2711"]
        
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            if not line.startswith("/dev/"):
                current_name = line.rstrip(":")
            elif line.startswith("/dev/video"):
                # SKIP known virtual devices
                if any(skip in current_name.lower() for skip in skip_devices):
                    print(f"[robocam] Skipping {line} ({current_name})", file=sys.stderr)
                    continue
                    
                m = re.search(r"/dev/video(\d+)", line)
                if not m:
                    continue
                idx = int(m.group(1))
                if idx in seen_indices:
                    continue
                
                seen_indices.add(idx)
                
                # Determine camera type first
                csi_kw   = ["mmal", "unicam", "imx", "ov", "csi", "rpicam", "camera", "pisp"]
                cam_type = "CSI" if any(
                    k in current_name.lower() for k in csi_kw
                ) else "USB"
                
                # For CSI cameras, trust libcamera will handle it
                # For USB cameras, verify they can read frames
                if cam_type == "CSI":
                    print(f"[robocam] Found CSI camera: {line} ({current_name})", file=sys.stderr)
                    cameras.append({
                        "index":  idx,
                        "name":   current_name,
                        "type":   cam_type,
                        "device": f"/dev/video{idx}",
                    })
                else:
                    # USB camera - test it works
                    print(f"[robocam] Testing USB camera {line} ({current_name})...", file=sys.stderr)
                    cap = cv2.VideoCapture(idx, cv2.CAP_V4L2)
                    if not cap.isOpened():
                        cap.release()
                        print(f"[robocam]   → Can't open USB camera", file=sys.stderr)
                        continue
                    ret, _ = cap.read()
                    cap.release()
                    if not ret:
                        print(f"[robocam]   → Can't read from USB camera", file=sys.stderr)
                        continue
                    print(f"[robocam]   → USB camera OK", file=sys.stderr)
                    cameras.append({
                        "index":  idx,
                        "name":   current_name,
                        "type":   cam_type,
                        "device": f"/dev/video{idx}",
                    })
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # ── Fallback: probe /dev/video0-9 directly ───────────────
    if not cameras:
        print(f"[robocam] Using fallback camera detection", file=sys.stderr)
        for i in range(10):
            if i in seen_indices:
                continue
            if not os.path.exists(f"/dev/video{i}"):
                continue
            # Assume it's a camera if device exists and can open
            # (might be CSI which needs libcamera, so don't test frame read)
            cap = cv2.VideoCapture(i, cv2.CAP_V4L2)
            if cap.isOpened():
                cap.release()
                cameras.append({
                    "index":  i,
                    "name":   f"Camera {i}",
                    "type":   "CSI",  # Assume CSI if unknown
                    "device": f"/dev/video{i}",
                })
                seen_indices.add(i)

    # ── libcamera check (Pi 5 / Ubuntu 22+) ──────────────────
    try:
        result = subprocess.run(
            ["libcamera-hello", "--list-cameras"],
            capture_output=True, text=True, timeout=6
        )
        combined = result.stdout + result.stderr
        has_csi  = ("Available cameras" in combined
                    or "imx" in combined.lower()
                    or "ov"  in combined.lower())
        if has_csi:
            print(f"[robocam] libcamera detected CSI camera", file=sys.stderr)
            tagged = False
            for cam in cameras:
                if cam["type"] == "CSI":
                    if "(libcamera)" not in cam["name"]:
                        cam["name"] += " (libcamera)"
                    tagged = True
            if not tagged:
                cameras.append({
                    "index":  99,
                    "name":   "CSI Camera (libcamera)",
                    "type":   "CSI",
                    "device": "libcamera",
                })
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    print(f"[robocam] Camera detection complete: found {len(cameras)} camera(s)", file=sys.stderr)
    
    # Check if CSI camera found but libcamera not available
    has_csi = any(cam["type"] == "CSI" for cam in cameras)
    has_libcam = has_libcamera_support()
    if has_csi and not has_libcam:
        print(f"[robocam] ⚠️  WARNING: CSI camera detected but libcamera not working!", file=sys.stderr)
        print(f"[robocam]    Solution: bash ~/Robocam/build_libcamera.sh (builds from Raspberry Pi source)", file=sys.stderr)
    
    return cameras


def open_camera(cam_info, width=640, height=480):
    """
    Open and return a cv2.VideoCapture.
    For CSI cameras, tries libcamera first, then falls back to v4l2.
    For USB cameras, uses v4l2 directly.
    """
    print(f"[robocam] Opening camera: {cam_info['name']} (type={cam_info['type']}, idx={cam_info['index']})", file=sys.stderr)
    
    if cam_info["device"] == "libcamera":
        # Explicit libcamera device
        print(f"[robocam]   → Trying libcamera pipeline...", file=sys.stderr)
        pipeline = (
            "libcamerasrc ! "
            f"video/x-raw,width={width},height={height},framerate=30/1 ! "
            "videoconvert ! appsink drop=true max-buffers=2 sync=false"
        )
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print(f"[robocam]   → OK (libcamera/GStreamer)", file=sys.stderr)
                return cap
            cap.release()
            print(f"[robocam]   → Pipeline opened but can't read frames", file=sys.stderr)
        print(f"[robocam]   → Failed, trying v4l2 fallback...", file=sys.stderr)
        # Fallback to index 0
        cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
        return cap

    # For CSI cameras, try libcamera + GStreamer first
    if cam_info["type"] == "CSI":
        print(f"[robocam]   → CSI camera, trying libcamera GStreamer...", file=sys.stderr)
        try:
            pipeline = (
                "libcamerasrc ! "
                f"video/x-raw,width={width},height={height},framerate=30/1 ! "
                "videoconvert ! appsink drop=true max-buffers=2 sync=false"
            )
            cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
            if cap.isOpened():
                # Test if we can actually read
                ret, _ = cap.read()
                if ret:
                    print(f"[robocam]   → OK (libcamera/GStreamer)", file=sys.stderr)
                    return cap
                else:
                    print(f"[robocam]   → GStreamer opened but can't read (libcamera-plugin missing?)", file=sys.stderr)
                    cap.release()
        except Exception as e:
            print(f"[robocam]   → GStreamer error: {e}", file=sys.stderr)
        
        # Try libcamera-raw directly as last resort for CSI
        print(f"[robocam]   → Trying libcamera-raw alternative...", file=sys.stderr)
        try:
            import subprocess as sp
            result = sp.run(["which", "libcamera-raw"], capture_output=True)
            if result.returncode == 0:
                # libcamera-raw available, but we can't use it directly with OpenCV
                # So this is just informational
                print(f"[robocam]   → libcamera-raw command exists, but using v4l2 fallback", file=sys.stderr)
        except Exception:
            pass
    
    # Fall back to v4l2 (works for USB, may not work for CSI without libcamera)
    print(f"[robocam]   → Trying v4l2 backend (index {cam_info['index']})...", file=sys.stderr)
    cap = cv2.VideoCapture(cam_info["index"], cv2.CAP_V4L2)
    if cap.isOpened():
        # Try to read a frame to verify it works
        ret, _ = cap.read()
        if ret:
            print(f"[robocam]   → OK (v4l2) — Camera working!", file=sys.stderr)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            return cap
        else:
            print(f"[robocam]   ⚠️  v4l2 opened but can't read frames", file=sys.stderr)
            if cam_info["type"] == "CSI":
                print(f"[robocam]", file=sys.stderr)
                print(f"[robocam]   ❌ CSI Camera Cannot Read Frames", file=sys.stderr)
                print(f"[robocam]", file=sys.stderr)
                print(f"[robocam]   SOLUTION: Build libcamera from source", file=sys.stderr)
                print(f"[robocam]", file=sys.stderr)
                print(f"[robocam]   Command: bash ~/Robocam/build_libcamera.sh", file=sys.stderr)
                print(f"[robocam]   Time: ~15 minutes on Pi 4", file=sys.stderr)
                print(f"[robocam]   Then: source ~/.bashrc && robocam", file=sys.stderr)
                print(f"[robocam]", file=sys.stderr)
                print(f"[robocam]   This builds libcamera + tools from Raspberry Pi's", file=sys.stderr)
                print(f"[robocam]   official source code, enabling full CSI support.", file=sys.stderr)
    else:
        print(f"[robocam]   ✗ Failed to open device", file=sys.stderr)
    
    # Try to set props anyway (might help)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cap


# ─────────────────────────────────────────────────────────────
#  FRAME GRABBER THREAD
#
#  KEY DESIGN: This thread ONLY reads raw numpy arrays from the
#  camera and puts them into a queue. It NEVER touches any
#  Tkinter object or creates any ImageTk.PhotoImage.
#
#  Reason: ImageTk.PhotoImage must be created on the main
#  thread. Creating it in a background thread causes a
#  segmentation fault on Linux/ARM (Ubuntu + Raspberry Pi).
# ─────────────────────────────────────────────────────────────
class FrameGrabber(threading.Thread):
    def __init__(self, cap, frame_queue, stop_event):
        super().__init__(daemon=True)
        self.cap        = cap
        self.queue      = frame_queue   # queue.Queue(maxsize=2)
        self.stop_event = stop_event

    def run(self):
        while not self.stop_event.is_set():
            if not self.cap or not self.cap.isOpened():
                break
            ret, frame = self.cap.read()
            if not ret:
                # None signals a read error to the main thread
                try:
                    self.queue.put_nowait(None)
                except queue.Full:
                    pass
                break
            # Drop oldest frame if main thread can't keep up
            try:
                self.queue.put_nowait(frame)
            except queue.Full:
                try:
                    self.queue.get_nowait()
                    self.queue.put_nowait(frame)
                except queue.Empty:
                    pass
            time.sleep(0.01)


# ─────────────────────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────────────────────
class RoboCamApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("RoboNeT Camera Tool")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)

        # Camera
        self.cameras      = []
        self.selected_cam = None
        self.cap          = None

        # Grabber thread
        self.frame_queue  = queue.Queue(maxsize=2)
        self.stop_event   = threading.Event()
        self.grabber      = None

        # Recording
        self.recording      = False
        self.video_writer   = None
        self.rec_start_time = None

        # Frame state (main thread only)
        self.current_frame = None
        self.photo_count   = 0
        self._poll_id      = None

        # FPS
        self._fps_frames = 0
        self._fps_time   = time.time()

        os.makedirs(SAVE_DIR, exist_ok=True)

        self._build_ui()
        self._apply_styles()
        self.after(200, self._auto_detect)
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI ────────────────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        topbar = tk.Frame(self, bg=BG_DARK, pady=6)
        topbar.pack(fill="x", padx=16)

        tk.Label(topbar, text="🤖  RoboNeT Camera Tool",
                 bg=BG_DARK, fg=ACCENT,
                 font=("Courier New", 15, "bold")).pack(side="left")
        tk.Label(topbar, text="Ubuntu 22+ · Raspberry Pi",
                 bg=BG_DARK, fg=TEXT_MUTED,
                 font=FONT_MONO).pack(side="left", padx=12)

        self.status_dot = tk.Label(topbar, text="●", bg=BG_DARK,
                                   fg=TEXT_MUTED,
                                   font=("TkDefaultFont", 14))
        self.status_dot.pack(side="right")
        self.status_lbl = tk.Label(topbar, text="No camera active",
                                   bg=BG_DARK, fg=TEXT_MUTED, font=FONT_MONO)
        self.status_lbl.pack(side="right", padx=6)

        # Use tk.Frame instead of ttk.Separator for ARM compatibility
        separator = tk.Frame(self, bg=BORDER, height=1)
        separator.pack(fill="x", padx=8)

        main = tk.Frame(self, bg=BG_DARK)
        main.pack(fill="both", expand=True, padx=12, pady=8)

        left = tk.Frame(main, bg=BG_PANEL, width=230)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        self._build_left_panel(left)

        right = tk.Frame(main, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)
        self._build_preview(right)
        self._build_controls(right)

        self._build_log()

    def _build_left_panel(self, parent):
        self._section_label(parent, "CAMERA DETECTION")

        self.detect_btn = self._btn(parent, "🔍  Scan for Cameras",
                                    self._auto_detect, ACCENT)
        self.detect_btn.pack(fill="x", padx=10, pady=(4, 8))

        lf = tk.Frame(parent, bg=BG_CARD)
        lf.pack(fill="x", padx=10, pady=4)
        tk.Label(lf, text="Available Cameras", bg=BG_CARD,
                 fg=TEXT_MUTED, font=("Courier New", 8)).pack(
            anchor="w", padx=8, pady=(6, 2))
        self.cam_listbox = tk.Listbox(
            lf, bg=BG_CARD, fg=TEXT_PRIMARY,
            selectbackground=ACCENT2, selectforeground="white",
            font=FONT_MONO, height=6, bd=0,
            highlightthickness=0, activestyle="none"
        )
        self.cam_listbox.pack(fill="x", padx=4, pady=(0, 6))
        self.cam_listbox.bind("<<ListboxSelect>>", self._on_cam_select)

        self._section_label(parent, "CAMERA INFO")
        info_card = tk.Frame(parent, bg=BG_CARD)
        info_card.pack(fill="x", padx=10, pady=4)
        self.info_labels = {}
        for key in ["Type", "Device", "Index"]:
            row = tk.Frame(info_card, bg=BG_CARD)
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=f"{key}:", bg=BG_CARD,
                     fg=TEXT_MUTED, font=("Courier New", 8),
                     width=7, anchor="w").pack(side="left")
            lbl = tk.Label(row, text="—", bg=BG_CARD,
                           fg=ACCENT, font=("Courier New", 8), anchor="w")
            lbl.pack(side="left")
            self.info_labels[key] = lbl
        tk.Frame(info_card, bg=BG_CARD, height=6).pack()

        self.connect_btn = self._btn(parent, "▶  Connect Camera",
                                     self._connect_camera, ACCENT2)
        self.connect_btn.pack(fill="x", padx=10, pady=6)
        self.connect_btn.config(state="disabled")

        self.disconnect_btn = self._btn(parent, "■  Disconnect",
                                        self._disconnect_camera, DANGER)
        self.disconnect_btn.pack(fill="x", padx=10, pady=(0, 6))
        self.disconnect_btn.config(state="disabled")

        self._section_label(parent, "SETTINGS")
        sc = tk.Frame(parent, bg=BG_CARD)
        sc.pack(fill="x", padx=10, pady=4)
        tk.Label(sc, text="Resolution", bg=BG_CARD,
                 fg=TEXT_MUTED, font=("Courier New", 8)).pack(
            anchor="w", padx=8, pady=(6, 0))
        self.res_var = tk.StringVar(value="640x480")
        
        # Try to use ttk.Combobox, but fall back to tk.Entry
        if ttk is not None:
            try:
                ttk.Combobox(sc, textvariable=self.res_var,
                             values=["320x240", "640x480", "1280x720", "1920x1080"],
                             state="readonly", width=18).pack(padx=8, pady=4, anchor="w")
            except Exception:
                tk.Entry(sc, textvariable=self.res_var, width=18,
                         bg=BG_CARD, fg=TEXT_PRIMARY, relief="flat").pack(padx=8, pady=4, anchor="w")
        else:
            # TTK not available (Pi), use simple Entry
            tk.Entry(sc, textvariable=self.res_var, width=18,
                     bg=BG_CARD, fg=TEXT_PRIMARY, relief="flat").pack(padx=8, pady=4, anchor="w")
        tk.Label(sc, text="Save Folder", bg=BG_CARD,
                 fg=TEXT_MUTED, font=("Courier New", 8)).pack(anchor="w", padx=8)
        fr = tk.Frame(sc, bg=BG_CARD)
        fr.pack(fill="x", padx=8, pady=(2, 8))
        self.folder_lbl = tk.Label(fr, text="~/robocam_output",
                                    bg=BG_CARD, fg=ACCENT,
                                    font=("Courier New", 7), anchor="w")
        self.folder_lbl.pack(side="left", fill="x", expand=True)
        self._small_btn(fr, "📁", self._choose_folder).pack(side="right")

    def _build_preview(self, parent):
        border = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        border.pack(pady=(0, 8))
        self.preview_canvas = tk.Canvas(
            border, width=PREVIEW_W, height=PREVIEW_H,
            bg=BG_CARD, highlightthickness=0
        )
        self.preview_canvas.pack()
        self.canvas_placeholder = self.preview_canvas.create_text(
            PREVIEW_W // 2, PREVIEW_H // 2,
            text="No camera connected\n\nScan → Select → Connect",
            fill=TEXT_MUTED, font=("Courier New", 13), justify="center"
        )
        self.rec_overlay = self.preview_canvas.create_text(
            12, 12, anchor="nw", text="",
            fill=DANGER, font=("Courier New", 11, "bold")
        )

    def _build_controls(self, parent):
        ctrl = tk.Frame(parent, bg=BG_DARK)
        ctrl.pack(fill="x")
        self.photo_btn = self._btn(ctrl, "📷  Take Photo",
                                   self._take_photo, ACCENT, width=18)
        self.photo_btn.pack(side="left", padx=(0, 6))
        self.photo_btn.config(state="disabled")
        self.rec_btn = self._btn(ctrl, "⏺  Start Recording",
                                 self._toggle_record, DANGER, width=18)
        self.rec_btn.pack(side="left", padx=6)
        self.rec_btn.config(state="disabled")
        self._btn(ctrl, "📂  Open Output",
                  self._open_output_folder, WARNING, width=14).pack(side="right")

        stats = tk.Frame(parent, bg=BG_DARK)
        stats.pack(fill="x", pady=(6, 0))
        self.photo_stat = tk.Label(stats, text="Photos: 0",
                                    bg=BG_DARK, fg=TEXT_MUTED, font=FONT_MONO)
        self.photo_stat.pack(side="left")
        self.rec_stat = tk.Label(stats, text="",
                                  bg=BG_DARK, fg=DANGER, font=FONT_MONO)
        self.rec_stat.pack(side="left", padx=12)
        self.fps_stat = tk.Label(stats, text="",
                                  bg=BG_DARK, fg=TEXT_MUTED, font=FONT_MONO)
        self.fps_stat.pack(side="right")

    def _build_log(self):
        lf = tk.Frame(self, bg=BG_PANEL)
        lf.pack(fill="x", padx=12, pady=(4, 8))
        hdr = tk.Frame(lf, bg=BG_PANEL)
        hdr.pack(fill="x", padx=8, pady=(4, 0))
        tk.Label(hdr, text="SYSTEM LOG", bg=BG_PANEL,
                 fg=TEXT_MUTED, font=("Courier New", 8)).pack(side="left")
        self._small_btn(hdr, "Clear", self._clear_log).pack(side="right")
        self.log_text = tk.Text(
            lf, height=5, bg=BG_DARK, fg=ACCENT,
            font=("Courier New", 9), relief="flat",
            bd=0, state="disabled", wrap="word", highlightthickness=0
        )
        self.log_text.pack(fill="x", padx=8, pady=(2, 8))
        self.log_text.tag_config("info",    foreground=ACCENT)
        self.log_text.tag_config("warn",    foreground=WARNING)
        self.log_text.tag_config("error",   foreground=DANGER)
        self.log_text.tag_config("success", foreground="#4ade80")

    # ── HELPERS ───────────────────────────────────────────────
    def _section_label(self, parent, text):
        tk.Label(parent, text=text, bg=BG_PANEL, fg=TEXT_MUTED,
                 font=("Courier New", 7)).pack(
            anchor="w", padx=10, pady=(10, 2))

    def _btn(self, parent, text, cmd, color, width=None):
        kw = dict(text=text, command=cmd, bg=color, fg=BG_DARK,
                  font=("Courier New", 9, "bold"), relief="flat",
                  cursor="hand2", activebackground=color,
                  activeforeground=BG_DARK, padx=10, pady=6, bd=0)
        if width:
            kw["width"] = width
        return tk.Button(parent, **kw)

    def _small_btn(self, parent, text, cmd):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=BG_CARD, fg=TEXT_MUTED, font=("Courier New", 8),
            relief="flat", cursor="hand2", padx=4, pady=2,
            activebackground=BORDER, activeforeground=TEXT_PRIMARY
        )

    def _apply_styles(self):
        """
        Apply ttk styles only if available.
        On ARM/Pi systems, ttk is disabled to avoid crashes.
        App works fine without ttk styling.
        """
        if ttk is None:
            # TTK disabled - just return, app still works
            return
        
        try:
            style = ttk.Style(self)
            style.configure("TCombobox",
                            fieldbackground=BG_CARD, background=BG_CARD,
                            foreground=TEXT_PRIMARY, selectbackground=ACCENT2,
                            borderwidth=0)
            style.configure("TSeparator", background=BORDER)
        except Exception as e:
            # Even on non-Pi systems, if ttk fails, just skip it
            print(f"[WARN] ttk styling unavailable: {e}", file=sys.stderr)

    def _log(self, msg, level="info"):
        ts = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n", level)
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _clear_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.config(state="disabled")

    def _set_status(self, text, color=TEXT_MUTED):
        self.status_lbl.config(text=text, fg=color)
        self.status_dot.config(fg=color)

    # ── DETECTION ─────────────────────────────────────────────
    def _auto_detect(self):
        self._log("Scanning for cameras...", "info")
        self.detect_btn.config(state="disabled", text="🔄  Scanning...")
        threading.Thread(target=self._detect_worker, daemon=True).start()

    def _detect_worker(self):
        cameras = detect_cameras()
        self.after(0, self._apply_detection_results, cameras)

    def _apply_detection_results(self, cameras):
        self.cameras = cameras
        self.cam_listbox.delete(0, "end")
        if not cameras:
            self._log("No cameras found. Check connections.", "warn")
            self._set_status("No cameras found", WARNING)
        else:
            for cam in cameras:
                icon  = "📷" if cam["type"] == "CSI" else "🔌"
                label = f"{icon} [{cam['type']}] {cam['name'][:24]}"
                self.cam_listbox.insert("end", label)
            self._log(f"Found {len(cameras)} camera(s).", "success")
            self._set_status(f"{len(cameras)} camera(s) detected", ACCENT)
        self.detect_btn.config(state="normal", text="🔍  Scan for Cameras")

    def _on_cam_select(self, event):
        sel = self.cam_listbox.curselection()
        if not sel:
            return
        cam = self.cameras[sel[0]]
        self.selected_cam = cam
        self.info_labels["Type"].config(text=cam["type"])
        self.info_labels["Device"].config(text=cam["device"])
        self.info_labels["Index"].config(text=str(cam["index"]))
        self.connect_btn.config(state="normal")

    # ── CONNECT / DISCONNECT ──────────────────────────────────
    def _connect_camera(self):
        if not self.selected_cam:
            return
        self._disconnect_camera(silent=True)

        self._log(f"Connecting to {self.selected_cam['name']}...", "info")
        w, h    = map(int, self.res_var.get().split("x"))
        self.cap = open_camera(self.selected_cam, width=w, height=h)

        if not self.cap or not self.cap.isOpened():
            msg = "Failed to open camera."
            if self.selected_cam["type"] == "CSI":
                msg += (
                    "\n\n🔧 CSI Camera Setup Required:\n\n"
                    "Build libcamera from source:\n"
                    "   bash ~/Robocam/build_libcamera.sh\n"
                    "   source ~/.bashrc\n"
                    "   robocam\n\n"
                    "This takes ~15 minutes on Pi 4."
                )
            else:
                msg += " Try another USB camera, or check connections."
            self._log(msg, "error")
            self._set_status("Connection failed", DANGER)
            return

        # Start grabber thread
        self.stop_event.clear()
        self.frame_queue = queue.Queue(maxsize=2)
        self.grabber     = FrameGrabber(self.cap, self.frame_queue,
                                         self.stop_event)
        self.grabber.start()

        self.preview_canvas.itemconfig(self.canvas_placeholder, text="")
        self._poll_frames()   # start main-thread polling loop

        self._log(
            f"Connected! {self.selected_cam['name']} @ {self.res_var.get()}",
            "success"
        )
        self._set_status(f"Live — {self.selected_cam['name']}", ACCENT)
        self.photo_btn.config(state="normal")
        self.rec_btn.config(state="normal")
        self.connect_btn.config(state="disabled")
        self.disconnect_btn.config(state="normal")

    def _disconnect_camera(self, silent=False):
        # Cancel scheduled poll
        if self._poll_id:
            self.after_cancel(self._poll_id)
            self._poll_id = None

        # Stop grabber
        self.stop_event.set()
        if self.grabber:
            self.grabber.join(timeout=2)
            self.grabber = None

        if self.recording:
            self._stop_recording()

        if self.cap:
            self.cap.release()
            self.cap = None

        self.current_frame = None

        # Reset canvas
        self.preview_canvas.delete("all")
        self.canvas_placeholder = self.preview_canvas.create_text(
            PREVIEW_W // 2, PREVIEW_H // 2,
            text="No camera connected\n\nScan → Select → Connect",
            fill=TEXT_MUTED, font=("Courier New", 13), justify="center"
        )
        self.rec_overlay = self.preview_canvas.create_text(
            12, 12, anchor="nw", text="",
            fill=DANGER, font=("Courier New", 11, "bold")
        )

        self.photo_btn.config(state="disabled")
        self.rec_btn.config(state="disabled")
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        self.fps_stat.config(text="")
        self._set_status("Disconnected", TEXT_MUTED)
        if not silent:
            self._log("Camera disconnected.", "warn")

    # ── FRAME POLLING — runs entirely on main thread ──────────
    def _poll_frames(self):
        """
        Pulls raw numpy frames from the queue and converts them
        to PhotoImage HERE on the main thread. This is the fix
        for the segmentation fault — ImageTk.PhotoImage must
        never be created in a background thread on Linux/ARM.
        """
        try:
            frame = self.frame_queue.get_nowait()
        except queue.Empty:
            self._poll_id = self.after(30, self._poll_frames)
            return

        if frame is None:
            msg = "Camera read error: can't get frames from device."
            if self.selected_cam and self.selected_cam.get("type") == "CSI":
                msg += (
                    "\n\n⚠️ CSI Camera Support on Ubuntu 22.04\n\n"
                    "libcamera needs to be built from source.\n\n"
                    "SOLUTION:\n"
                    "1. bash ~/Robocam/build_libcamera.sh (~15 min)\n"
                    "2. source ~/.bashrc\n"
                    "3. robocam\n\n"
                    "Then restart the app to use CSI camera."
                )
            else:
                msg += "\nCheck: Is the camera connected? Try another device?"
            self._log(msg, "error")
            self._set_status("Camera error", DANGER)
            self._disconnect_camera(silent=True)
            return

        # Store raw frame (used by photo capture & recording)
        self.current_frame = frame

        # Write to video file if recording
        if self.recording and self.video_writer:
            self.video_writer.write(frame)

        # Convert BGR → RGB → PIL → PhotoImage  ← MAIN THREAD ONLY
        rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img   = Image.fromarray(rgb)
        img   = img.resize((PREVIEW_W, PREVIEW_H), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image=img)

        # Render on canvas
        self.preview_canvas.delete("frame")
        self.preview_canvas.create_image(
            0, 0, anchor="nw", image=photo, tags="frame"
        )
        self.preview_canvas.tag_raise(self.rec_overlay)
        # Keep a reference — Tkinter GC will delete it otherwise
        self.preview_canvas._photo = photo

        # FPS
        self._fps_frames += 1
        elapsed = time.time() - self._fps_time
        if elapsed >= 1.0:
            fps = self._fps_frames / elapsed
            self.fps_stat.config(text=f"FPS: {fps:.1f}", fg=TEXT_MUTED)
            self._fps_frames = 0
            self._fps_time   = time.time()

        # Recording overlay timer
        if self.recording and self.rec_start_time:
            secs = int(time.time() - self.rec_start_time)
            m, s = divmod(secs, 60)
            self.preview_canvas.itemconfig(
                self.rec_overlay, text=f"⏺ REC  {m:02d}:{s:02d}"
            )

        # Schedule next poll (~30 fps target)
        self._poll_id = self.after(30, self._poll_frames)

    # ── PHOTO ─────────────────────────────────────────────────
    def _take_photo(self):
        if self.current_frame is None:
            self._log("No frame available yet.", "warn")
            return
        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_DIR, f"photo_{ts}.jpg")
        cv2.imwrite(filename, self.current_frame)
        self.photo_count += 1
        self.photo_stat.config(text=f"Photos: {self.photo_count}")
        self._log(f"Photo saved → {filename}", "success")

    # ── RECORDING ─────────────────────────────────────────────
    def _toggle_record(self):
        if self.recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        if self.current_frame is None:
            self._log("No frame available to record.", "warn")
            return
        ts       = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_DIR, f"video_{ts}.avi")
        h, w     = self.current_frame.shape[:2]
        fourcc   = cv2.VideoWriter_fourcc(*"XVID")
        self.video_writer   = cv2.VideoWriter(filename, fourcc, 20.0, (w, h))
        self.recording      = True
        self.rec_start_time = time.time()
        self.rec_btn.config(text="⏹  Stop Recording", bg=WARNING)
        self.rec_stat.config(text="● REC")
        self._log(f"Recording started → {filename}", "warn")

    def _stop_recording(self):
        self.recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        dur = (int(time.time() - self.rec_start_time)
               if self.rec_start_time else 0)
        self.rec_start_time = None
        self.rec_btn.config(text="⏺  Start Recording", bg=DANGER)
        self.rec_stat.config(text="")
        self.preview_canvas.itemconfig(self.rec_overlay, text="")
        self._log(f"Recording stopped. Duration: {dur}s", "success")

    # ── UTILITIES ─────────────────────────────────────────────
    def _choose_folder(self):
        global SAVE_DIR
        folder = filedialog.askdirectory(initialdir=SAVE_DIR)
        if folder:
            SAVE_DIR = folder
            short = folder.replace(os.path.expanduser("~"), "~")
            self.folder_lbl.config(text=short)
            self._log(f"Save folder → {folder}", "info")

    def _open_output_folder(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        try:
            subprocess.Popen(["xdg-open", SAVE_DIR])
        except Exception:
            self._log(f"Output folder: {SAVE_DIR}", "info")

    def _on_close(self):
        if self._poll_id:
            self.after_cancel(self._poll_id)
        self.stop_event.set()
        if self.grabber:
            self.grabber.join(timeout=2)
        if self.recording:
            self._stop_recording()
        if self.cap:
            self.cap.release()
        self.destroy()


# ─────────────────────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = RoboCamApp()
    app.mainloop()
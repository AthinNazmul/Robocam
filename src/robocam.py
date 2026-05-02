#!/usr/bin/env python3
"""
RoboNeT Camera Tool
====================
A lightweight Tkinter GUI tool for detecting and using camera modules on
Raspberry Pi running Ubuntu 24.04. Supports:
  - CSI cameras (Pi Camera 1.3, IMX219) via libcamera / v4l2
  - USB cameras via OpenCV / v4l2
  - Auto-detection of all available camera devices
  - Live preview, photo capture, video recording

Requirements:
  pip install opencv-python pillow
  sudo apt install v4l-utils libcamera-apps -y

Author: RoboNeT - United International University (CENTER)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import subprocess
import os
import time
import datetime
import re
import sys

# Try importing optional dependencies with helpful error messages
try:
    import cv2
except ImportError:
    print("ERROR: OpenCV not found. Run: pip install opencv-python")
    sys.exit(1)

try:
    from PIL import Image, ImageTk
except ImportError:
    print("ERROR: Pillow not found. Run: pip install pillow")
    sys.exit(1)


# ─────────────────────────────────────────────
#  THEME & CONSTANTS
# ─────────────────────────────────────────────
BG_DARK       = "#0f1117"
BG_PANEL      = "#1a1d27"
BG_CARD       = "#22263a"
ACCENT        = "#00d4aa"        # teal-green
ACCENT2       = "#7c6af7"        # purple
DANGER        = "#ff4f5e"
WARNING       = "#ffb547"
TEXT_PRIMARY  = "#e8eaf0"
TEXT_MUTED    = "#6b7280"
BORDER        = "#2e3347"
FONT_MONO     = ("Courier New", 10)
FONT_UI       = ("TkDefaultFont", 10)

PREVIEW_W     = 640
PREVIEW_H     = 480
SAVE_DIR      = os.path.expanduser("~/robocam_output")


# ─────────────────────────────────────────────
#  CAMERA DETECTION
# ─────────────────────────────────────────────
def detect_cameras():
    """
    Detect all available cameras:
      1. v4l2 devices (/dev/video*)
      2. libcamera-detected CSI cameras
    Returns a list of dicts: {index, name, type, device}
    """
    cameras = []
    seen_indices = set()

    # --- v4l2 / USB + CSI via V4L2 ---
    try:
        result = subprocess.run(
            ["v4l2-ctl", "--list-devices"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout
        current_name = "Unknown Camera"
        for line in output.splitlines():
            line = line.strip()
            if line and not line.startswith("/dev/"):
                current_name = line.rstrip(":")
            elif line.startswith("/dev/video"):
                match = re.search(r"/dev/video(\d+)", line)
                if match:
                    idx = int(match.group(1))
                    if idx not in seen_indices:
                        seen_indices.add(idx)
                        cam_type = "CSI" if any(k in current_name.lower()
                                                for k in ["mmal", "bcm", "unicam",
                                                          "imx", "ov", "csi", "rpicam"]) \
                                        else "USB"
                        cameras.append({
                            "index":  idx,
                            "name":   current_name,
                            "type":   cam_type,
                            "device": f"/dev/video{idx}"
                        })
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    # --- fallback: probe /dev/video0..9 directly ---
    if not cameras:
        for i in range(10):
            if i in seen_indices:
                continue
            dev = f"/dev/video{i}"
            if os.path.exists(dev):
                cap = cv2.VideoCapture(i)
                if cap.isOpened():
                    ret, _ = cap.read()
                    cap.release()
                    if ret:
                        cameras.append({
                            "index":  i,
                            "name":   f"Camera {i}",
                            "type":   "Unknown",
                            "device": dev
                        })
                        seen_indices.add(i)

    # --- libcamera CSI check ---
    try:
        result = subprocess.run(
            ["libcamera-hello", "--list-cameras"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout + result.stderr
        if "Available cameras" in output or "imx" in output.lower() or "ov" in output.lower():
            # Mark existing CSI cameras or add a libcamera entry
            found_csi = False
            for cam in cameras:
                if cam["type"] == "CSI":
                    cam["name"] += " (libcamera)"
                    found_csi = True
            if not found_csi:
                cameras.append({
                    "index":  99,
                    "name":   "CSI Camera (libcamera only)",
                    "type":   "CSI",
                    "device": "libcamera"
                })
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass

    return cameras


def open_camera(cam_info):
    """Open a camera and return a cv2.VideoCapture object."""
    if cam_info["device"] == "libcamera":
        # Try libcamera via GStreamer pipeline
        pipeline = (
            "libcamerasrc ! video/x-raw,width=640,height=480,framerate=30/1 "
            "! videoconvert ! appsink"
        )
        cap = cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)
        if cap.isOpened():
            return cap
        # fallback to index 0
        return cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(cam_info["index"])
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, PREVIEW_W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, PREVIEW_H)
        return cap


# ─────────────────────────────────────────────
#  MAIN APPLICATION
# ─────────────────────────────────────────────
class RoboCamApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("RoboNeT Camera Tool")
        self.configure(bg=BG_DARK)
        self.resizable(False, False)

        # State
        self.cameras          = []
        self.selected_cam     = None
        self.cap              = None
        self.preview_running  = False
        self.preview_thread   = None
        self.recording        = False
        self.video_writer     = None
        self.rec_start_time   = None
        self.photo_count      = 0
        self.current_frame    = None
        self._after_id        = None

        os.makedirs(SAVE_DIR, exist_ok=True)

        self._build_ui()
        self._apply_styles()
        self.after(100, self._auto_detect)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── UI CONSTRUCTION ──────────────────────
    def _build_ui(self):
        # ── Top bar ──
        topbar = tk.Frame(self, bg=BG_DARK, pady=6)
        topbar.pack(fill="x", padx=16)

        tk.Label(topbar, text="🤖  RoboNeT Camera Tool",
                 bg=BG_DARK, fg=ACCENT,
                 font=("Courier New", 15, "bold")).pack(side="left")

        tk.Label(topbar, text="Ubuntu · Raspberry Pi",
                 bg=BG_DARK, fg=TEXT_MUTED,
                 font=FONT_MONO).pack(side="left", padx=12)

        self.status_dot = tk.Label(topbar, text="●", bg=BG_DARK,
                                   fg=TEXT_MUTED, font=("TkDefaultFont", 14))
        self.status_dot.pack(side="right")
        self.status_lbl = tk.Label(topbar, text="No camera active",
                                   bg=BG_DARK, fg=TEXT_MUTED, font=FONT_MONO)
        self.status_lbl.pack(side="right", padx=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=8)

        # ── Main area ──
        main = tk.Frame(self, bg=BG_DARK)
        main.pack(fill="both", expand=True, padx=12, pady=8)

        # Left panel
        left = tk.Frame(main, bg=BG_PANEL, width=230,
                        relief="flat", bd=0)
        left.pack(side="left", fill="y", padx=(0, 10), pady=0)
        left.pack_propagate(False)
        self._build_left_panel(left)

        # Right area: preview + controls
        right = tk.Frame(main, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)
        self._build_preview(right)
        self._build_controls(right)

        # ── Bottom log ──
        self._build_log()

    def _build_left_panel(self, parent):
        # Section: Camera Detection
        self._section_label(parent, "CAMERA DETECTION")

        self.detect_btn = self._btn(parent, "🔍  Scan for Cameras",
                                    self._auto_detect, ACCENT)
        self.detect_btn.pack(fill="x", padx=10, pady=(4, 8))

        # Camera list
        list_frame = tk.Frame(parent, bg=BG_CARD, relief="flat")
        list_frame.pack(fill="x", padx=10, pady=4)

        tk.Label(list_frame, text="Available Cameras",
                 bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Courier New", 8)).pack(anchor="w", padx=8, pady=(6, 2))

        self.cam_listbox = tk.Listbox(
            list_frame, bg=BG_CARD, fg=TEXT_PRIMARY,
            selectbackground=ACCENT2, selectforeground="white",
            font=FONT_MONO, height=6, bd=0, highlightthickness=0,
            relief="flat", activestyle="none"
        )
        self.cam_listbox.pack(fill="x", padx=4, pady=(0, 6))
        self.cam_listbox.bind("<<ListboxSelect>>", self._on_cam_select)

        # Camera info card
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

        # Connect button
        self.connect_btn = self._btn(parent, "▶  Connect Camera",
                                     self._connect_camera, ACCENT2)
        self.connect_btn.pack(fill="x", padx=10, pady=6)
        self.connect_btn.config(state="disabled")

        self.disconnect_btn = self._btn(parent, "■  Disconnect",
                                        self._disconnect_camera, DANGER)
        self.disconnect_btn.pack(fill="x", padx=10, pady=(0, 6))
        self.disconnect_btn.config(state="disabled")

        # Section: Settings
        self._section_label(parent, "SETTINGS")
        settings_card = tk.Frame(parent, bg=BG_CARD)
        settings_card.pack(fill="x", padx=10, pady=4)

        # Resolution
        tk.Label(settings_card, text="Resolution",
                 bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Courier New", 8)).pack(anchor="w", padx=8, pady=(6, 0))
        self.res_var = tk.StringVar(value="640x480")
        res_combo = ttk.Combobox(settings_card, textvariable=self.res_var,
                                  values=["320x240", "640x480",
                                          "1280x720", "1920x1080"],
                                  state="readonly", width=18)
        res_combo.pack(padx=8, pady=4, anchor="w")

        # Save folder
        tk.Label(settings_card, text="Save Folder",
                 bg=BG_CARD, fg=TEXT_MUTED,
                 font=("Courier New", 8)).pack(anchor="w", padx=8)
        folder_row = tk.Frame(settings_card, bg=BG_CARD)
        folder_row.pack(fill="x", padx=8, pady=(2, 8))
        self.folder_lbl = tk.Label(folder_row, text="~/robocam_output",
                                    bg=BG_CARD, fg=ACCENT,
                                    font=("Courier New", 7), anchor="w")
        self.folder_lbl.pack(side="left", fill="x", expand=True)
        self._small_btn(folder_row, "📁", self._choose_folder).pack(side="right")

    def _build_preview(self, parent):
        preview_border = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        preview_border.pack(pady=(0, 8))

        self.preview_canvas = tk.Canvas(
            preview_border, width=PREVIEW_W, height=PREVIEW_H,
            bg=BG_CARD, highlightthickness=0
        )
        self.preview_canvas.pack()

        # Placeholder text on canvas
        self.canvas_placeholder = self.preview_canvas.create_text(
            PREVIEW_W // 2, PREVIEW_H // 2,
            text="No camera connected\n\nScan → Select → Connect",
            fill=TEXT_MUTED, font=("Courier New", 13),
            justify="center"
        )

        # Recording overlay text
        self.rec_text = self.preview_canvas.create_text(
            12, 12, anchor="nw",
            text="", fill=DANGER,
            font=("Courier New", 11, "bold")
        )

    def _build_controls(self, parent):
        ctrl = tk.Frame(parent, bg=BG_DARK)
        ctrl.pack(fill="x")

        # Photo button
        self.photo_btn = self._btn(ctrl, "📷  Take Photo",
                                   self._take_photo, ACCENT, width=18)
        self.photo_btn.pack(side="left", padx=(0, 6))
        self.photo_btn.config(state="disabled")

        # Record button
        self.rec_btn = self._btn(ctrl, "⏺  Start Recording",
                                 self._toggle_record, DANGER, width=18)
        self.rec_btn.pack(side="left", padx=6)
        self.rec_btn.config(state="disabled")

        # Open folder
        self._btn(ctrl, "📂  Open Output",
                  self._open_output_folder, WARNING, width=14).pack(side="right")

        # Stats row
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
        log_frame = tk.Frame(self, bg=BG_PANEL)
        log_frame.pack(fill="x", padx=12, pady=(4, 8))

        header = tk.Frame(log_frame, bg=BG_PANEL)
        header.pack(fill="x", padx=8, pady=(4, 0))
        tk.Label(header, text="SYSTEM LOG", bg=BG_PANEL,
                 fg=TEXT_MUTED, font=("Courier New", 8)).pack(side="left")
        self._small_btn(header, "Clear", self._clear_log).pack(side="right")

        self.log_text = tk.Text(
            log_frame, height=5, bg=BG_DARK, fg=ACCENT,
            font=("Courier New", 9), relief="flat",
            bd=0, state="disabled", wrap="word",
            highlightthickness=0
        )
        self.log_text.pack(fill="x", padx=8, pady=(2, 8))

        # Tag colours
        self.log_text.tag_config("info",    foreground=ACCENT)
        self.log_text.tag_config("warn",    foreground=WARNING)
        self.log_text.tag_config("error",   foreground=DANGER)
        self.log_text.tag_config("success", foreground="#4ade80")

    # ── HELPERS ──────────────────────────────
    def _section_label(self, parent, text):
        tk.Label(parent, text=text, bg=BG_PANEL, fg=TEXT_MUTED,
                 font=("Courier New", 7)).pack(
            anchor="w", padx=10, pady=(10, 2))

    def _btn(self, parent, text, cmd, color, width=None):
        kw = dict(
            text=text, command=cmd,
            bg=color, fg=BG_DARK,
            font=("Courier New", 9, "bold"),
            relief="flat", cursor="hand2",
            activebackground=color, activeforeground=BG_DARK,
            padx=10, pady=6, bd=0
        )
        if width:
            kw["width"] = width
        return tk.Button(parent, **kw)

    def _small_btn(self, parent, text, cmd):
        return tk.Button(
            parent, text=text, command=cmd,
            bg=BG_CARD, fg=TEXT_MUTED,
            font=("Courier New", 8), relief="flat",
            cursor="hand2", padx=4, pady=2,
            activebackground=BORDER, activeforeground=TEXT_PRIMARY
        )

    def _apply_styles(self):
        style = ttk.Style(self)
        style.theme_use("default")
        style.configure("TCombobox",
                        fieldbackground=BG_CARD,
                        background=BG_CARD,
                        foreground=TEXT_PRIMARY,
                        selectbackground=ACCENT2,
                        borderwidth=0)
        style.configure("TSeparator", background=BORDER)

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

    # ── CAMERA DETECTION ─────────────────────
    def _auto_detect(self):
        self._log("Scanning for cameras...", "info")
        self.detect_btn.config(state="disabled", text="🔄  Scanning...")
        self.after(50, self._run_detection)

    def _run_detection(self):
        self.cameras = detect_cameras()
        self.cam_listbox.delete(0, "end")

        if not self.cameras:
            self._log("No cameras found. Check connections.", "warn")
            self._set_status("No cameras found", WARNING)
        else:
            for cam in self.cameras:
                icon = "📷" if cam["type"] == "CSI" else "🔌"
                label = f"{icon} [{cam['type']}] {cam['name'][:24]}"
                self.cam_listbox.insert("end", label)
            self._log(f"Found {len(self.cameras)} camera(s).", "success")
            self._set_status(f"{len(self.cameras)} camera(s) detected", ACCENT)

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

    # ── CONNECT / DISCONNECT ─────────────────
    def _connect_camera(self):
        if not self.selected_cam:
            return
        self._disconnect_camera(silent=True)

        self._log(f"Connecting to {self.selected_cam['name']}...", "info")
        self.cap = open_camera(self.selected_cam)

        if not self.cap or not self.cap.isOpened():
            self._log("Failed to open camera. Try another device.", "error")
            self._set_status("Connection failed", DANGER)
            return

        # Apply resolution
        w, h = map(int, self.res_var.get().split("x"))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)

        self.preview_running = True
        self.preview_canvas.itemconfig(self.canvas_placeholder, text="")
        self.preview_thread = threading.Thread(
            target=self._preview_loop, daemon=True)
        self.preview_thread.start()

        self._log(f"Connected! {self.selected_cam['name']} @ {self.res_var.get()}", "success")
        self._set_status(f"Live — {self.selected_cam['name']}", ACCENT)
        self.photo_btn.config(state="normal")
        self.rec_btn.config(state="normal")
        self.connect_btn.config(state="disabled")
        self.disconnect_btn.config(state="normal")

    def _disconnect_camera(self, silent=False):
        self.preview_running = False
        if self.recording:
            self._stop_recording()
        if self.cap:
            self.cap.release()
            self.cap = None
        self.current_frame = None
        self.preview_canvas.delete("all")
        self.canvas_placeholder = self.preview_canvas.create_text(
            PREVIEW_W // 2, PREVIEW_H // 2,
            text="No camera connected\n\nScan → Select → Connect",
            fill=TEXT_MUTED, font=("Courier New", 13), justify="center"
        )
        self.rec_text = self.preview_canvas.create_text(
            12, 12, anchor="nw", text="", fill=DANGER,
            font=("Courier New", 11, "bold")
        )
        self.photo_btn.config(state="disabled")
        self.rec_btn.config(state="disabled")
        self.connect_btn.config(state="normal")
        self.disconnect_btn.config(state="disabled")
        self.fps_stat.config(text="")
        self._set_status("Disconnected", TEXT_MUTED)
        if not silent:
            self._log("Camera disconnected.", "warn")

    # ── PREVIEW LOOP ─────────────────────────
    def _preview_loop(self):
        fps_counter = 0
        fps_timer = time.time()

        while self.preview_running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                self.after(0, lambda: self._log(
                    "Frame read failed. Camera may be disconnected.", "error"))
                break

            self.current_frame = frame.copy()

            if self.recording and self.video_writer:
                self.video_writer.write(frame)

            # Convert for Tkinter
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)
            img = img.resize((PREVIEW_W, PREVIEW_H), Image.LANCZOS)
            photo = ImageTk.PhotoImage(image=img)

            # Schedule GUI update on main thread
            self.after(0, self._update_canvas, photo)

            # FPS
            fps_counter += 1
            elapsed = time.time() - fps_timer
            if elapsed >= 1.0:
                fps = fps_counter / elapsed
                self.after(0, self.fps_stat.config,
                           {"text": f"FPS: {fps:.1f}", "fg": TEXT_MUTED})
                fps_counter = 0
                fps_timer = time.time()

            # Rec overlay
            if self.recording and self.rec_start_time:
                secs = int(time.time() - self.rec_start_time)
                m, s = divmod(secs, 60)
                self.after(0, self.preview_canvas.itemconfig,
                           self.rec_text,
                           {"text": f"⏺ REC  {m:02d}:{s:02d}"})

            time.sleep(0.03)

        self.after(0, self.preview_canvas.itemconfig,
                   self.rec_text, {"text": ""})

    def _update_canvas(self, photo):
        self.preview_canvas.delete("frame")
        self.preview_canvas.create_image(
            0, 0, anchor="nw", image=photo, tags="frame")
        self.preview_canvas.tag_raise(self.rec_text)
        self.preview_canvas._photo = photo  # prevent GC

    # ── PHOTO CAPTURE ────────────────────────
    def _take_photo(self):
        if self.current_frame is None:
            self._log("No frame available.", "warn")
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_DIR, f"photo_{ts}.jpg")
        cv2.imwrite(filename, self.current_frame)
        self.photo_count += 1
        self.photo_stat.config(text=f"Photos: {self.photo_count}")
        self._log(f"Photo saved → {filename}", "success")

    # ── VIDEO RECORDING ──────────────────────
    def _toggle_record(self):
        if self.recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self):
        if self.current_frame is None:
            self._log("No frame available to record.", "warn")
            return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(SAVE_DIR, f"video_{ts}.avi")
        h, w = self.current_frame.shape[:2]
        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (w, h))
        self.recording = True
        self.rec_start_time = time.time()
        self.rec_btn.config(text="⏹  Stop Recording", bg=WARNING)
        self.rec_stat.config(text="● REC")
        self._log(f"Recording started → {filename}", "warn")

    def _stop_recording(self):
        self.recording = False
        if self.video_writer:
            self.video_writer.release()
            self.video_writer = None
        dur = int(time.time() - self.rec_start_time) if self.rec_start_time else 0
        self.rec_start_time = None
        self.rec_btn.config(text="⏺  Start Recording", bg=DANGER)
        self.rec_stat.config(text="")
        self.preview_canvas.itemconfig(self.rec_text, text="")
        self._log(f"Recording stopped. Duration: {dur}s", "success")

    # ── UTILITIES ────────────────────────────
    def _choose_folder(self):
        global SAVE_DIR
        folder = filedialog.askdirectory(initialdir=SAVE_DIR)
        if folder:
            SAVE_DIR = folder
            short = folder.replace(os.path.expanduser("~"), "~")
            self.folder_lbl.config(text=short)
            self._log(f"Save folder changed → {folder}", "info")

    def _open_output_folder(self):
        os.makedirs(SAVE_DIR, exist_ok=True)
        try:
            subprocess.Popen(["xdg-open", SAVE_DIR])
        except Exception:
            self._log(f"Output folder: {SAVE_DIR}", "info")

    def _on_close(self):
        self.preview_running = False
        if self.recording:
            self._stop_recording()
        if self.cap:
            self.cap.release()
        self.destroy()


# ─────────────────────────────────────────────
#  ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = RoboCamApp()
    app.mainloop()
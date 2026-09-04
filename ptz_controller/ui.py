"""Tkinter MVP user interface with manual controls and guarded joystick mode."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from .joystick import JoystickReader
from .visca import ViscaClient


class PTZControllerApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("PTZ Controller — MVP")
        self.root.geometry("860x620")
        self.root.minsize(760, 560)
        self.client: ViscaClient | None = None
        self.reader = JoystickReader()
        self.joystick_enabled = tk.BooleanVar(value=False)
        self.live_enabled = tk.BooleanVar(value=False)
        self.dead_zone = tk.DoubleVar(value=0.08)
        self.speed = tk.IntVar(value=6)
        self.status = tk.StringVar(value="Demo mode — commands are not sent")
        self.joystick_status = tk.StringVar(value="Not scanned")
        self.axes = {name: tk.StringVar(value="+0.00") for name in ("X", "Y", "Twist", "Throttle")}
        self._last_motion = (0, 0, 0)
        self._build()
        self.root.protocol("WM_DELETE_WINDOW", self.shutdown)

    def _build(self) -> None:
        style = ttk.Style(self.root)
        style.configure("Title.TLabel", font=("Arial", 20, "bold"))
        style.configure("Header.TLabel", font=("Arial", 11, "bold"))
        shell = ttk.Frame(self.root, padding=18)
        shell.pack(fill="both", expand=True)
        ttk.Label(shell, text="PTZ Controller", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(shell, textvariable=self.status).grid(row=0, column=1, columnspan=3, sticky="e")

        connection = ttk.LabelFrame(shell, text="Camera connection", padding=12)
        connection.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(16, 10))
        self.host = tk.StringVar(value="192.168.1.120")
        self.port = tk.StringVar(value="52381")
        for column, (label, variable, width) in enumerate((("Camera IP", self.host, 20), ("UDP port", self.port, 8))):
            ttk.Label(connection, text=label).grid(row=0, column=column * 2, sticky="w")
            ttk.Entry(connection, textvariable=variable, width=width).grid(row=0, column=column * 2 + 1, padx=(5, 16))
        ttk.Checkbutton(connection, text="Send live camera commands", variable=self.live_enabled, command=self.set_live_mode).grid(row=0, column=4, padx=8)
        ttk.Button(connection, text="Connect", command=self.connect).grid(row=0, column=5)

        manual = ttk.LabelFrame(shell, text="Manual camera test", padding=14)
        manual.grid(row=2, column=0, sticky="nsew", padx=(0, 10))
        ttk.Label(manual, text="Test these first at a low speed.").grid(row=0, column=0, columnspan=3, pady=(0, 8))
        ttk.Button(manual, text="▲", command=lambda: self.move(0, 1)).grid(row=1, column=1, ipadx=12, ipady=7)
        ttk.Button(manual, text="◀", command=lambda: self.move(-1, 0)).grid(row=2, column=0, ipadx=12, ipady=7)
        ttk.Button(manual, text="STOP", command=self.stop).grid(row=2, column=1, ipadx=9, ipady=7)
        ttk.Button(manual, text="▶", command=lambda: self.move(1, 0)).grid(row=2, column=2, ipadx=12, ipady=7)
        ttk.Button(manual, text="▼", command=lambda: self.move(0, -1)).grid(row=3, column=1, ipadx=12, ipady=7)
        ttk.Separator(manual).grid(row=4, column=0, columnspan=3, sticky="ew", pady=14)
        ttk.Button(manual, text="Zoom −", command=lambda: self.zoom(-1)).grid(row=5, column=0)
        ttk.Button(manual, text="Zoom stop", command=lambda: self.zoom(0)).grid(row=5, column=1)
        ttk.Button(manual, text="Zoom +", command=lambda: self.zoom(1)).grid(row=5, column=2)
        ttk.Label(manual, text="Movement speed").grid(row=6, column=0, columnspan=3, pady=(18, 0))
        ttk.Scale(manual, from_=1, to=24, variable=self.speed, orient="horizontal").grid(row=7, column=0, columnspan=3, sticky="ew")

        joystick = ttk.LabelFrame(shell, text="Joystick", padding=14)
        joystick.grid(row=2, column=1, columnspan=3, sticky="nsew")
        ttk.Button(joystick, text="Scan USB joystick", command=self.scan_joystick).grid(row=0, column=0, sticky="w")
        ttk.Label(joystick, textvariable=self.joystick_status).grid(row=0, column=1, columnspan=3, sticky="w", padx=12)
        for row, name in enumerate(self.axes, start=1):
            ttk.Label(joystick, text=name).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Label(joystick, textvariable=self.axes[name], style="Header.TLabel").grid(row=row, column=1, sticky="w")
        ttk.Label(joystick, text="Dead zone").grid(row=5, column=0, sticky="w", pady=(12, 0))
        ttk.Scale(joystick, from_=0.02, to=0.25, variable=self.dead_zone, orient="horizontal").grid(row=5, column=1, columnspan=2, sticky="ew", pady=(12, 0))
        ttk.Checkbutton(joystick, text="Enable joystick camera control", variable=self.joystick_enabled, command=self.toggle_joystick).grid(row=6, column=0, columnspan=4, sticky="w", pady=(14, 0))
        ttk.Label(joystick, text="Joystick control remains disabled until manually enabled.").grid(row=7, column=0, columnspan=4, sticky="w", pady=(5, 0))

        presets = ttk.LabelFrame(shell, text="Presets", padding=12)
        presets.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        for preset, name in enumerate(("Pulpit", "Piano", "Worship team", "Wide stage", "Audience"), start=1):
            ttk.Button(presets, text=f"{preset}  {name}", command=lambda value=preset: self.recall(value)).grid(row=0, column=preset - 1, padx=4)

        shell.columnconfigure(0, weight=1)
        shell.columnconfigure(1, weight=1)
        shell.rowconfigure(2, weight=1)

    def connect(self) -> None:
        try:
            if self.client:
                self.client.close()
            self.client = ViscaClient(self.host.get().strip(), int(self.port.get()), enabled=self.live_enabled.get())
            self.status.set(f"Connected to {self.host.get()}:{self.port.get()} ({'LIVE' if self.live_enabled.get() else 'demo'})")
        except ValueError:
            messagebox.showerror("Invalid port", "Enter a valid UDP port number.")

    def set_live_mode(self) -> None:
        if self.live_enabled.get() and not messagebox.askyesno("Enable live commands", "This will send camera-movement commands to the configured IP address. Continue?"):
            self.live_enabled.set(False)
        if self.client:
            self.client.enabled = self.live_enabled.get()
        self.status.set("Live commands enabled" if self.live_enabled.get() else "Demo mode — commands are not sent")

    def _client(self) -> ViscaClient:
        if self.client is None:
            self.connect()
        assert self.client is not None
        return self.client

    def move(self, pan: int, tilt: int) -> None:
        self._client().pan_tilt(pan, tilt, self.speed.get(), min(20, self.speed.get()))
        self.status.set(f"{'LIVE' if self.live_enabled.get() else 'Demo'}: pan {pan}, tilt {tilt}")

    def stop(self) -> None:
        self._client().stop()
        self._last_motion = (0, 0, 0)
        self.status.set("STOP sent" if self.live_enabled.get() else "Demo: STOP")

    def zoom(self, direction: int) -> None:
        self._client().zoom(direction)
        self.status.set("Zoom command sent" if self.live_enabled.get() else "Demo: zoom")

    def recall(self, preset: int) -> None:
        self._client().recall_preset(preset)
        self.status.set(f"{'LIVE' if self.live_enabled.get() else 'Demo'}: preset {preset}")

    def scan_joystick(self) -> None:
        if not self.reader.available:
            self.joystick_status.set("pygame missing — run: python -m pip install -r requirements.txt")
            return
        self.joystick_status.set(self.reader.name if self.reader.connect_first() else "No joystick detected")
        if self.reader.device:
            self.poll_joystick()

    def toggle_joystick(self) -> None:
        if self.joystick_enabled.get() and self.reader.device is None:
            self.joystick_enabled.set(False)
            messagebox.showwarning("No joystick", "Scan and connect a joystick before enabling control.")
        if not self.joystick_enabled.get():
            self.stop()

    def poll_joystick(self) -> None:
        if self.reader.device is None:
            return
        state = self.reader.read()
        self.axes["X"].set(f"{state.x:+.2f}")
        self.axes["Y"].set(f"{state.y:+.2f}")
        self.axes["Twist"].set(f"{state.twist:+.2f}")
        self.axes["Throttle"].set(f"{state.throttle:.0%}")
        if self.joystick_enabled.get():
            zone = self.dead_zone.get()
            pan = 1 if state.x > zone else -1 if state.x < -zone else 0
            tilt = 1 if state.y > zone else -1 if state.y < -zone else 0
            zoom = 1 if state.twist > zone else -1 if state.twist < -zone else 0
            speed = max(1, round(1 + state.throttle * 23))
            intent = (pan, tilt, zoom)
            if intent != self._last_motion:
                self._client().pan_tilt(pan, tilt, speed, min(20, speed))
                self._client().zoom(zoom, min(7, max(0, round(abs(state.twist) * 7))))
                self._last_motion = intent
        self.root.after(50, self.poll_joystick)

    def shutdown(self) -> None:
        try:
            if self.client:
                self.client.stop()
                self.client.close()
        finally:
            self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

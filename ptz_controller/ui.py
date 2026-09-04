"""Tkinter MVP user interface with manual controls and guarded joystick mode."""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from .joystick import JoystickReader
from .presets import PresetStore
from .visca import ViscaClient


class PTZControllerApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("PTZ Controller — MVP")
        self.root.geometry("860x620")
        self.root.minsize(760, 560)
        self.client: ViscaClient | None = None
        self.reader = JoystickReader()
        self.preset_store = PresetStore()
        self.presets = self.preset_store.load()
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

        self.presets_frame = ttk.LabelFrame(shell, text="Presets", padding=12)
        self.presets_frame.grid(row=3, column=0, columnspan=4, sticky="ew", pady=(10, 0))
        self.render_presets()

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

    def render_presets(self) -> None:
        for child in self.presets_frame.winfo_children():
            child.destroy()
        for index, preset in enumerate(self.presets):
            row, column = divmod(index, 3)
            ttk.Button(
                self.presets_frame,
                text=f"{preset['number']}  {preset['name']}",
                command=lambda value=int(preset["number"]): self.recall(value),
            ).grid(row=row, column=column, padx=4, pady=3, sticky="ew")
            self.presets_frame.columnconfigure(column, weight=1)
        controls_row = (len(self.presets) + 2) // 3
        ttk.Button(self.presets_frame, text="Manage presets…", command=self.open_preset_manager).grid(row=controls_row, column=0, padx=4, pady=(12, 0), sticky="ew")
        ttk.Button(self.presets_frame, text="Store current position…", command=self.store_preset).grid(row=controls_row, column=1, columnspan=2, padx=4, pady=(12, 0), sticky="ew")

    def open_preset_manager(self) -> None:
        window = tk.Toplevel(self.root)
        window.title("Manage presets")
        window.resizable(False, False)
        frame = ttk.Frame(window, padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Preset names are saved on this computer.").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        listing = tk.Listbox(frame, width=38, height=9)
        listing.grid(row=1, column=0, columnspan=3, sticky="ew")
        number = tk.StringVar()
        name = tk.StringVar()

        def refresh(select_number: int | None = None) -> None:
            listing.delete(0, tk.END)
            for item in self.presets:
                listing.insert(tk.END, f"{item['number']:>2}  {item['name']}")
            if select_number is not None:
                for index, item in enumerate(self.presets):
                    if item["number"] == select_number:
                        listing.selection_set(index)
                        listing.activate(index)
                        break

        def select(_event=None) -> None:
            if not listing.curselection():
                return
            item = self.presets[listing.curselection()[0]]
            number.set(str(item["number"]))
            name.set(str(item["name"]))

        def save() -> None:
            try:
                value = int(number.get())
            except ValueError:
                messagebox.showerror("Invalid preset", "Preset number must be between 0 and 15.", parent=window)
                return
            label = name.get().strip()
            selected = listing.curselection()
            if not 0 <= value <= 15 or not label:
                messagebox.showerror("Invalid preset", "Enter a preset number from 0 to 15 and a name.", parent=window)
                return
            old_number = self.presets[selected[0]]["number"] if selected else None
            if any(item["number"] == value and item["number"] != old_number for item in self.presets):
                messagebox.showerror("Preset already used", f"Preset {value} already has a name. Select it to rename it, or choose another number.", parent=window)
                return
            if selected:
                self.presets[selected[0]] = {"number": value, "name": label}
            else:
                self.presets.append({"number": value, "name": label})
            self.presets.sort(key=lambda item: int(item["number"]))
            self.preset_store.save(self.presets)
            self.render_presets()
            refresh(value)

        def remove() -> None:
            if not listing.curselection():
                return
            item = self.presets[listing.curselection()[0]]
            if messagebox.askyesno("Remove preset label", f"Remove the local label for preset {item['number']} ({item['name']})? This does not erase the camera position.", parent=window):
                self.presets.pop(listing.curselection()[0])
                self.preset_store.save(self.presets)
                self.render_presets()
                refresh()
                number.set("")
                name.set("")

        listing.bind("<<ListboxSelect>>", select)
        ttk.Label(frame, text="Preset number").grid(row=2, column=0, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=number, width=8).grid(row=3, column=0, sticky="w")
        ttk.Label(frame, text="Display name").grid(row=2, column=1, sticky="w", pady=(12, 0))
        ttk.Entry(frame, textvariable=name, width=24).grid(row=3, column=1, sticky="ew", padx=(6, 0))
        ttk.Button(frame, text="Add / save", command=save).grid(row=3, column=2, padx=(8, 0))
        ttk.Button(frame, text="Remove selected", command=remove).grid(row=4, column=0, columnspan=3, pady=(12, 0), sticky="ew")
        refresh()

    def store_preset(self) -> None:
        preset = simpledialog.askinteger("Store preset", "Preset number to overwrite (0–15):", parent=self.root, minvalue=0, maxvalue=15)
        if preset is None:
            return
        if not messagebox.askyesno("Confirm preset store", f"Overwrite camera preset {preset} with the current camera position?", parent=self.root):
            return
        self._client().store_preset(preset)
        self.status.set(f"{'LIVE' if self.live_enabled.get() else 'Demo'}: stored preset {preset}")

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

import tkinter as tk
from tkinter import ttk


class MissionUI:
    """Display the grid, battery, current clue, and scrolling decision log."""

    def __init__(self, grid_size, delay_ms=150):
        self.grid_size = grid_size
        self.delay_ms = delay_ms
        self.latest_clue = "No scan yet"
        self.closed = False

        self.root = tk.Tk()
        self.root.title("WALL-E and EVE's Signal")
        self.root.geometry("920x720")
        self.root.minsize(780, 620)
        self.root.configure(bg="#101820")
        self.root.protocol("WM_DELETE_WINDOW", self._close)

        self.bg = "#101820"
        self.panel = "#1b2836"
        self.text = "#e8f0f7"
        self.muted = "#91a4b7"
        self.green = "#45d483"
        self.yellow = "#f3c969"
        self.blue = "#57b8ff"

        title = tk.Label(
            self.root,
            text="WALL-E AND EVE'S SIGNAL",
            font=("Segoe UI", 19, "bold"),
            bg=self.bg,
            fg=self.text,
        )
        title.pack(pady=(14, 3))

        subtitle = tk.Label(
            self.root,
            text="AUTONOMOUS SEARCH  •  BELIEF UPDATES  •  ENERGY MANAGEMENT",
            font=("Segoe UI", 9),
            bg=self.bg,
            fg=self.muted,
        )
        subtitle.pack(pady=(0, 12))

        self.status = tk.Label(
            self.root,
            text="MISSION INITIALIZING",
            font=("Segoe UI", 13, "bold"),
            bg=self.panel,
            fg=self.yellow,
            padx=12,
            pady=10,
        )
        self.status.pack(fill="x", padx=18, pady=(0, 12))

        body = tk.Frame(self.root, bg=self.bg)
        body.pack(fill="both", expand=True, padx=18, pady=(0, 14))

        left = tk.Frame(body, bg=self.bg)
        left.pack(side="left", fill="both", expand=True)

        right = tk.Frame(body, bg=self.panel, width=340)
        right.pack(side="right", fill="both", padx=(16, 0))
        right.pack_propagate(False)

        self.canvas = tk.Canvas(
            left,
            width=360,
            height=360,
            bg=self.bg,
            highlightthickness=0,
        )
        self.canvas.pack(pady=8)

        self.position_label = tk.Label(
            left, text="Position: --", bg=self.bg, fg=self.text,
            font=("Segoe UI", 11),
        )
        self.position_label.pack(anchor="w", pady=(8, 3))

        self.step_label = tk.Label(
            left, text="Steps: 0", bg=self.bg, fg=self.text,
            font=("Segoe UI", 11),
        )
        self.step_label.pack(anchor="w", pady=3)

        self.energy_label = tk.Label(
            left, text="Energy: --", bg=self.bg, fg=self.text,
            font=("Segoe UI", 11),
        )
        self.energy_label.pack(anchor="w", pady=(8, 3))

        self.battery = ttk.Progressbar(
            left, orient="horizontal", mode="determinate",
            length=330, maximum=100,
        )
        self.battery.pack(anchor="w", pady=(0, 8))

        tk.Label(
            right, text="MISSION TELEMETRY",
            font=("Segoe UI", 12, "bold"),
            bg=self.panel, fg=self.text,
        ).pack(anchor="w", padx=14, pady=(14, 8))

        self.mode_label = self._info_label(right, "Mode: initializing")
        self.clue_label = self._info_label(right, "Latest clue: none")
        self.belief_label = self._info_label(right, "Estimate: unavailable")
        self.message_label = self._info_label(right, "Waiting for first action")

        tk.Label(
            right, text="DECISION & EVENT LOG",
            font=("Segoe UI", 11, "bold"),
            bg=self.panel, fg=self.text,
        ).pack(anchor="w", padx=14, pady=(14, 6))

        log_frame = tk.Frame(right, bg=self.panel)
        log_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.log = tk.Text(
            log_frame,
            bg="#0d141c",
            fg="#d5e2ef",
            insertbackground=self.text,
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            state="disabled",
        )
        scrollbar = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log.yview
        )
        self.log.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

        self._draw_grid()

    def _info_label(self, parent, initial_text):
        label = tk.Label(
            parent,
            text=initial_text,
            bg=self.panel,
            fg=self.text,
            font=("Segoe UI", 10),
            justify="left",
            anchor="w",
            wraplength=300,
        )
        label.pack(fill="x", padx=14, pady=5)
        return label

    def _close(self):
        self.closed = True
        self.root.destroy()

    def _draw_grid(self, observation=None, eve_position=None):
        """Draw only public positions, except for confirmed EVE."""
        self.canvas.delete("all")

        size = 62
        gap = 7
        total = self.grid_size * (size + gap)
        start_x = (380 - total) // 2
        start_y = 12

        current = (
            tuple(observation["position"]) if observation else None
        )
        visited = (
            {tuple(p) for p in observation.get("visited", [])}
            if observation else set()
        )
        station = None
        if observation is not None:
            # The recharge station is supplied separately by refresh().
            station = getattr(self, "_station", None)

        for row in range(self.grid_size):
            for col in range(self.grid_size):
                cell = (row, col)
                x1 = start_x + col * (size + gap)
                y1 = start_y + row * (size + gap)
                x2, y2 = x1 + size, y1 + size

                color = "#253443"
                label = ""

                if cell in visited:
                    color = "#304557"

                if cell == station:
                    color = "#735b25"
                    label = "CHARGE"

                if current == cell:
                    color = "#146b58"
                    label = "WALL-E"

                if eve_position is not None and cell == eve_position:
                    color = "#7c2940"
                    label = "EVE"

                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=color, outline="#3d5062", width=1,
                )
                if label:
                    self.canvas.create_text(
                        (x1 + x2) / 2, (y1 + y2) / 2,
                        text=label, fill="white",
                        font=("Segoe UI", 8, "bold"),
                    )

    def log_event(self, message):
        """Append one line without making the log editable."""
        if self.closed:
            return
        self.log.configure(state="normal")
        self.log.insert("end", message + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def refresh(self, observation, decision, agent, station):
        """Refresh dashboard after an action."""
        if self.closed:
            return

        self._station = tuple(station)
        clue = observation.get("sensor_clue")
        if clue:
            self.latest_clue = clue

        self._draw_grid(
            observation,
            tuple(observation["position"]) if observation.get("found") else None,
        )

        energy = observation["energy"]
        maximum = observation["max_energy"]
        percent = 100 * energy / maximum if maximum else 0

        self.position_label.configure(
            text=f"Position: {tuple(observation['position'])}"
        )
        self.step_label.configure(
            text=f"Steps: {observation['step_count']}  |  "
                 f"Visited: {observation['visited_count']}"
        )
        self.energy_label.configure(
            text=f"Energy: {energy}/{maximum}"
        )
        self.battery["value"] = percent

        self.mode_label.configure(
            text=f"Mode: {decision.get('mode', 'unknown').upper()}"
        )
        self.clue_label.configure(
            text=f"Latest clue: {self.latest_clue}"
        )

        confidence = agent.confidence_summary()
        self.belief_label.configure(
            text=(
                f"Estimated EVE: {tuple(confidence['estimated_location'])}\n"
                f"Belief confidence: {confidence['confidence']:.1%}"
            )
        )
        self.message_label.configure(text=observation["message"])

        if observation["found"]:
            self.status.configure(
                text="EVE FOUND — MISSION COMPLETE",
                fg=self.green,
            )
        else:
            self.status.configure(
                text="MISSION IN PROGRESS",
                fg=self.yellow,
            )

        self.root.update_idletasks()
        self.root.update()

    def show_final(self, report):
        """Display the final outcome and keep the window open."""
        if self.closed:
            return

        if report["mission_status"] == "found":
            self.status.configure(
                text="EVE FOUND — MISSION COMPLETE",
                fg=self.green,
            )
        else:
            self.status.configure(
                text="MISSION ENDED — SEE REPORT",
                fg=self.yellow,
            )

        self.log_event(
            f"FINAL REPORT: {report['mission_status'].upper()} | "
            f"Steps: {report['steps']} | "
            f"Confidence: {report['confidence']:.1%}"
        )
        self.log_event("The window will remain open until you close it.")
        self.root.mainloop()
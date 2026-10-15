"""Simulated grid world for WALL-E and EVE's Signal."""

import json
from pathlib import Path


DIRECTIONS = {
    "north": (-1, 0),
    "south": (1, 0),
    "east": (0, 1),
    "west": (0, -1),
}


class GridEnvironment:
    """Environment that keeps EVE's true position hidden from the agent."""

    def __init__(self, config_path="config.json"):
        path = Path(config_path)
        with path.open("r", encoding="utf-8") as file:
            self.config = json.load(file)

        self.grid_size = int(self.config["grid_size"])
        self.position = tuple(self.config["start_position"])
        self.eve_position = tuple(self.config["eve_position"])
        self.recharge_station = tuple(self.config["recharge_station"])

        self.max_energy = int(self.config["max_energy"])
        self.energy = int(self.config["initial_energy"])
        self.move_cost = int(self.config["move_cost"])
        self.scan_cost = int(self.config["scan_cost"])
        self.recharge_amount = int(self.config["recharge_amount"])
        self.signal_radius = int(self.config["signal_radius"])

        self.step_count = 0
        self.found = False
        self.visited = {self.position}
        self.evidence = []
        self.latest_message = "Mission initialized."
        self.latest_clue = None

        self._validate_config()

        if self.position == self.eve_position:
            self.found = True
            self.latest_message = "EVE is at the starting location."

    def _validate_config(self):
        """Reject invalid configuration values before the mission begins."""
        if self.grid_size < 2:
            raise ValueError("grid_size must be at least 2.")

        for name, position in (
            ("start_position", self.position),
            ("eve_position", self.eve_position),
            ("recharge_station", self.recharge_station),
        ):
            if not self.in_bounds(position):
                raise ValueError(f"{name} is outside the grid.")

        if self.energy < 0 or self.energy > self.max_energy:
            raise ValueError("initial_energy must be between 0 and max_energy.")

        if self.max_energy < 1:
            raise ValueError("max_energy must be positive.")

        if self.move_cost < 1 or self.scan_cost < 1:
            raise ValueError("Movement and scan costs must be positive.")

        if self.recharge_amount < 1:
            raise ValueError("recharge_amount must be positive.")

        if self.signal_radius < 0:
            raise ValueError("signal_radius cannot be negative.")

    def in_bounds(self, position):
        """Return True if a position is inside the square grid."""
        row, col = position
        return 0 <= row < self.grid_size and 0 <= col < self.grid_size

    @staticmethod
    def manhattan(a, b):
        """Distance between two cells when movement is along grid edges."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def observe(self):
        """Return public state without exposing EVE's hidden coordinates."""
        return {
            "position": list(self.position),
            "energy": self.energy,
            "max_energy": self.max_energy,
            "found": self.found,
            "message": self.latest_message,
            "sensor_clue": self.latest_clue,
            "visited_count": len(self.visited),
            "visited": [list(p) for p in sorted(self.visited)],
            "step_count": self.step_count,
            "at_station": self.position == self.recharge_station,
            "evidence_count": len(self.evidence),
        }

    def _finish_action(self, message, clue=None):
        """Update the action counter and return a fresh observation."""
        self.step_count += 1
        self.latest_message = message
        self.latest_clue = clue
        return self.observe()

    def _sensor_clue(self):
        """Generate a directional clue without revealing EVE's coordinates."""
        if self.position == self.eve_position:
            return "at_location"

        distance = self.manhattan(self.position, self.eve_position)

        if distance > self.signal_radius:
            return "no_signal"

        row_delta = self.eve_position[0] - self.position[0]
        col_delta = self.eve_position[1] - self.position[1]

        # Follow the axis with the larger distance. Vertical wins ties.
        if abs(row_delta) >= abs(col_delta) and row_delta != 0:
            return "south" if row_delta > 0 else "north"

        if col_delta != 0:
            return "east" if col_delta > 0 else "west"

        return "at_location"

    def step(self, action):
        """
        Execute an action and return an observation.

        Accepted actions:
            "scan"
            "recharge"
            {"move": "north"}  # north, south, east, or west
        """
        if self.found:
            return self.observe()

        if action == "scan":
            return self.scan()

        if action == "recharge":
            return self.recharge()

        if isinstance(action, dict) and "move" in action:
            return self.move(action["move"])

        return self._finish_action(
            f"Invalid action: {action!r}. No energy consumed."
        )

    def move(self, direction):
        """Move one cell in a valid direction."""
        if direction not in DIRECTIONS:
            return self._finish_action(f"Invalid direction: {direction!r}.")

        if self.energy < self.move_cost:
            return self._finish_action("Move rejected: insufficient energy.")

        dr, dc = DIRECTIONS[direction]
        destination = (self.position[0] + dr, self.position[1] + dc)

        if not self.in_bounds(destination):
            return self._finish_action(
                f"Move {direction} blocked by the grid boundary."
            )

        self.energy -= self.move_cost
        self.position = destination
        self.visited.add(destination)

        if self.position == self.eve_position:
            self.found = True
            self.evidence.append({
                "step": self.step_count + 1,
                "type": "direct_contact",
                "position": list(self.position),
                "detail": "WALL-E entered EVE's cell.",
            })
            return self._finish_action(
                "EVE FOUND! Direct contact confirmed.",
                clue="at_location",
            )

        return self._finish_action(
            f"Moved {direction} to {self.position}. "
            "A new scan is needed for a fresh clue."
        )

    def scan(self):
        """Spend energy to scan and record the sensor result."""
        if self.energy < self.scan_cost:
            return self._finish_action("Scan rejected: insufficient energy.")

        self.energy -= self.scan_cost
        clue = self._sensor_clue()

        self.evidence.append({
            "step": self.step_count + 1,
            "type": "scan",
            "position": list(self.position),
            "clue": clue,
            "detail": (
                "Direct confirmation of EVE."
                if clue == "at_location"
                else f"Sensor returned {clue!r}."
            ),
        })

        if clue == "at_location":
            self.found = True
            message = "EVE FOUND! Scan directly confirmed her location."
        elif clue == "no_signal":
            message = "Scan complete: no signal in range."
        else:
            message = f"Scan complete: signal points {clue}."

        return self._finish_action(message, clue=clue)

    def recharge(self):
        """Recharge only at the station, up to maximum energy."""
        if self.position != self.recharge_station:
            return self._finish_action(
                "Recharge rejected: WALL-E is not at the station."
            )

        if self.energy >= self.max_energy:
            return self._finish_action(
                "Recharge skipped: battery is already full."
            )

        before = self.energy
        self.energy = min(
            self.max_energy,
            self.energy + self.recharge_amount,
        )
        gained = self.energy - before

        return self._finish_action(
            f"Recharged at station: +{gained} energy "
            f"({self.energy}/{self.max_energy})."
        )

    def is_at_eve(self):
        """Return mission status, not a comparison against hidden coordinates."""
        return self.found
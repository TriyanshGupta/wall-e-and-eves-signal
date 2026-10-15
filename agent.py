"""Belief-based autonomous agent for WALL-E."""

from environment import DIRECTIONS


class WallEAgent:
    """Choose actions from observations, beliefs, and energy constraints."""

    def __init__(self, config):
        self.size = int(config["grid_size"])
        self.station = tuple(config["recharge_station"])
        self.move_cost = int(config["move_cost"])
        self.scan_cost = int(config["scan_cost"])
        self.max_energy = int(config["max_energy"])
        self.signal_radius = int(config["signal_radius"])

        cells = [
            (r, c)
            for r in range(self.size)
            for c in range(self.size)
        ]
        self.beliefs = {cell: 1.0 / len(cells) for cell in cells}

        self.last_scan_position = None
        self.active_clue = None
        self.clue_position = None
        self.evidence = []
        self.mode = "initializing"
        self.last_reason = "Starting with a uniform location belief."
        self.found = False

    @staticmethod
    def manhattan(a, b):
        """Return Manhattan distance between two grid cells."""
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    def _normalize(self):
        """Normalize probabilities; recover safely if all weights are zero."""
        total = sum(self.beliefs.values())

        if total <= 0:
            uniform = 1.0 / len(self.beliefs)
            self.beliefs = {
                cell: uniform for cell in self.beliefs
            }
        else:
            self.beliefs = {
                cell: probability / total
                for cell, probability in self.beliefs.items()
            }

    def update_beliefs(self, observation):
        """Use fresh sensor evidence; never treat movement messages as clues."""
        position = tuple(observation["position"])

        if observation.get("found"):
            self.found = True
            self.beliefs = {cell: 0.0 for cell in self.beliefs}
            self.beliefs[position] = 1.0
            self.active_clue = "at_location"
            self.clue_position = position
            return

        # A clue belongs to the position where the scan was taken.
        # Moving invalidates that clue for navigation.
        if self.clue_position is not None and position != self.clue_position:
            self.active_clue = None
            self.clue_position = None

        clue = observation.get("sensor_clue")

        # Movement observations have sensor_clue=None. Ignore them.
        if clue is None:
            return

        self.last_scan_position = position
        self.active_clue = clue
        self.clue_position = position

        self.evidence.append({
            "position": list(position),
            "clue": clue,
            "step": observation.get("step_count", 0),
        })

        if clue == "at_location":
            self.beliefs = {cell: 0.0 for cell in self.beliefs}
            self.beliefs[position] = 1.0
            self.found = True
            return

        updated = {}

        for cell, probability in self.beliefs.items():
            row_delta = cell[0] - position[0]
            col_delta = cell[1] - position[1]
            distance = self.manhattan(position, cell)

            if clue == "no_signal":
                consistent = distance > self.signal_radius

            elif clue == "north":
                consistent = (
                    row_delta < 0
                    and abs(row_delta) >= abs(col_delta)
                )

            elif clue == "south":
                consistent = (
                    row_delta > 0
                    and abs(row_delta) >= abs(col_delta)
                )

            elif clue == "east":
                consistent = (
                    col_delta > 0
                    and abs(row_delta) < abs(col_delta)
                )

            elif clue == "west":
                consistent = (
                    col_delta < 0
                    and abs(col_delta) >= abs(row_delta)
                )

            else:
                consistent = True

            updated[cell] = probability if consistent else 0.0

        # Do not destroy the previous distribution if evidence is inconsistent.
        if sum(updated.values()) > 0:
            self.beliefs = updated
            self._normalize()

    def confidence_summary(self):
        """Return the most likely cell and its estimated probability."""
        cell = max(self.beliefs, key=self.beliefs.get)
        return {
            "estimated_location": list(cell),
            "confidence": round(self.beliefs[cell], 4),
        }

    def _step_toward(self, target, position):
        """Choose one legal step toward a target using the shortest grid route."""
        row_delta = target[0] - position[0]
        col_delta = target[1] - position[1]

        if row_delta == 0 and col_delta == 0:
            return None

        # Favor the axis with the larger remaining distance.
        if abs(row_delta) >= abs(col_delta) and row_delta != 0:
            return "south" if row_delta > 0 else "north"

        return "east" if col_delta > 0 else "west"

    def _return_action(self, position):
        """Return one step toward the recharge station."""
        direction = self._step_toward(self.station, position)

        if direction is None:
            return "recharge", "At the station; recharge before continuing."

        return {
            "move": direction
        }, f"Returning to the station via {direction} to protect the energy reserve."

    def decide(self, observation):
        """Return a dictionary containing the next action and its explanation."""
        position = tuple(observation["position"])
        energy = int(observation["energy"])
        max_energy = int(observation["max_energy"])
        visited = {
            tuple(cell) for cell in observation.get("visited", [])
        }

        if observation.get("found") or self.found:
            self.mode = "mission complete"
            self.last_reason = "EVE has been directly confirmed. Stop immediately."
            return {
                "action": "stop",
                "reason": self.last_reason,
                "mode": self.mode,
            }

        station_distance = self.manhattan(position, self.station)
        return_reserve = station_distance * self.move_cost

        if position == self.station and energy < max_energy:
            self.mode = "recharging"
            self.last_reason = "At the station with a battery below maximum."
            return {
                "action": "recharge",
                "reason": self.last_reason,
                "mode": self.mode,
            }

        # Preserve enough energy to reach the station safely.
        if position != self.station and energy < (
            return_reserve + self.scan_cost
        ):
            self.mode = "returning"
            action, reason = self._return_action(position)
            self.last_reason = reason
            return {"action": action, "reason": reason, "mode": self.mode}

        # Scan once whenever WALL-E arrives at a new position.
        if self.last_scan_position != position:
            if energy - self.scan_cost >= return_reserve:
                self.mode = "scanning"
                reason = (
                    "Scan the current cell for fresh evidence while "
                    "preserving the return-energy reserve."
                )
                self.last_reason = reason
                return {
                    "action": "scan",
                    "reason": reason,
                    "mode": self.mode,
                }

            if position != self.station:
                self.mode = "returning"
                action, reason = self._return_action(position)
                self.last_reason = reason
                return {
                    "action": action,
                    "reason": reason,
                    "mode": self.mode,
                }

        # Use a directional clue only at the position where it was observed.
        if (
            self.active_clue in DIRECTIONS
            and self.clue_position == position
        ):
            direction = self.active_clue
            dr, dc = DIRECTIONS[direction]
            destination = (position[0] + dr, position[1] + dc)

            if (
                0 <= destination[0] < self.size
                and 0 <= destination[1] < self.size
            ):
                after_move = energy - self.move_cost
                destination_reserve = (
                    self.manhattan(destination, self.station)
                    * self.move_cost
                )

                if after_move >= destination_reserve + self.scan_cost:
                    self.mode = "following clue"
                    reason = (
                        f"The fresh clue points {direction}; move one cell "
                        "that way, then scan again."
                    )
                    self.last_reason = reason
                    return {
                        "action": {"move": direction},
                        "reason": reason,
                        "mode": self.mode,
                    }

            # Do not keep a clue that cannot safely be followed.
            self.active_clue = None

        # No usable clue: choose a likely unvisited target.
        candidates = [
            cell for cell in self.beliefs
            if cell not in visited and cell != position
        ]

        if not candidates:
            candidates = [
                cell for cell in self.beliefs if cell != position
            ]

        if not candidates:
            self.mode = "exploring"
            reason = "No new target remains; request another scan."
            self.last_reason = reason
            return {
                "action": "scan",
                "reason": reason,
                "mode": self.mode,
            }

        target = max(candidates, key=self.beliefs.get)
        direction = self._step_toward(target, position)

        if direction is None:
            self.mode = "exploring"
            return {
                "action": "scan",
                "reason": "Scan the current cell to obtain fresh evidence.",
                "mode": self.mode,
            }

        dr, dc = DIRECTIONS[direction]
        destination = (position[0] + dr, position[1] + dc)
        after_move = energy - self.move_cost
        destination_reserve = (
            self.manhattan(destination, self.station) * self.move_cost
        )

        if after_move < destination_reserve + self.scan_cost:
            if position != self.station:
                self.mode = "returning"
                action, reason = self._return_action(position)
                self.last_reason = reason
                return {
                    "action": action,
                    "reason": reason,
                    "mode": self.mode,
                }

            self.mode = "recharging"
            return {
                "action": "recharge",
                "reason": "Recharge before starting another search leg.",
                "mode": self.mode,
            }

        self.mode = "exploring"
        reason = (
            f"No usable fresh directional clue. Explore toward the most "
            f"likely unvisited target {target}."
        )
        self.last_reason = reason
        return {
            "action": {"move": direction},
            "reason": reason,
            "mode": self.mode,
        }
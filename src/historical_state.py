
import json
import os
from datetime import datetime, timezone


class HistoricalState:
    def __init__(self, file_path="historical_states.json"):
        self.file_path = file_path

        if not os.path.exists(self.file_path):
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump([], file)

    def save_state(self, state):
        """Save cloud topology state with a timestamp."""
        history = self.get_all_states()

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "state": state
        }

        history.append(record)

        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump(history, file, indent=4)

        return record

    def get_all_states(self):
        """Return all previously saved states."""
        if not os.path.exists(self.file_path):
            return []

        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def get_state_by_timestamp(self, timestamp):
        """Find a state using its exact timestamp."""
        for record in self.get_all_states():
            if record["timestamp"] == timestamp:
                return record["state"]

        return None

    def get_latest_state(self):
        """Return the most recently saved state."""
        history = self.get_all_states()

        if not history:
            return None

        return history[-1]["state"]

    def clear_history(self):
        """Remove all saved historical states."""
        with open(self.file_path, "w", encoding="utf-8") as file:
            json.dump([], file, indent=4)


import json
from pathlib import Path


class StatePersistence:
    def __init__(self, file_path="data/aerodrift_state.json"):
        self.file_path = Path(file_path)

    def save_state(self, state):
        """Save application state to a JSON file."""
        self.file_path.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(state, file, indent=4)

        return {
            "status": "saved",
            "file_path": str(self.file_path)
        }

    def load_state(self):
        """Load previously saved state from a JSON file."""
        if not self.file_path.exists():
            return {}

        with self.file_path.open("r", encoding="utf-8") as file:
            return json.load(file)

    def clear_state(self):
        """Delete the saved state file."""
        if self.file_path.exists():
            self.file_path.unlink()

        return {"status": "cleared"}

from src.state_persistence import StatePersistence


def test_save_and_load_state(tmp_path):
    file_path = tmp_path / "aerodrift_state.json"
    persistence = StatePersistence(file_path)

    state = {
        "project": "AeroDrift",
        "status": "running",
        "completed_tasks": 3
    }

    result = persistence.save_state(state)

    assert result["status"] == "saved"
    assert file_path.exists()
    assert persistence.load_state() == state


def test_load_state_when_file_does_not_exist(tmp_path):
    file_path = tmp_path / "missing_state.json"
    persistence = StatePersistence(file_path)

    assert persistence.load_state() == {}


def test_clear_state(tmp_path):
    file_path = tmp_path / "aerodrift_state.json"
    persistence = StatePersistence(file_path)

    persistence.save_state({"status": "running"})
    result = persistence.clear_state()

    assert result["status"] == "cleared"
    assert not file_path.exists()
    assert persistence.load_state() == {}
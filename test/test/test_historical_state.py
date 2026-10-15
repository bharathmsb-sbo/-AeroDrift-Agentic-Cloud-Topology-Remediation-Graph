
import json
from src.historical_state import HistoricalState


def test_save_and_get_latest_state(tmp_path):
    file_path = tmp_path / "history.json"
    history = HistoricalState(str(file_path))

    state = {
        "vpc": "vpc-001",
        "subnet": "subnet-001"
    }

    record = history.save_state(state)

    assert record["state"] == state
    assert record["timestamp"] is not None
    assert history.get_latest_state() == state


def test_get_all_states(tmp_path):
    file_path = tmp_path / "history.json"
    history = HistoricalState(str(file_path))

    history.save_state({"vpc": "vpc-001"})
    history.save_state({"vpc": "vpc-002"})

    states = history.get_all_states()

    assert len(states) == 2
    assert states[0]["state"]["vpc"] == "vpc-001"
    assert states[1]["state"]["vpc"] == "vpc-002"


def test_get_state_by_timestamp(tmp_path):
    file_path = tmp_path / "history.json"
    history = HistoricalState(str(file_path))

    record = history.save_state({"vpc": "vpc-001"})

    result = history.get_state_by_timestamp(record["timestamp"])

    assert result == {"vpc": "vpc-001"}


def test_get_missing_timestamp(tmp_path):
    file_path = tmp_path / "history.json"
    history = HistoricalState(str(file_path))

    assert history.get_state_by_timestamp("invalid-timestamp") is None


def test_empty_history(tmp_path):
    file_path = tmp_path / "history.json"
    history = HistoricalState(str(file_path))

    assert history.get_all_states() == []
    assert history.get_latest_state() is None


def test_clear_history(tmp_path):
    file_path = tmp_path / "history.json"
    history = HistoricalState(str(file_path))

    history.save_state({"vpc": "vpc-001"})
    history.clear_history()

    assert history.get_all_states() == []
    assert history.get_latest_state() is None

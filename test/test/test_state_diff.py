from src.state_diff import StateDiff


def test_added_resource():
    old_state = {"vpc-001": {"type": "vpc"}}
    new_state = {
        "vpc-001": {"type": "vpc"},
        "sg-001": {"type": "security_group"},
    }

    result = StateDiff.compare_states(old_state, new_state)

    assert result["sg-001"]["old"] is None
    assert result["sg-001"]["new"] == {"type": "security_group"}


def test_removed_resource():
    old_state = {
        "vpc-001": {"type": "vpc"},
        "sg-001": {"type": "security_group"},
    }
    new_state = {"vpc-001": {"type": "vpc"}}

    result = StateDiff.compare_states(old_state, new_state)

    assert result["sg-001"]["old"] == {"type": "security_group"}
    assert result["sg-001"]["new"] is None


def test_unchanged_state():
    state = {"vpc-001": {"type": "vpc"}}

    result = StateDiff.compare_states(state, state)

    assert result == {}


def test_changed_resource():
    old_state = {"sg-001": {"type": "security_group", "port": 80}}
    new_state = {"sg-001": {"type": "security_group", "port": 443}}

    result = StateDiff.compare_states(old_state, new_state)

    assert result["sg-001"]["old"]["port"] == 80
    assert result["sg-001"]["new"]["port"] == 443

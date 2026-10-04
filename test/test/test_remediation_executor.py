from src.remediation_executor import RemediationExecutor


def test_execute_revoke_security_group_ingress():
    executor = RemediationExecutor()

    action = {
        "action": "revoke_security_group_ingress",
        "security_group_id": "sg-001",
        "port": 22,
    }

    result = executor.execute(action)

    assert result["status"] == "executed"
    assert result["action"] == "revoke_security_group_ingress"
    assert result["security_group_id"] == "sg-001"
    assert result["port"] == 22


def test_execute_unsupported_action():
    executor = RemediationExecutor()

    action = {
        "action": "unknown_action"
    }

    result = executor.execute(action)

    assert result["status"] == "skipped"
    assert result["reason"] == "Unsupported action"
from src.remediation_audit import RemediationAudit


def test_remediation_audit_record():
    audit = RemediationAudit()

    drift = {
        "type": "open_security_group_port",
        "security_group_id": "sg-001",
        "port": 22
    }

    action = {
        "action": "revoke_security_group_ingress",
        "security_group_id": "sg-001"
    }

    result = {
        "status": "success"
    }

    record = audit.record(drift, action, result)

    assert record["drift"] == drift
    assert record["action"] == action
    assert record["result"] == result


def test_remediation_audit_get_records():
    audit = RemediationAudit()

    audit.record(
        {"type": "test_drift"},
        {"action": "test_action"},
        {"status": "success"}
    )

    records = audit.get_records()

    assert len(records) == 1
from src.remediation_workflow import RemediationWorkflow


def test_remediation_workflow_open_port():
    workflow = RemediationWorkflow()

    drift = {
        "type": "open_security_group_port",
        "security_group_id": "sg-001",
        "port": 22,
        "protocol": "tcp",
        "cidr": "0.0.0.0/0"
    }

    result = workflow.run(drift)

    assert result["status"] == "completed"
    assert result["action"]["action"] == "revoke_security_group_ingress"


def test_remediation_workflow_unsupported_drift():
    workflow = RemediationWorkflow()

    drift = {
        "type": "unknown_drift"
    }

    result = workflow.run(drift)

    assert result["status"] == "skipped"
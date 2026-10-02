from src.remediation_agent import RemediationAgent


def test_open_security_group_port():
    agent = RemediationAgent()

    drift = {
        "type": "open_security_group_port",
        "security_group_id": "sg-001",
        "port": 22,
        "protocol": "tcp",
        "cidr": "0.0.0.0/0",
    }

    result = agent.analyze_drift(drift)

    assert result["action"] == "revoke_security_group_ingress"
    assert result["security_group_id"] == "sg-001"
    assert result["port"] == 22
    assert result["protocol"] == "tcp"
    assert result["cidr"] == "0.0.0.0/0"


def test_unsupported_drift():
    agent = RemediationAgent()

    drift = {
        "type": "unknown_drift"
    }

    result = agent.analyze_drift(drift)

    assert result["action"] == "no_remediation"
    assert result["reason"] == "Unsupported drift type"
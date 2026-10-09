from src.remediation_logger import RemediationLogger


def test_remediation_logger_record():
    logger = RemediationLogger()

    result = logger.log(
        drift="open_security_group_port",
        action="revoke_security_group_ingress",
        result="executed"
    )

    assert result["drift"] == "open_security_group_port"
    assert result["action"] == "revoke_security_group_ingress"
    assert result["result"] == "executed"


def test_remediation_logger_get_logs():
    logger = RemediationLogger()

    logger.log(
        drift="open_security_group_port",
        action="revoke_security_group_ingress",
        result="executed"
    )

    logs = logger.get_logs()

    assert len(logs) == 1
    assert logs[0]["action"] == "revoke_security_group_ingress"
    assert logs[0]["result"] == "executed"
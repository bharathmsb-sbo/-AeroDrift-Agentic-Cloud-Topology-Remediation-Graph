"""
Unit tests for the AST remediation code generation, controlled dry-run execution,
and remediation verification modules.
"""

from src.ingestion.mock_aws import MockAWSProvider
from src.remediation.code_generator import RemediationCodeGenerator, generate_remediation_code
from src.remediation.executor import MockEC2Client, RemediationExecutor, execute_remediation
from src.remediation.verifier import RemediationVerifier, verify_remediation


def test_remediation_code_generation_structure():
    """Verify AST code generator creates the expected boto3 revoke call."""
    generator = RemediationCodeGenerator()
    code = generator.generate_revoke_ingress(
        security_group="sg-001",
        protocol="tcp",
        port=22,
        source="0.0.0.0/0",
    )

    assert "ec2.revoke_security_group_ingress" in code
    assert "sg-001" in code
    assert "0.0.0.0/0" in code
    assert "22" in code
    assert "tcp" in code


def test_generate_remediation_code_convenience_function():
    """Verify module-level generate_remediation_code helper function."""
    finding = {
        "security_group": "sg-001",
        "protocol": "tcp",
        "port": 22,
        "source": "0.0.0.0/0",
    }
    code = generate_remediation_code(finding)
    assert "revoke_security_group_ingress" in code


def test_controlled_remediation_executor_dry_run():
    """Verify that RemediationExecutor removes the offending rule upon execution."""
    provider = MockAWSProvider()
    resources = provider.get_all_resources()

    # Pre-check: Rule exists in mock security group
    sg = resources["security_groups"][0]
    assert len(sg.ingress_rules) == 1

    finding = {
        "security_group": "sg-001",
        "protocol": "tcp",
        "port": 22,
        "source": "0.0.0.0/0",
    }
    code = generate_remediation_code(finding)

    # RemediationExecutor takes the resources dict
    executor = RemediationExecutor(resources)
    executor.execute(code)

    # Rule must now be removed from simulated state
    assert len(sg.ingress_rules) == 0


def test_remediation_verifier_and_execute_remediation():
    """Verify RemediationVerifier before and after execute_remediation."""
    provider = MockAWSProvider()
    resources = provider.get_all_resources()

    finding = {
        "security_group": "sg-001",
        "protocol": "tcp",
        "port": 22,
        "source": "0.0.0.0/0",
    }

    # Before execution: rule exists, so verify_remediation is False (not resolved)
    assert verify_remediation(resources, finding) is False

    # Execute remediation with resources and finding
    returned_code = execute_remediation(resources, finding)
    assert "revoke_security_group_ingress" in returned_code

    # After execution: rule is gone, so verify_remediation is True (resolved)
    assert verify_remediation(resources, finding) is True
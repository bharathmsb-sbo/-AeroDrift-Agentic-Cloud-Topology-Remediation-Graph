import ast

from src.remediation.code_generator import generate_remediation_code


class MockEC2Client:
    """
    Simulates an AWS EC2 client.

    This does NOT connect to AWS.
    It only records what remediation action
    AeroDrift would perform.
    """

    def __init__(self) -> None:
        self.actions: list[dict] = []

    def revoke_security_group_ingress(
        self,
        GroupId: str,
        IpPermissions: list[dict],
    ) -> None:
        """
        Simulate revoking a security group ingress rule.
        """

        action = {
            "action": "revoke_security_group_ingress",
            "GroupId": GroupId,
            "IpPermissions": IpPermissions,
        }

        self.actions.append(action)

        print("\n[DRY RUN] Remediation executed")
        print(f"Security Group: {GroupId}")
        print(f"Permissions: {IpPermissions}")


class RemediationExecutor:
    """
    Executes AeroDrift remediation code
    in a controlled local dry-run environment.
    """

    def __init__(self) -> None:
        self.ec2 = MockEC2Client()

    def validate_code(self, code: str) -> bool:
        """
        Validate that the generated code
        is valid Python syntax.
        """

        try:
            ast.parse(code)
            return True

        except SyntaxError as error:
            print(f"Invalid remediation code: {error}")
            return False

    def execute(self, code: str) -> None:
        """
        Execute generated remediation code
        using the mock EC2 client.

        No real AWS API is called.
        """

        if not self.validate_code(code):
            raise ValueError(
                "Remediation code validation failed."
            )

        safe_namespace = {
            "ec2": self.ec2,
            "__builtins__": {},
        }

        exec(
            code,
            safe_namespace,
        )

    def execute_finding(self, finding: dict) -> str:
        """
        Generate remediation code from a drift finding
        and execute it in dry-run mode.
        """

        code = generate_remediation_code(finding)

        print("\nGenerated Remediation Code:")
        print(code)

        self.execute(code)

        return code


def execute_remediation(finding: dict) -> str:
    """
    Convenience function for executing
    remediation for a detected finding.
    """

    executor = RemediationExecutor()

    return executor.execute_finding(finding)
import ast

from src.remediation.code_generator import generate_remediation_code
from src.remediation.verifier import verify_remediation


class MockEC2Client:
    """
    Simulates an AWS EC2 client.

    This does NOT connect to AWS.
    It modifies the simulated security group
    state for testing remediation.
    """

    def __init__(self, resources: dict) -> None:
        self.resources = resources
        self.actions: list[dict] = []

    def revoke_security_group_ingress(
        self,
        GroupId: str,
        IpPermissions: list[dict],
    ) -> None:
        """
        Simulate revoking a security group ingress rule.
        """

        for security_group in self.resources["security_groups"]:

            if security_group.group_id != GroupId:
                continue

            remaining_rules = []

            for rule in security_group.ingress_rules:

                should_remove = False

                for permission in IpPermissions:

                    if (
                        rule.get("protocol")
                        == permission.get("IpProtocol")
                        and rule.get("port")
                        == permission.get("FromPort")
                    ):
                        for ip_range in permission.get(
                            "IpRanges", []
                        ):
                            if (
                                rule.get("source")
                                == ip_range.get("CidrIp")
                            ):
                                should_remove = True

                if not should_remove:
                    remaining_rules.append(rule)

            security_group.ingress_rules = remaining_rules

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

    def __init__(self, resources: dict) -> None:
        self.resources = resources
        self.ec2 = MockEC2Client(resources)

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
        Generate remediation code from a drift finding,
        execute it in dry-run mode,
        and verify the remediation.
        """

        code = generate_remediation_code(finding)

        print("\nGenerated Remediation Code:")
        print(code)

        self.execute(code)

        verified = verify_remediation(
            self.resources,
            finding,
        )

        if verified:
            print("\n[VERIFICATION] Remediation verified")
            print(
                f"Security Group: "
                f"{finding['security_group']}"
            )
            print("Status: DRIFT RESOLVED")
        else:
            print("\n[VERIFICATION] Remediation verification failed")
            print(
                f"Security Group: "
                f"{finding['security_group']}"
            )
            print("Status: DRIFT STILL PRESENT")

        return code


def execute_remediation(
    resources: dict,
    finding: dict,
) -> str:
    """
    Convenience function for executing
    remediation for a detected finding.
    """

    executor = RemediationExecutor(resources)

    return executor.execute_finding(finding)
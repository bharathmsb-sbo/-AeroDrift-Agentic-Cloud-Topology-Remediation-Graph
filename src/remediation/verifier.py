class RemediationVerifier:
    """
    Verifies whether a detected security group
    ingress rule has been removed.
    """

    def __init__(self, resources: dict) -> None:
        self.resources = resources

    def verify_ingress_removed(
        self,
        security_group_id: str,
        protocol: str,
        port: int,
        source: str,
    ) -> bool:
        """
        Check whether the unwanted ingress rule
        is still present in the security group.
        """

        for security_group in self.resources["security_groups"]:
            if security_group.group_id != security_group_id:
                continue

            for rule in security_group.ingress_rules:
                if (
                    rule.get("protocol") == protocol
                    and rule.get("port") == port
                    and rule.get("source") == source
                ):
                    return False

        return True


def verify_remediation(
    resources: dict,
    finding: dict,
) -> bool:
    """
    Verify whether the detected drift
    has been removed.
    """

    verifier = RemediationVerifier(resources)

    return verifier.verify_ingress_removed(
        security_group_id=finding["security_group"],
        protocol=finding["protocol"],
        port=finding["port"],
        source=finding["source"],
    )
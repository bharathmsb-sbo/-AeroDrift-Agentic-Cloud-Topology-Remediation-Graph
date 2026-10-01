class RemediationAgent:
    def analyze_drift(self, drift):
        if drift.get("type") == "open_security_group_port":
            return {
                "action": "revoke_security_group_ingress",
                "security_group_id": drift.get("security_group_id"),
                "port": drift.get("port"),
                "protocol": drift.get("protocol", "tcp"),
                "cidr": drift.get("cidr", "0.0.0.0/0"),
            }

        return {
            "action": "no_remediation",
            "reason": "Unsupported drift type",
        }
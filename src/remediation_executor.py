class RemediationExecutor:

    def execute(self, action):
        if action.get("action") == "revoke_security_group_ingress":
            return {
                "status": "executed",
                "action": "revoke_security_group_ingress",
                "security_group_id": action.get("security_group_id"),
                "port": action.get("port"),
            }

        return {
            "status": "skipped",
            "reason": "Unsupported action",
        }
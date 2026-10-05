from src.remediation_agent import RemediationAgent
from src.remediation_executor import RemediationExecutor


class RemediationWorkflow:
    def __init__(self):
        self.agent = RemediationAgent()
        self.executor = RemediationExecutor()

    def run(self, drift):
        action = self.agent.analyze_drift(drift)

        if action.get("action") == "no_remediation":
            return {
                "status": "skipped",
                "reason": "No remediation available",
                "action": action
            }

        result = self.executor.execute(action)

        return {
            "status": "completed",
            "action": action,
            "execution": result
        }
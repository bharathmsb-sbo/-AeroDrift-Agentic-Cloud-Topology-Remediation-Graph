class RemediationLogger:
    def __init__(self):
        self.logs = []

    def log(self, drift, action, result):
        entry = {
            "drift": drift,
            "action": action,
            "result": result
        }

        self.logs.append(entry)
        return entry

    def get_logs(self):
        return self.logs
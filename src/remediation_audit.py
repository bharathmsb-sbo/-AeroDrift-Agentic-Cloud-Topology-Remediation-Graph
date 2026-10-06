class RemediationAudit:
    def __init__(self):
        self.records = []

    def record(self, drift, action, result):
        audit_record = {
            "drift": drift,
            "action": action,
            "result": result
        }

        self.records.append(audit_record)

        return audit_record

    def get_records(self):
        return self.records
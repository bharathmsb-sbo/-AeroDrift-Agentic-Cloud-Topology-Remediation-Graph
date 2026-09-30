import time


class GraphAudit:
    def __init__(self, drift_detector, check_interval=1):
        self.drift_detector = drift_detector
        self.check_interval = check_interval

    def monitor(self, timeout=5):
        start_time = time.monotonic()

        while time.monotonic() - start_time < timeout:
            if self.drift_detector.detect_internet_to_database_path():
                detection_time = time.monotonic() - start_time

                return {
                    "detected": True,
                    "detection_time": detection_time
                }

            time.sleep(self.check_interval)

        return {
            "detected": False,
            "detection_time": None
        }
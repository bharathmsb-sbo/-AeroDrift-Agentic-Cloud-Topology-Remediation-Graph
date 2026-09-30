from src.drift_detector import DriftDetector


def test_detect_internet_to_database_path():
    topology = {
        "nodes": [
            {"id": "0.0.0.0/0", "type": "internet"},
            {"id": "subnet-001", "type": "subnet"},
            {"id": "db-001", "type": "database"}
        ],
        "edges": [
            {
                "source": "0.0.0.0/0",
                "target": "subnet-001",
                "relationship": "accessible"
            },
            {
                "source": "subnet-001",
                "target": "db-001",
                "relationship": "contains"
            }
        ]
    }

    detector = DriftDetector(topology)

    assert detector.detect_internet_to_database_path() is True


def test_no_internet_to_database_path():
    topology = {
        "nodes": [
            {"id": "0.0.0.0/0", "type": "internet"},
            {"id": "subnet-001", "type": "subnet"},
            {"id": "db-001", "type": "database"}
        ],
        "edges": [
            {
                "source": "subnet-001",
                "target": "db-001",
                "relationship": "contains"
            }
        ]
    }

    detector = DriftDetector(topology)

    assert detector.detect_internet_to_database_path() is False
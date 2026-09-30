from src.drift_detector import DriftDetector
from src.graph_audit import GraphAudit


def test_graph_audit_detects_new_path_under_5_seconds():
    topology = {
        "nodes": [
            {"id": "0.0.0.0/0", "type": "internet"},
            {"id": "private-db", "type": "database"},
        ],
        "edges": []
    }

    detector = DriftDetector(topology)
    audit = GraphAudit(detector, check_interval=0.1)

    # Initially there is no Internet -> Database path
    assert detector.detect_internet_to_database_path() is False

    # Simulate Security Group change creating a new network path
    topology["edges"].append({
        "source": "0.0.0.0/0",
        "target": "private-db"
    })

    result = audit.monitor(timeout=5)

    assert result["detected"] is True
    assert result["detection_time"] < 5
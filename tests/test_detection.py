"""
Unit tests for Drift Detection engine.
Verifies scanning of topology graph edges for unauthorized public ingress.
"""

import networkx as nx
from src.detection.drift_detector import DriftDetector, detect_drift
from src.topology.graph_engine import build_mock_topology


def test_drift_detection_finds_public_ssh():
    """Verify that detect_public_ingress detects the port 22 open rule."""
    graph = build_mock_topology()
    detector = DriftDetector(graph)
    findings = detector.detect_public_ingress()

    assert len(findings) == 1
    finding = findings[0]
    assert finding["security_group"] == "sg-001"
    assert finding["protocol"] == "tcp"
    assert finding["port"] == 22
    assert finding["source"] == "0.0.0.0/0"


def test_detect_drift_convenience_function():
    """Verify that the module-level detect_drift function returns the expected findings."""
    graph = build_mock_topology()
    findings = detect_drift(graph)

    assert len(findings) == 1
    assert findings[0]["security_group"] == "sg-001"


def test_drift_detection_no_findings_when_clean():
    """Verify that detector returns an empty list when no public ingress edge exists."""
    # Create a benign graph without public ingress
    clean_graph = nx.DiGraph()
    clean_graph.add_node("subnet-private")
    clean_graph.add_node("db-001")
    clean_graph.add_edge("db-001", "subnet-private", relationship="located_in")

    detector = DriftDetector(clean_graph)
    findings = detector.detect_public_ingress()

    assert len(findings) == 0
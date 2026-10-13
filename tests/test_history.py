"""
Unit tests for historical topology storage (SQLite) and graph diff engine.
Uses pytest's tmp_path fixture to ensure isolated database testing.
"""

import networkx as nx
from src.history.database import HistoryDatabase
from src.history.diff import GraphDiff, compare_snapshots
from src.topology.graph_engine import build_mock_topology


def test_history_database_initialize_and_empty(tmp_path):
    """Verify initialization and that get_latest_snapshot returns None when empty."""
    test_db = tmp_path / "test_history.db"
    db = HistoryDatabase(database_path=str(test_db))
    db.initialize()

    assert db.get_latest_snapshot() is None


def test_history_database_save_and_retrieve_snapshot(tmp_path):
    """Verify saving a topology snapshot and retrieving its contents."""
    test_db = tmp_path / "test_history.db"
    db = HistoryDatabase(database_path=str(test_db))
    db.initialize()

    graph = build_mock_topology()
    db.save_snapshot(graph)

    snapshot = db.get_latest_snapshot()
    assert snapshot is not None
    assert snapshot["id"] == 1
    assert snapshot["node_count"] == 6
    assert snapshot["edge_count"] == 4
    assert "nodes" in snapshot["graph_data"]
    assert "edges" in snapshot["graph_data"]


def test_graph_diff_no_changes():
    """Verify that comparing identical snapshots returns empty change sets."""
    graph = build_mock_topology()

    # Create mock serialized snapshot structure
    nodes = [{"id": n, "data": d} for n, d in graph.nodes(data=True)]
    edges = [{"source": u, "target": v, "data": d} for u, v, d in graph.edges(data=True)]
    snapshot = {"graph_data": {"nodes": nodes, "edges": edges}}

    diff = compare_snapshots(snapshot, snapshot)

    assert diff["added_nodes"] == []
    assert diff["removed_nodes"] == []
    assert diff["added_edges"] == []
    assert diff["removed_edges"] == []


def test_graph_diff_detects_drift_remediation():
    """Verify diff engine detects removed public ingress edge after remediation."""
    graph_before = build_mock_topology()

    # Simulate remediated topology by removing the public ingress edge
    graph_after = build_mock_topology()
    graph_after.remove_edge("internet", "sg-001")

    nodes_before = [{"id": n, "data": d} for n, d in graph_before.nodes(data=True)]
    edges_before = [{"source": u, "target": v, "data": d} for u, v, d in graph_before.edges(data=True)]
    snapshot_before = {"graph_data": {"nodes": nodes_before, "edges": edges_before}}

    nodes_after = [{"id": n, "data": d} for n, d in graph_after.nodes(data=True)]
    edges_after = [{"source": u, "target": v, "data": d} for u, v, d in graph_after.edges(data=True)]
    snapshot_after = {"graph_data": {"nodes": nodes_after, "edges": edges_after}}

    diff = GraphDiff().compare(snapshot_before, snapshot_after)

    assert diff["added_nodes"] == []
    assert diff["removed_nodes"] == []
    assert diff["added_edges"] == []
    # Verify the edge from internet to sg-001 was detected as removed
    assert len(diff["removed_edges"]) == 1
    assert "internet" in diff["removed_edges"][0]
    assert "sg-001" in diff["removed_edges"][0]
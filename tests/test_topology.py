"""
Unit tests for Cloud Topology Graph Engine.
Verifies graph node counts, edge relationships, and network topology structure.
"""

from src.topology.graph_engine import build_mock_topology


def test_topology_graph_node_count():
    """Verify that the mock graph contains exactly 6 nodes."""
    graph = build_mock_topology()
    assert graph.number_of_nodes() == 6

    expected_nodes = {
        "subnet-public",
        "subnet-private",
        "i-001",
        "sg-001",
        "db-001",
        "internet",
    }
    assert set(graph.nodes()) == expected_nodes


def test_topology_graph_edge_count():
    """Verify that the mock graph contains exactly 4 edges."""
    graph = build_mock_topology()
    assert graph.number_of_edges() == 4


def test_topology_graph_edge_relationships():
    """Verify the specific relationships and attributes on graph edges."""
    graph = build_mock_topology()

    # EC2 located in public subnet
    assert graph.has_edge("i-001", "subnet-public")
    assert graph["i-001"]["subnet-public"]["relationship"] == "located_in"

    # Security Group protects EC2
    assert graph.has_edge("sg-001", "i-001")
    assert graph["sg-001"]["i-001"]["relationship"] == "protects"

    # Database located in private subnet
    assert graph.has_edge("db-001", "subnet-private")
    assert graph["db-001"]["subnet-private"]["relationship"] == "located_in"

    # Public internet ingress to Security Group
    assert graph.has_edge("internet", "sg-001")
    edge_data = graph["internet"]["sg-001"]
    assert edge_data["relationship"] == "ingress"
    assert edge_data["protocol"] == "tcp"
    assert edge_data["port"] == 22
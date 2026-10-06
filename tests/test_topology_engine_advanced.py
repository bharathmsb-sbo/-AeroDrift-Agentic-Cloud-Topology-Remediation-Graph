"""
Advanced unit tests for topology engine module.
"""

import pytest
from aerodrift.topology_engine import TopologyEngine, ResourceType, ResourceNode


@pytest.mark.unit
class TestTopologyEngineAdvanced:
    """Advanced test cases for TopologyEngine class."""

    def test_resource_node_hash(self):
        """Test that ResourceNode is hashable."""
        node = ResourceNode(
            resource_id="test-123",
            resource_type=ResourceType.VPC,
            name="Test VPC",
            attributes={"cidr": "10.0.0.0/16"}
        )
        assert hash(node) is not None

    def test_add_resource(self):
        """Test adding a resource to the topology."""
        engine = TopologyEngine()
        node = ResourceNode(
            resource_id="test-123",
            resource_type=ResourceType.VPC,
            name="Test VPC",
            attributes={"cidr": "10.0.0.0/16"}
        )
        engine.add_resource(node)
        assert "test-123" in engine.resource_index
        assert engine.graph.number_of_nodes() == 2  # Including internet gateway

    def test_add_network_edge(self):
        """Test adding a network edge between resources."""
        engine = TopologyEngine()
        node1 = ResourceNode(
            resource_id="vpc-123",
            resource_type=ResourceType.VPC,
            name="Test VPC",
            attributes={"cidr": "10.0.0.0/16"}
        )
        node2 = ResourceNode(
            resource_id="subnet-456",
            resource_type=ResourceType.SUBNET,
            name="Test Subnet",
            attributes={"cidr": "10.0.1.0/24"}
        )
        engine.add_resource(node1)
        engine.add_resource(node2)
        engine.add_network_edge("vpc-123", "subnet-456", "contains")
        assert engine.graph.has_edge("vpc-123", "subnet-456")

    def test_get_resource_details(self):
        """Test getting resource details."""
        engine = TopologyEngine()
        node = ResourceNode(
            resource_id="test-123",
            resource_type=ResourceType.VPC,
            name="Test VPC",
            attributes={"cidr": "10.0.0.0/16"}
        )
        engine.add_resource(node)
        details = engine.get_resource_details("test-123")
        assert details is not None
        assert details.resource_id == "test-123"
        assert details.name == "Test VPC"

    def test_get_connected_resources(self):
        """Test getting connected resources."""
        engine = TopologyEngine()
        node1 = ResourceNode(
            resource_id="vpc-123",
            resource_type=ResourceType.VPC,
            name="Test VPC",
            attributes={"cidr": "10.0.0.0/16"}
        )
        node2 = ResourceNode(
            resource_id="subnet-456",
            resource_type=ResourceType.SUBNET,
            name="Test Subnet",
            attributes={"cidr": "10.0.1.0/24"}
        )
        engine.add_resource(node1)
        engine.add_resource(node2)
        engine.add_network_edge("vpc-123", "subnet-456", "contains")
        
        connected = engine.get_connected_resources("vpc-123", direction='out')
        assert "subnet-456" in connected

    def test_clear(self):
        """Test clearing the topology."""
        engine = TopologyEngine()
        node = ResourceNode(
            resource_id="test-123",
            resource_type=ResourceType.VPC,
            name="Test VPC",
            attributes={"cidr": "10.0.0.0/16"}
        )
        engine.add_resource(node)
        assert engine.graph.number_of_nodes() > 0
        
        engine.clear()
        assert engine.graph.number_of_nodes() == 0
        assert len(engine.resource_index) == 0

    def test_cache_statistics(self):
        """Test getting cache statistics."""
        engine = TopologyEngine()
        stats = engine.get_cache_statistics()
        assert 'cache_hits' in stats
        assert 'cache_misses' in stats
        assert 'hit_rate' in stats
        assert 'cache_size' in stats

    def test_performance_statistics(self):
        """Test getting performance statistics."""
        engine = TopologyEngine()
        stats = engine.get_performance_statistics()
        assert isinstance(stats, dict)

    def test_invalidate_cache(self):
        """Test cache invalidation."""
        engine = TopologyEngine()
        engine._path_cache["test_key"] = ["test_value"]
        engine.invalidate_cache()
        assert len(engine._path_cache) == 0

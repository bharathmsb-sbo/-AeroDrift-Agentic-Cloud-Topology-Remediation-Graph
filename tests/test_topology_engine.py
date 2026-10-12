"""Tests for cloud topology graph operations."""

from aerodrift.topology_engine.topology_engine import ResourceNode, ResourceType, TopologyEngine


def _add_resource(engine, resource_id, resource_type=ResourceType.EC2_INSTANCE):
    engine.add_resource(
        ResourceNode(
            resource_id=resource_id,
            resource_type=resource_type,
            name=resource_id,
            attributes={},
        )
    )


def test_adding_edge_invalidates_cached_missing_path():
    engine = TopologyEngine()
    _add_resource(engine, engine.internet_gateway_id, ResourceType.INTERNET)
    _add_resource(engine, "database", ResourceType.DATABASE)

    assert engine.find_path_from_internet("database") is None

    engine.add_network_edge(engine.internet_gateway_id, "database", "ingress")

    assert engine.find_path_from_internet("database") == [
        engine.internet_gateway_id,
        "database",
    ]


def test_adding_edge_invalidates_cached_shortest_path():
    engine = TopologyEngine()
    _add_resource(engine, engine.internet_gateway_id, ResourceType.INTERNET)
    _add_resource(engine, "subnet", ResourceType.SUBNET)
    _add_resource(engine, "database", ResourceType.DATABASE)
    engine.add_network_edge(engine.internet_gateway_id, "subnet", "contains")
    engine.add_network_edge("subnet", "database", "contains")

    assert engine.find_path_from_internet("database") == [
        engine.internet_gateway_id,
        "subnet",
        "database",
    ]

    engine.add_network_edge(engine.internet_gateway_id, "database", "ingress")

    assert engine.find_path_from_internet("database") == [
        engine.internet_gateway_id,
        "database",
    ]
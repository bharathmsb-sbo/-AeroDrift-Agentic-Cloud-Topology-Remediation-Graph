
from src.cloud_ingestion import CloudIngestion
from src.topology_builder import TopologyBuilder


def test_build_topology():
    ingestion = CloudIngestion()

    import asyncio
    resources = asyncio.run(
        ingestion.collect_mock_data()
    )

    builder = TopologyBuilder()
    topology = builder.build_topology(resources)

    assert "nodes" in topology
    assert "edges" in topology

    assert len(topology["nodes"]) > 0
    assert len(topology["edges"]) > 0


def test_subnet_vpc_relationship():
    ingestion = CloudIngestion()

    import asyncio
    resources = asyncio.run(
        ingestion.collect_mock_data()
    )

    builder = TopologyBuilder()
    topology = builder.build_topology(resources)

    edge = topology["edges"][0]

    assert edge["source"] == "vpc-001"
    assert edge["target"] == "subnet-001"
    assert edge["relationship"] == "contains"
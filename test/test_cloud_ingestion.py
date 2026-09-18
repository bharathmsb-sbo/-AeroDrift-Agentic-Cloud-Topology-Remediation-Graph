import asyncio

from src.cloud_ingestion import CloudIngestion


def test_mock_data():
    ingestion = CloudIngestion()

    data = asyncio.run(
        ingestion.collect_mock_data()
    )

    assert "vpcs" in data
    assert "subnets" in data
    assert "security_groups" in data
    assert "ec2_instances" in data


def test_vpc_data():
    ingestion = CloudIngestion()

    data = asyncio.run(
        ingestion.collect_mock_data()
    )

    assert len(data["vpcs"]) > 0
    assert data["vpcs"][0]["vpc_id"] == "vpc-001"
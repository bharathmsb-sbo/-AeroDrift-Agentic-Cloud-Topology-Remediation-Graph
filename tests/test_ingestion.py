"""
Unit tests for Mock AWS resource ingestion.
Verifies that all mock cloud resources are loaded with expected attributes.
"""

from src.ingestion.mock_aws import MockAWSProvider


def test_mock_aws_get_all_resources_keys():
    """Verify that get_all_resources returns all required resource categories."""
    provider = MockAWSProvider()
    resources = provider.get_all_resources()

    assert "ec2_instances" in resources
    assert "subnets" in resources
    assert "security_groups" in resources
    assert "databases" in resources


def test_mock_aws_ec2_instances():
    """Verify EC2 instance counts and attributes."""
    provider = MockAWSProvider()
    resources = provider.get_all_resources()
    ec2_list = resources["ec2_instances"]

    assert len(ec2_list) == 1
    ec2 = ec2_list[0]
    assert ec2.instance_id == "i-001"
    assert ec2.name == "web-server"
    assert ec2.subnet_id == "subnet-public"
    assert ec2.security_group_id == "sg-001"


def test_mock_aws_subnets():
    """Verify Subnet counts and public/private separation."""
    provider = MockAWSProvider()
    resources = provider.get_all_resources()
    subnets = resources["subnets"]

    assert len(subnets) == 2
    subnet_types = {s.subnet_type for s in subnets}
    assert "public" in subnet_types
    assert "private" in subnet_types


def test_mock_aws_security_groups():
    """Verify Security Group rules, specifically checking for the port 22 rule."""
    provider = MockAWSProvider()
    resources = provider.get_all_resources()
    security_groups = resources["security_groups"]

    assert len(security_groups) == 1
    sg = security_groups[0]
    assert sg.group_id == "sg-001"
    assert sg.name == "web-security-group"

    # Check the ingress rule that represents potential drift
    assert len(sg.ingress_rules) == 1
    rule = sg.ingress_rules[0]
    assert rule["protocol"] == "tcp"
    assert rule["port"] == 22
    assert rule["source"] == "0.0.0.0/0"


def test_mock_aws_databases():
    """Verify Database instance counts and subnet placement."""
    provider = MockAWSProvider()
    resources = provider.get_all_resources()
    databases = resources["databases"]

    assert len(databases) == 1
    db = databases[0]
    assert db.database_id == "db-001"
    assert db.name == "production-db"
    assert db.subnet_id == "subnet-private"
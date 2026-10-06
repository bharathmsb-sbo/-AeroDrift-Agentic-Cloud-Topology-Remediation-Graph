"""
Unit tests for cloud ingestion module.
"""

import pytest
import asyncio
from aerodrift.cloud_ingestion import AWSIngestion, MockAWSData
from aerodrift.cloud_ingestion.aws_ingestion import VPC, Subnet, SecurityGroup, EC2Instance


@pytest.mark.unit
class TestMockAWSData:
    """Test cases for MockAWSData class."""

    def test_initialization(self):
        """Test that MockAWSData initializes correctly."""
        mock_data = MockAWSData()
        assert mock_data._vpcs is not None
        assert mock_data._subnets is not None
        assert mock_data._security_groups is not None
        assert mock_data._instances is not None

    def test_get_vpcs(self):
        """Test getting mock VPCs."""
        mock_data = MockAWSData()
        vpcs = mock_data.get_vpcs()
        assert len(vpcs) == 2
        assert all(isinstance(vpc, VPC) for vpc in vpcs)

    def test_get_subnets(self):
        """Test getting mock subnets."""
        mock_data = MockAWSData()
        subnets = mock_data.get_subnets()
        assert len(subnets) == 3
        assert all(isinstance(subnet, Subnet) for subnet in subnets)

    def test_get_security_groups(self):
        """Test getting mock security groups."""
        mock_data = MockAWSData()
        sgs = mock_data.get_security_groups()
        assert len(sgs) == 4
        assert all(isinstance(sg, SecurityGroup) for sg in sgs)

    def test_get_ec2_instances(self):
        """Test getting mock EC2 instances."""
        mock_data = MockAWSData()
        instances = mock_data.get_ec2_instances()
        assert len(instances) == 4
        assert all(isinstance(instance, EC2Instance) for instance in instances)

    def test_add_vulnerable_rule(self):
        """Test adding a vulnerable rule to a security group."""
        mock_data = MockAWSData()
        initial_count = len(mock_data._security_groups[1].ingress_rules)
        mock_data.add_vulnerable_rule("sg-web-server", cidr="0.0.0.0/0", port=3389)
        assert len(mock_data._security_groups[1].ingress_rules) == initial_count + 1

    def test_remove_vulnerable_rule(self):
        """Test removing a vulnerable rule from a security group."""
        mock_data = MockAWSData()
        mock_data.add_vulnerable_rule("sg-web-server", cidr="0.0.0.0/0", port=3389)
        initial_count = len(mock_data._security_groups[1].ingress_rules)
        mock_data.remove_vulnerable_rule("sg-web-server", cidr="0.0.0.0/0", port=3389)
        assert len(mock_data._security_groups[1].ingress_rules) == initial_count - 1


@pytest.mark.unit
@pytest.mark.asyncio
class TestAWSIngestion:
    """Test cases for AWSIngestion class."""

    async def test_initialization_with_mock(self):
        """Test that AWSIngestion initializes with mock mode."""
        ingestion = AWSIngestion(use_mock=True)
        assert ingestion.use_mock is True
        assert ingestion.region == "us-east-1"

    async def test_collect_vpcs_with_mock(self):
        """Test collecting VPCs with mock data."""
        ingestion = AWSIngestion(use_mock=True)
        vpcs = await ingestion.collect_vpcs()
        assert len(vpcs) == 2
        assert all(isinstance(vpc, VPC) for vpc in vpcs)

    async def test_collect_subnets_with_mock(self):
        """Test collecting subnets with mock data."""
        ingestion = AWSIngestion(use_mock=True)
        subnets = await ingestion.collect_subnets()
        assert len(subnets) == 3
        assert all(isinstance(subnet, Subnet) for subnet in subnets)

    async def test_collect_security_groups_with_mock(self):
        """Test collecting security groups with mock data."""
        ingestion = AWSIngestion(use_mock=True)
        sgs = await ingestion.collect_security_groups()
        assert len(sgs) == 4
        assert all(isinstance(sg, SecurityGroup) for sg in sgs)

    async def test_collect_ec2_instances_with_mock(self):
        """Test collecting EC2 instances with mock data."""
        ingestion = AWSIngestion(use_mock=True)
        instances = await ingestion.collect_ec2_instances()
        assert len(instances) == 4
        assert all(isinstance(instance, EC2Instance) for instance in instances)

    async def test_collect_all_resources(self):
        """Test collecting all resources concurrently."""
        ingestion = AWSIngestion(use_mock=True)
        data = await ingestion.collect_all_resources()
        assert 'timestamp' in data
        assert 'region' in data
        assert 'vpcs' in data
        assert 'subnets' in data
        assert 'security_groups' in data
        assert 'instances' in data
        assert len(data['vpcs']) == 2
        assert len(data['subnets']) == 3
        assert len(data['security_groups']) == 4
        assert len(data['instances']) == 4

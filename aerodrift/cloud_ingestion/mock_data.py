"""
Mock AWS Data: Simulated AWS resources for testing and development.
"""

from typing import List, Dict, Any
from .aws_ingestion import VPC, Subnet, SecurityGroup, EC2Instance


class MockAWSData:
    """
    Provides mock AWS data for testing without real AWS credentials.
    Simulates a realistic cloud environment with security vulnerabilities.
    """
    
    def __init__(self):
        """Initialize mock AWS data with realistic test scenarios."""
        self._vpcs = self._create_vpcs()
        self._subnets = self._create_subnets()
        self._security_groups = self._create_security_groups()
        self._instances = self._create_instances()
    
    def _create_vpcs(self) -> List[VPC]:
        """Create mock VPCs."""
        return [
            VPC(
                vpc_id="vpc-12345678",
                cidr_block="10.0.0.0/16",
                state="available",
                tags={"Name": "Production-VPC", "Environment": "production"}
            ),
            VPC(
                vpc_id="vpc-87654321",
                cidr_block="172.16.0.0/16",
                state="available",
                tags={"Name": "Development-VPC", "Environment": "development"}
            )
        ]
    
    def _create_subnets(self) -> List[Subnet]:
        """Create mock subnets."""
        return [
            Subnet(
                subnet_id="subnet-11111111",
                vpc_id="vpc-12345678",
                cidr_block="10.0.1.0/24",
                availability_zone="us-east-1a",
                state="available"
            ),
            Subnet(
                subnet_id="subnet-22222222",
                vpc_id="vpc-12345678",
                cidr_block="10.0.2.0/24",
                availability_zone="us-east-1b",
                state="available"
            ),
            Subnet(
                subnet_id="subnet-33333333",
                vpc_id="vpc-87654321",
                cidr_block="172.16.1.0/24",
                availability_zone="us-east-1a",
                state="available"
            )
        ]
    
    def _create_security_groups(self) -> List[SecurityGroup]:
        """Create mock security groups with intentional vulnerabilities."""
        return [
            # Secure database security group
            SecurityGroup(
                group_id="sg-secure-db",
                group_name="secure-database-sg",
                description="Security group for production database",
                vpc_id="vpc-12345678",
                ingress_rules=[
                    {
                        'protocol': 'tcp',
                        'from_port': 3306,
                        'to_port': 3306,
                        'cidr': '10.0.1.0/24',
                        'description': 'MySQL from app subnet'
                    }
                ],
                egress_rules=[
                    {
                        'protocol': '-1',
                        'from_port': None,
                        'to_port': None,
                        'cidr': '0.0.0.0/0',
                        'description': 'All outbound traffic'
                    }
                ]
            ),
            # VULNERABLE: Web server with SSH open to internet
            SecurityGroup(
                group_id="sg-web-server",
                group_name="web-server-sg",
                description="Security group for web servers",
                vpc_id="vpc-12345678",
                ingress_rules=[
                    {
                        'protocol': 'tcp',
                        'from_port': 80,
                        'to_port': 80,
                        'cidr': '0.0.0.0/0',
                        'description': 'HTTP from internet'
                    },
                    {
                        'protocol': 'tcp',
                        'from_port': 443,
                        'to_port': 443,
                        'cidr': '0.0.0.0/0',
                        'description': 'HTTPS from internet'
                    },
                    {
                        'protocol': 'tcp',
                        'from_port': 22,
                        'to_port': 22,
                        'cidr': '0.0.0.0/0',  # VULNERABLE: SSH open to world
                        'description': 'SSH access - TEMPORARY'
                    }
                ],
                egress_rules=[
                    {
                        'protocol': '-1',
                        'from_port': None,
                        'to_port': None,
                        'cidr': '0.0.0.0/0',
                        'description': 'All outbound traffic'
                    }
                ]
            ),
            # Application tier security group
            SecurityGroup(
                group_id="sg-app-tier",
                group_name="application-tier-sg",
                description="Security group for application servers",
                vpc_id="vpc-12345678",
                ingress_rules=[
                    {
                        'protocol': 'tcp',
                        'from_port': 8080,
                        'to_port': 8080,
                        'cidr': '10.0.1.0/24',
                        'description': 'App from load balancer'
                    }
                ],
                egress_rules=[
                    {
                        'protocol': '-1',
                        'from_port': None,
                        'to_port': None,
                        'cidr': '0.0.0.0/0',
                        'description': 'All outbound traffic'
                    }
                ]
            ),
            # Development security group (permissive)
            SecurityGroup(
                group_id="sg-dev-sg",
                group_name="development-sg",
                description="Permissive security group for development",
                vpc_id="vpc-87654321",
                ingress_rules=[
                    {
                        'protocol': '-1',
                        'from_port': None,
                        'to_port': None,
                        'cidr': '172.16.1.0/24',
                        'description': 'All traffic from dev subnet'
                    }
                ],
                egress_rules=[
                    {
                        'protocol': '-1',
                        'from_port': None,
                        'to_port': None,
                        'cidr': '0.0.0.0/0',
                        'description': 'All outbound traffic'
                    }
                ]
            )
        ]
    
    def _create_instances(self) -> List[EC2Instance]:
        """Create mock EC2 instances."""
        return [
            # Production database instance
            EC2Instance(
                instance_id="i-db-prod-001",
                instance_type="db.t3.large",
                state="running",
                vpc_id="vpc-12345678",
                subnet_id="subnet-11111111",
                private_ip="10.0.1.50",
                public_ip=None,
                security_groups=["sg-secure-db"]
            ),
            # Web server instance
            EC2Instance(
                instance_id="i-web-prod-001",
                instance_type="t3.medium",
                state="running",
                vpc_id="vpc-12345678",
                subnet_id="subnet-11111111",
                private_ip="10.0.1.10",
                public_ip="54.123.45.67",
                security_groups=["sg-web-server"]
            ),
            # Application server instance
            EC2Instance(
                instance_id="i-app-prod-001",
                instance_type="t3.large",
                state="running",
                vpc_id="vpc-12345678",
                subnet_id="subnet-22222222",
                private_ip="10.0.2.20",
                public_ip=None,
                security_groups=["sg-app-tier", "sg-web-server"]
            ),
            # Development instance
            EC2Instance(
                instance_id="i-dev-001",
                instance_type="t3.micro",
                state="running",
                vpc_id="vpc-87654321",
                subnet_id="subnet-33333333",
                private_ip="172.16.1.10",
                public_ip=None,
                security_groups=["sg-dev-sg"]
            )
        ]
    
    def get_vpcs(self) -> List[VPC]:
        """Get mock VPCs."""
        return self._vpcs
    
    def get_subnets(self) -> List[Subnet]:
        """Get mock subnets."""
        return self._subnets
    
    def get_security_groups(self) -> List[SecurityGroup]:
        """Get mock security groups."""
        return self._security_groups
    
    def get_ec2_instances(self) -> List[EC2Instance]:
        """Get mock EC2 instances."""
        return self._instances
    
    def add_vulnerable_rule(self, group_id: str, cidr: str = "0.0.0.0/0", port: int = 22):
        """
        Add a vulnerable ingress rule to a security group for testing.
        
        Args:
            group_id: Security group ID to modify
            cidr: CIDR block to allow (default: 0.0.0.0/0)
            port: Port to open (default: 22 for SSH)
        """
        for sg in self._security_groups:
            if sg.group_id == group_id:
                sg.ingress_rules.append({
                    'protocol': 'tcp',
                    'from_port': port,
                    'to_port': port,
                    'cidr': cidr,
                    'description': 'VULNERABLE: Accidentally opened to internet'
                })
                print(f"Added vulnerable rule to {group_id}: {cidr}:{port}")
                return
        print(f"Security group {group_id} not found")
    
    def remove_vulnerable_rule(self, group_id: str, cidr: str = "0.0.0.0/0", port: int = 22):
        """
        Remove a vulnerable ingress rule from a security group.
        
        Args:
            group_id: Security group ID to modify
            cidr: CIDR block to remove
            port: Port to close
        """
        for sg in self._security_groups:
            if sg.group_id == group_id:
                original_count = len(sg.ingress_rules)
                sg.ingress_rules = [
                    rule for rule in sg.ingress_rules
                    if not (rule.get('cidr') == cidr and rule.get('from_port') == port)
                ]
                removed = original_count - len(sg.ingress_rules)
                print(f"Removed {removed} vulnerable rule(s) from {group_id}")
                return
        print(f"Security group {group_id} not found")

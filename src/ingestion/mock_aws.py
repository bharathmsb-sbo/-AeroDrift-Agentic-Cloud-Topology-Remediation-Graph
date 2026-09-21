from dataclasses import dataclass, field
from typing import Any


@dataclass
class EC2Instance:
    instance_id: str
    name: str
    subnet_id: str


@dataclass
class Subnet:
    subnet_id: str
    name: str
    subnet_type: str


@dataclass
class SecurityGroup:
    group_id: str
    name: str
    ingress_rules: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Database:
    database_id: str
    name: str
    subnet_id: str


class MockAWSProvider:
    """
    Provides simulated AWS resource data for AeroDrift development.

    This allows us to test cloud ingestion and topology generation
    without connecting to a real AWS account.
    """

    def __init__(self) -> None:
        self.ec2_instances = [
            EC2Instance(
                instance_id="i-001",
                name="web-server",
                subnet_id="subnet-public",
            )
        ]

        self.subnets = [
            Subnet(
                subnet_id="subnet-public",
                name="public-subnet",
                subnet_type="public",
            ),
            Subnet(
                subnet_id="subnet-private",
                name="private-subnet",
                subnet_type="private",
            ),
        ]

        self.security_groups = [
            SecurityGroup(
                group_id="sg-001",
                name="web-security-group",
                ingress_rules=[
                    {
                        "protocol": "tcp",
                        "port": 22,
                        "source": "0.0.0.0/0",
                    }
                ],
            )
        ]

        self.databases = [
            Database(
                database_id="db-001",
                name="production-db",
                subnet_id="subnet-private",
            )
        ]

    def get_all_resources(self) -> dict[str, list[Any]]:
        """Return all simulated AWS resources."""

        return {
            "ec2_instances": self.ec2_instances,
            "subnets": self.subnets,
            "security_groups": self.security_groups,
            "databases": self.databases,
        }
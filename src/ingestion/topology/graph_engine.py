import networkx as nx

from src.ingestion.mock_aws import MockAWSProvider


class CloudTopology:
    """
    Builds a directed graph representing relationships
    between simulated AWS resources.
    """

    def __init__(self, resources: dict) -> None:
        self.resources = resources
        self.graph = nx.DiGraph()

    def build(self) -> nx.DiGraph:
        """Build the cloud topology graph."""

        self._add_subnets()
        self._add_instances()
        self._add_databases()
        self._add_security_groups()

        return self.graph

    def _add_subnets(self) -> None:
        """Add subnet resources to the graph."""

        for subnet in self.resources["subnets"]:
            self.graph.add_node(
                subnet.subnet_id,
                resource_type="subnet",
                name=subnet.name,
                subnet_type=subnet.subnet_type,
            )

    def _add_instances(self) -> None:
        """Add EC2 instances and connect them to their subnets."""

        for instance in self.resources["ec2_instances"]:
            self.graph.add_node(
                instance.instance_id,
                resource_type="ec2",
                name=instance.name,
            )

            self.graph.add_edge(
                instance.instance_id,
                instance.subnet_id,
                relationship="located_in",
            )

    def _add_databases(self) -> None:
        """Add databases and connect them to their subnets."""

        for database in self.resources["databases"]:
            self.graph.add_node(
                database.database_id,
                resource_type="database",
                name=database.name,
            )

            self.graph.add_edge(
                database.database_id,
                database.subnet_id,
                relationship="located_in",
            )

    def _add_security_groups(self) -> None:
        """Add security groups and their ingress relationships."""

        for security_group in self.resources["security_groups"]:
            self.graph.add_node(
                security_group.group_id,
                resource_type="security_group",
                name=security_group.name,
            )

            for rule in security_group.ingress_rules:
                source = rule["source"]

                if source == "0.0.0.0/0":
                    self.graph.add_node(
                        "internet",
                        resource_type="internet",
                        name="Internet",
                    )

                    self.graph.add_edge(
                        "internet",
                        security_group.group_id,
                        relationship="ingress",
                        protocol=rule["protocol"],
                        port=rule["port"],
                    )


def build_mock_topology() -> nx.DiGraph:
    """Create and return the topology from mock AWS resources."""

    provider = MockAWSProvider()
    resources = provider.get_all_resources()

    topology = CloudTopology(resources)

    return topology.build()
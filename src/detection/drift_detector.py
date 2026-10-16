import networkx as nx


class DriftDetector:
    """
    Detects security-related drift in the cloud topology.
    """

    def __init__(self, graph: nx.DiGraph) -> None:
        self.graph = graph

    def detect_public_ingress(self) -> list[dict]:
        """
        Detect security groups that allow public internet access.
        """

        findings = []

        for source, target, data in self.graph.edges(data=True):
            if (
                source == "internet"
                and data.get("relationship") == "ingress"
            ):
                findings.append(
                    {
                        "security_group": target,
                        "protocol": data.get("protocol"),
                        "port": data.get("port"),
                        "source": "0.0.0.0/0",
                    }
                )

        return findings


def detect_drift(graph: nx.DiGraph) -> list[dict]:
    """
    Run drift detection against the cloud topology.
    """

    detector = DriftDetector(graph)

    return detector.detect_public_ingress()
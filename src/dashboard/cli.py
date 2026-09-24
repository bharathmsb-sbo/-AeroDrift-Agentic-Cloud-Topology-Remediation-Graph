from datetime import datetime

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.rule import Rule
from rich.columns import Columns

from src.detection.drift_detector import detect_drift
from src.topology.graph_engine import build_mock_topology


console = Console()


class AeroDriftDashboard:
    """
    Rich CLI dashboard for AeroDrift.

    This dashboard:
    - Builds the current cloud topology
    - Detects cloud security drift
    - Displays detected findings
    - Shows a summary of the current cloud state
    """

    def __init__(self) -> None:
        """Initialize the dashboard."""

        self.graph = None
        self.findings: list[dict] = []

    def load_cloud_topology(self) -> None:
        """
        Build the current cloud topology
        from the mock AWS provider.
        """

        self.graph = build_mock_topology()

    def detect_cloud_drift(self) -> None:
        """
        Run the drift detector against
        the current cloud topology.
        """

        if self.graph is None:
            raise RuntimeError(
                "Cloud topology must be loaded before drift detection."
            )

        self.findings = detect_drift(self.graph)

    def display_header(self) -> None:
        """Display the AeroDrift dashboard header."""

        title = Text(
            "AeroDrift",
            style="bold cyan",
        )

        subtitle = Text(
            "Agentic Cloud Topology & Remediation Graph",
            style="white",
        )

        console.print(
            Panel(
                Text.assemble(
                    title,
                    "\n",
                    subtitle,
                ),
                title="Cloud Operations Dashboard",
                border_style="cyan",
                expand=False,
            )
        )

    def display_system_status(self) -> None:
        """Display the current system status."""

        topology_status = (
            "Loaded" if self.graph is not None else "Not Loaded"
        )

        drift_status = (
            "Drift Detected"
            if self.findings
            else "No Drift"
        )

        topology_text = Text(
            f"Topology: {topology_status}",
            style="green" if self.graph else "red",
        )

        drift_text = Text(
            f"Security: {drift_status}",
            style="red" if self.findings else "green",
        )

        timestamp = datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        time_text = Text(
            f"Checked: {timestamp}",
            style="yellow",
        )

        console.print(
            Columns(
                [
                    Panel(
                        topology_text,
                        title="Topology Status",
                        border_style="green",
                    ),
                    Panel(
                        drift_text,
                        title="Security Status",
                        border_style=(
                            "red" if self.findings else "green"
                        ),
                    ),
                    Panel(
                        time_text,
                        title="Last Scan",
                        border_style="yellow",
                    ),
                ]
            )
        )

    def display_resource_summary(self) -> None:
        """Display the number of resources in the topology."""

        if self.graph is None:
            return

        resource_counts: dict[str, int] = {}

        for _, data in self.graph.nodes(data=True):
            resource_type = data.get(
                "resource_type",
                "unknown",
            )

            resource_counts[resource_type] = (
                resource_counts.get(resource_type, 0) + 1
            )

        table = Table(
            title="Cloud Resource Summary",
            show_header=True,
        )

        table.add_column(
            "Resource Type",
            style="cyan",
        )

        table.add_column(
            "Count",
            justify="center",
            style="yellow",
        )

        for resource_type, count in sorted(
            resource_counts.items()
        ):
            table.add_row(
                resource_type.replace("_", " ").title(),
                str(count),
            )

        console.print(table)

    def display_drift_findings(self) -> None:
        """Display all detected drift findings."""

        console.print(
            Rule(
                "Security Drift Findings",
                style="red",
            )
        )

        if not self.findings:
            console.print(
                Panel(
                    "[bold green]No security drift detected.[/bold green]",
                    border_style="green",
                )
            )
            return

        table = Table(
            title="Detected Security Drift",
            show_header=True,
        )

        table.add_column(
            "Security Group",
            style="cyan",
        )

        table.add_column(
            "Protocol",
            style="yellow",
        )

        table.add_column(
            "Port",
            justify="center",
        )

        table.add_column(
            "Source",
            style="red",
        )

        table.add_column(
            "Status",
            style="bold red",
        )

        for finding in self.findings:
            table.add_row(
                finding["security_group"],
                finding["protocol"],
                str(finding["port"]),
                finding["source"],
                "DRIFT DETECTED",
            )

        console.print(table)

    def display_remediation_summary(self) -> None:
        """
        Display what AeroDrift can do with the
        detected drift findings.
        """

        console.print(
            Rule(
                "Remediation Status",
                style="yellow",
            )
        )

        if not self.findings:
            console.print(
                Panel(
                    "No remediation is required.",
                    border_style="green",
                )
            )
            return

        remediation_table = Table(
            title="Required Remediation",
            show_header=True,
        )

        remediation_table.add_column(
            "Security Group",
            style="cyan",
        )

        remediation_table.add_column(
            "Issue",
            style="red",
        )

        remediation_table.add_column(
            "Action",
            style="yellow",
        )

        for finding in self.findings:
            issue = (
                f"Public ingress on "
                f"{finding['protocol']} "
                f"port {finding['port']}"
            )

            action = (
                "Revoke unwanted ingress rule"
            )

            remediation_table.add_row(
                finding["security_group"],
                issue,
                action,
            )

        console.print(remediation_table)

    def display_graph_summary(self) -> None:
        """Display basic topology graph information."""

        if self.graph is None:
            return

        node_count = self.graph.number_of_nodes()
        edge_count = self.graph.number_of_edges()

        console.print(
            Panel(
                Text.assemble(
                    ("Nodes: ", "bold"),
                    (str(node_count), "cyan"),
                    ("\nEdges: ", "bold"),
                    (str(edge_count), "cyan"),
                ),
                title="Topology Graph",
                border_style="blue",
                expand=False,
            )
        )

    def run(self) -> None:
        """Run the complete AeroDrift dashboard."""

        console.clear()

        self.display_header()

        console.print()

        self.load_cloud_topology()

        self.detect_cloud_drift()

        self.display_system_status()

        console.print()

        self.display_resource_summary()

        console.print()

        self.display_graph_summary()

        console.print()

        self.display_drift_findings()

        console.print()

        self.display_remediation_summary()


def run_dashboard() -> None:
    """
    Create and run the AeroDrift dashboard.
    """

    dashboard = AeroDriftDashboard()

    dashboard.run()


if __name__ == "__main__":
    run_dashboard()
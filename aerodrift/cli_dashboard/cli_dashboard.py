"""
CLI Dashboard: Rich-based terminal UI for cloud topology visualization and drift reporting.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.syntax import Syntax
from rich.box import DOUBLE, ROUNDED

logger = logging.getLogger(__name__)


class CLIDashboard:
    """
    Beautiful CLI reporting tool using Rich library.
    
    Features:
    - Interactive text tree for cloud topology
    - Color-coded drift events
    - Real-time monitoring dashboard
    - Detailed incident reports
    """
    
    def __init__(self):
        """Initialize the CLI dashboard."""
        self.console = Console()
        self.current_layout = None
    
    def print_header(self, title: str = "AeroDrift - Agentic Cloud Healer"):
        """
        Print the application header.
        
        Args:
            title: Header title
        """
        header = Panel(
            Text(title, style="bold blue", justify="center"),
            box=DOUBLE,
            padding=(1, 2),
            border_style="blue"
        )
        self.console.print(header)
        self.console.print()
    
    def display_topology_tree(self, topology_engine, title: str = "Cloud Topology"):
        """
        Display the cloud topology as an interactive text tree.
        
        Args:
            topology_engine: TopologyEngine instance
            title: Tree title
        """
        tree = Tree(f"[bold blue]{title}[/bold blue]")
        
        # Add Internet node
        internet_id = topology_engine.internet_gateway_id
        internet_node = topology_engine.get_resource_details(internet_id)
        if internet_node:
            internet_branch = tree.add(f"[red]{internet_node.name}[/red]")
            self._add_connected_resources(topology_engine, internet_branch, internet_id)
        
        # Add VPCs
        vpcs = [
            resource for resource in topology_engine.resource_index.values()
            if resource.resource_type.value == 'vpc'
        ]
        
        for vpc in sorted(vpcs, key=lambda x: x.name):
            vpc_branch = tree.add(f"[cyan]{vpc.name}[/cyan] ({vpc.attributes.get('cidr_block', '')})")
            self._add_connected_resources(topology_engine, vpc_branch, vpc.resource_id)
        
        self.console.print(tree)
        self.console.print()
    
    def _add_connected_resources(self, topology_engine, branch, resource_id):
        """
        Recursively add connected resources to the tree branch.
        
        Args:
            topology_engine: TopologyEngine instance
            branch: Tree branch to add to
            resource_id: Resource ID to expand
        """
        connected = topology_engine.get_connected_resources(resource_id, direction='out')
        
        for connected_id in connected:
            resource = topology_engine.get_resource_details(connected_id)
            if not resource or resource.attributes.get('is_cidr'):
                continue
            
            # Choose icon and color based on resource type
            icon, color = self._get_resource_icon_and_color(resource.resource_type.value)
            
            # Check if resource is exposed (has path from internet)
            is_exposed = topology_engine.find_path_from_internet(connected_id) is not None
            
            if is_exposed:
                resource_branch = branch.add(f"[bold red]{icon} {resource.name}[/bold red]")
            else:
                resource_branch = branch.add(f"[{color}]{icon} {resource.name}[/{color}]")
            
            # Recursively add children (limit depth to prevent infinite loops)
            if resource.resource_type.value not in ['ec2_instance', 'database']:
                self._add_connected_resources(topology_engine, resource_branch, connected_id)
    
    def _get_resource_icon_and_color(self, resource_type: str) -> tuple:
        """
        Get icon and color for a resource type.
        
        Args:
            resource_type: Type of resource
            
        Returns:
            Tuple of (icon, color)
        """
        icons = {
            'vpc': ('[VPC]', 'cyan'),
            'subnet': ('[SUBNET]', 'green'),
            'security_group': ('[SG]', 'yellow'),
            'ec2_instance': ('[EC2]', 'blue'),
            'database': ('[DB]', 'magenta'),
            'internet': ('[INET]', 'red')
        }
        return icons.get(resource_type, ('[RES]', 'white'))
    
    def display_drift_events(self, drift_events: List[Any], title: str = "Detected Drift Events"):
        """
        Display detected drift events in a table.
        
        Args:
            drift_events: List of DriftEvent objects
            title: Table title
        """
        if not drift_events:
            self.console.print("[green][+] No drift events detected[/green]")
            self.console.print()
            return
        
        table = Table(title=title, show_header=True, header_style="bold magenta")
        table.add_column("Event ID", style="dim", width=12)
        table.add_column("Severity", style="bold", width=10)
        table.add_column("Type", width=20)
        table.add_column("Resource", width=20)
        table.add_column("Description", width=40)
        table.add_column("Time", width=16)
        
        for event in drift_events:
            severity_style = {
                'critical': 'red',
                'high': 'orange',
                'medium': 'yellow',
                'low': 'blue',
                'info': 'dim'
            }.get(event.severity.value, 'white')
            
            table.add_row(
                event.event_id,
                f"[{severity_style}]{event.severity.value.upper()}[/{severity_style}]",
                event.drift_type.value,
                event.resource_id,
                event.description,
                event.timestamp.strftime("%H:%M:%S")
            )
        
        self.console.print(table)
        self.console.print()
    
    def display_exposed_databases(self, exposed_dbs: List[Dict[str, Any]]):
        """
        Display exposed databases with their exposure paths.
        
        Args:
            exposed_dbs: List of exposed database information
        """
        if not exposed_dbs:
            self.console.print("[green][+] No exposed databases found[/green]")
            self.console.print()
            return
        
        self.console.print("[bold red][!] EXPOSED DATABASES DETECTED[/bold red]")
        self.console.print()
        
        for db in exposed_dbs:
            panel = Panel(
                f"[bold red]Database:[/bold red] {db['name']}\n"
                f"[bold red]Path from Internet:[/bold red]\n{db['path_description']}",
                title=f"[red]{db['resource_id']}[/red]",
                border_style="red"
            )
            self.console.print(panel)
            self.console.print()
    
    def display_graph_statistics(self, stats: Dict[str, Any]):
        """
        Display topology graph statistics.
        
        Args:
            stats: Statistics dictionary
        """
        table = Table(title="Topology Statistics", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Nodes", str(stats['total_nodes']))
        table.add_row("Total Edges", str(stats['total_edges']))
        table.add_row("Graph Connected", "Yes" if stats['is_connected'] else "No")
        table.add_row("Exposed Databases", f"[red]{stats['exposed_databases']}[/red]" if stats['exposed_databases'] > 0 else str(stats['exposed_databases']))
        
        for resource_type, count in stats['resource_type_counts'].items():
            table.add_row(f"{resource_type.title()}s", str(count))
        
        self.console.print(table)
        self.console.print()
    
    def display_remediation_code(self, code: str, title: str = "Generated Remediation Code"):
        """
        Display generated remediation code with syntax highlighting.
        
        Args:
            code: Python code to display
            title: Code block title
        """
        syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
        panel = Panel(syntax, title=title, border_style="green")
        self.console.print(panel)
        self.console.print()
    
    def display_incident_report(self, drift_events: List[Any], topology_stats: Dict[str, Any]):
        """
        Display a comprehensive incident report.
        
        Args:
            drift_events: List of drift events
            topology_stats: Topology statistics
        """
        self.print_header("AeroDrift Incident Report")
        
        # Summary
        critical_count = len([e for e in drift_events if e.severity.value == 'critical'])
        high_count = len([e for e in drift_events if e.severity.value == 'high'])
        
        summary = f"""
[bold]Incident Summary[/bold]
Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}
Critical Events: [red]{critical_count}[/red]
High Severity Events: [orange]{high_count}[/orange]
Total Events: {len(drift_events)}
"""
        self.console.print(Panel(summary, title="Summary", border_style="yellow"))
        self.console.print()
        
        # Topology Stats
        self.display_graph_statistics(topology_stats)
        
        # Drift Events
        self.display_drift_events(drift_events)
        
        # Footer
        footer = Panel(
            "[dim]Generated by AeroDrift - Agentic Cloud Healer[/dim]",
            box=ROUNDED,
            padding=(0, 2)
        )
        self.console.print(footer)
    
    def display_live_monitoring(self, update_callback, refresh_rate: float = 1.0):
        """
        Display a live monitoring dashboard.
        
        Args:
            update_callback: Function that returns the layout content
            refresh_rate: Refresh rate in seconds
        """
        try:
            with Live(update_callback(), refresh_per_second=1/refresh_rate) as live:
                while True:
                    live.update(update_callback())
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Monitoring stopped by user[/yellow]")
    
    def create_monitoring_layout(self, topology_engine, drift_events: List[Any]) -> Layout:
        """
        Create a layout for live monitoring.
        
        Args:
            topology_engine: TopologyEngine instance
            drift_events: List of drift events
            
        Returns:
            Rich Layout object
        """
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="stats", size=8),
            Layout(name="events", size=15),
            Layout(name="footer", size=3)
        )
        
        # Header
        layout["header"].update(
            Panel(
                Text("AeroDrift Live Monitoring", style="bold blue", justify="center"),
                box=DOUBLE
            )
        )
        
        # Statistics
        stats = topology_engine.get_graph_statistics()
        stats_text = f"""
Nodes: {stats['total_nodes']} | Edges: {stats['total_edges']}
Exposed DBs: [red]{stats['exposed_databases']}[/red]
Events: {len(drift_events)}
Last Update: {datetime.utcnow().strftime('%H:%M:%S')}
"""
        layout["stats"].update(Panel(stats_text, title="Statistics", border_style="cyan"))
        
        # Events
        if drift_events:
            recent_events = drift_events[-5:]  # Show last 5 events
            events_text = "\n".join([
                f"[{event.severity.value}] {event.description}"
                for event in recent_events
            ])
        else:
            events_text = "[green]No recent events[/green]"
        
        layout["events"].update(Panel(events_text, title="Recent Events", border_style="yellow"))
        
        # Footer
        layout["footer"].update(
            Panel(
                Text("Press Ctrl+C to exit", style="dim", justify="center"),
                box=ROUNDED
            )
        )
        
        return layout
    
    def create_progress(self, task_name: str, total: int = 100):
        """
        Create a progress bar for long-running operations.
        
        Args:
            task_name: Name of the task
            total: Total items to process
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console
        )
        task = progress.add_task(task_name, total=total)
        return progress, task
    
    def print_success(self, message: str):
        """Print a success message."""
        self.console.print(f"[green][+] {message}[/green]")
    
    def print_error(self, message: str):
        """Print an error message."""
        self.console.print(f"[red][-] {message}[/red]")
    
    def print_warning(self, message: str):
        """Print a warning message."""
        self.console.print(f"[yellow][!] {message}[/yellow]")
    
    def print_info(self, message: str):
        """Print an info message."""
        self.console.print(f"[blue][i] {message}[/blue]")

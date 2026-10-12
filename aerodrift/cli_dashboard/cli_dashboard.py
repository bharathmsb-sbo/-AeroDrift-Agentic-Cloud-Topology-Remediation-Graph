"""
CLI Dashboard: Enhanced Rich-based terminal UI for cloud topology visualization and drift reporting.
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
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.syntax import Syntax
from rich.box import DOUBLE, ROUNDED, HEAVY, SIMPLE
from rich.columns import Columns
from rich.align import Align

from rich.prompt import Prompt

logger = logging.getLogger(__name__)


class CLIDashboard:
    """
    Enhanced Beautiful CLI reporting tool using Rich library.
    
    Features:
    - Interactive text tree for cloud topology
    - Color-coded drift events with symbols
    - Real-time monitoring dashboard
    - Detailed incident reports
    - Interactive menu system
    - ASCII art headers
    - Progress indicators
    - Health score calculation
    """
    
    def __init__(self):
        """Initialize the CLI dashboard."""
        self.console = Console()
        self.current_layout = None
        self.symbol_map = {
            'critical': '[X]',
            'high': '[!]',
            'medium': '[*]',
            'low': '[i]',
            'info': '[i]',
            'success': '[+]',
            'error': '[-]',
            'warning': '[!]',
            'database': '[DB]',
            'vpc': '[VPC]',
            'ec2': '[EC2]',
            'security_group': '[SG]',
            'subnet': '[SUB]',
            'internet': '[NET]'
        }
    
    def print_header(self, title: str = "AeroDrift - Agentic Cloud Healer"):
        """
        Print the application header with enhanced styling.
        
        Args:
            title: Header title
        """
        # Simple ASCII Art Header without box characters
        ascii_art = """
    ================================================================
    
     A   E   R   O   D   R   I   F   T
    
                    Agentic Cloud Healer
               Self-Healing Infrastructure Engine
    
    ================================================================
"""
        
        self.console.print(ascii_art, style="bold cyan")
        
        # Subtitle with timestamp
        subtitle = Text.assemble(
            ("[*] ", "bold yellow"),
            (title, "bold white"),
            (" | ", "dim"),
            (f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]", "dim cyan")
        )
        
        self.console.print(Align.center(subtitle))
        self.console.print("=" * 60, style="cyan")
        self.console.print()
    
    def display_topology_tree(self, topology_engine, title: str = "Cloud Topology"):
        """
        Display the cloud topology as an interactive text tree with symbols.
        
        Args:
            topology_engine: TopologyEngine instance
            title: Tree title
        """
        tree = Tree(f"[bold blue][*] {title}[/bold blue]")
        
        # Add Internet node
        internet_id = topology_engine.internet_gateway_id
        internet_node = topology_engine.get_resource_details(internet_id)
        if internet_node:
            internet_branch = tree.add(f"[red][NET] {internet_node.name}[/red]")
            self._add_connected_resources(topology_engine, internet_branch, internet_id)
        
        # Add VPCs
        vpcs = [
            resource for resource in topology_engine.resource_index.values()
            if resource.resource_type.value == 'vpc'
        ]
        
        for vpc in sorted(vpcs, key=lambda x: x.name):
            vpc_branch = tree.add(f"[cyan][VPC] {vpc.name}[/cyan] ({vpc.attributes.get('cidr_block', '')})")
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
                resource_branch = branch.add(f"[bold red][!] {icon} {resource.name}[/bold red]")
            else:
                resource_branch = branch.add(f"[{color}][+] {icon} {resource.name}[/{color}]")
            
            # Recursively add children (limit depth to prevent infinite loops)
            if resource.resource_type.value not in ['ec2_instance', 'database']:
                self._add_connected_resources(topology_engine, resource_branch, connected_id)
    
    def _get_resource_icon_and_color(self, resource_type: str) -> tuple:
        """
        Get icon and color for a resource type with symbols.
        
        Args:
            resource_type: Type of resource
            
        Returns:
            Tuple of (icon, color)
        """
        icons = {
            'vpc': (f"{self.symbol_map['vpc']} VPC", 'cyan'),
            'subnet': (f"{self.symbol_map['subnet']} Subnet", 'green'),
            'security_group': (f"{self.symbol_map['security_group']} SG", 'yellow'),
            'ec2_instance': (f"{self.symbol_map['ec2']} EC2", 'blue'),
            'database': (f"{self.symbol_map['database']} DB", 'magenta'),
            'internet': (f"{self.symbol_map['internet']} Internet", 'red')
        }
        return icons.get(resource_type, ('[?] Resource', 'white'))
    
    def _get_drift_type_symbol(self, drift_type: str) -> str:
        """Get symbol for drift type."""
        symbol_map = {
            'exposed_database': '[DB]',
            'security_group_change': '[SG]',
            'new_public_instance': '[EC2]',
            'new_path_to_internet': '[NET]',
            'removed_resource': '[-]',
            'added_resource': '[+]'
        }
        return symbol_map.get(drift_type, '[?]')
    
    def display_drift_events(self, drift_events: List[Any], title: str = "Detected Drift Events"):
        """
        Display detected drift events in an enhanced table with symbols and better formatting.
        
        Args:
            drift_events: List of DriftEvent objects
            title: Table title
        """
        if not drift_events:
            self.console.print(Panel(
                f"{self.symbol_map['success']} No drift events detected - System is healthy!",
                title="System Status",
                border_style="green",
                padding=(1, 2)
            ))
            self.console.print()
            return
        
        # Create summary panel
        critical_count = len([e for e in drift_events if e.severity.value == 'critical'])
        high_count = len([e for e in drift_events if e.severity.value == 'high'])
        medium_count = len([e for e in drift_events if e.severity.value == 'medium'])
        
        summary_text = Text.assemble(
            (f"{self.symbol_map['critical']} Critical: ", "bold red"),
            (str(critical_count), "bold red"),
            (" | ", "dim"),
            (f"{self.symbol_map['high']} High: ", "bold orange"),
            (str(high_count), "bold orange"),
            (" | ", "dim"),
            (f"{self.symbol_map['medium']} Medium: ", "bold yellow"),
            (str(medium_count), "bold yellow"),
            (" | ", "dim"),
            (f"Total: {len(drift_events)}", "bold white")
        )
        
        self.console.print(Panel(summary_text, title="Event Summary", border_style="yellow"))
        self.console.print()
        
        # Enhanced table
        table = Table(
            title=title,
            show_header=True,
            header_style="bold magenta",
            box=HEAVY,
            padding=(0, 1)
        )
        table.add_column("[#] ID", style="dim", width=10)
        table.add_column("[!] Severity", style="bold", width=12)
        table.add_column("[?] Type", width=18)
        table.add_column("[@] Resource", width=18)
        table.add_column("[...] Description", width=35)
        table.add_column("[T] Time", width=12)
        
        for event in drift_events:
            severity_symbol = self.symbol_map.get(event.severity.value, '[?]')
            severity_style = {
                'critical': 'bold red',
                'high': 'bold orange',
                'medium': 'bold yellow',
                'low': 'bold blue',
                'info': 'dim'
            }.get(event.severity.value, 'white')
            
            type_symbol = self._get_drift_type_symbol(event.drift_type.value)
            
            table.add_row(
                event.event_id,
                f"{severity_symbol} [{severity_style}]{event.severity.value.upper()}[/{severity_style}]",
                f"{type_symbol} {event.drift_type.value.replace('_', ' ').title()}",
                event.resource_id[:15] + "..." if len(event.resource_id) > 15 else event.resource_id,
                event.description[:33] + "..." if len(event.description) > 33 else event.description,
                event.timestamp.strftime("%H:%M:%S")
            )
        
        self.console.print(table)
        self.console.print()
    
    def display_exposed_databases(self, exposed_dbs: List[Dict[str, Any]]):
        """
        Display exposed databases with enhanced visual formatting and security warnings.
        
        Args:
            exposed_dbs: List of exposed database information
        """
        if not exposed_dbs:
            self.console.print(Panel(
                f"{self.symbol_map['success']} No exposed databases found - All databases are secure!",
                title="Database Security Status",
                border_style="green",
                padding=(1, 2)
            ))
            self.console.print()
            return
        
        # Critical warning banner
        warning_banner = Text.assemble(
            (f"{self.symbol_map['critical']} CRITICAL SECURITY ALERT ", "bold red"),
            (f"{self.symbol_map['database']} {len(exposed_dbs)} EXPOSED DATABASE(S) DETECTED", "bold red"),
            (f" {self.symbol_map['critical']}", "bold red")
        )
        
        self.console.print(Panel(
            warning_banner,
            border_style="red",
            padding=(1, 2),
            box=HEAVY
        ))
        self.console.print()
        
        for idx, db in enumerate(exposed_dbs, 1):
            # Create detailed exposure panel
            content = Text()
            content.append(f"{self.symbol_map['database']} Database: ", style="bold red")
            content.append(db['name'], style="bold white")
            content.append("\n\n")
            content.append(f"{self.symbol_map['internet']} Attack Path from Internet:\n", style="bold yellow")
            content.append(db['path_description'], style="dim white")
            content.append("\n\n")
            content.append("[@] Resource ID: ", style="dim")
            content.append(db['resource_id'], style="cyan")
            
            panel = Panel(
                content,
                title=f"[red][!] EXPOSURE #{idx}[/red]",
                border_style="red",
                box=HEAVY,
                padding=(1, 2)
            )
            self.console.print(panel)
            self.console.print()
        
        # Action recommendation
        action_panel = Panel(
            Text.assemble(
                ("[*] RECOMMENDED ACTION: ", "bold yellow"),
                ("Review and revoke security group rules allowing internet access", "white"),
                ("\n\n", ""),
                ("[#] Use auto-remediation or manually revoke the rules shown above", "bold cyan")
            ),
            title="Security Recommendations",
            border_style="yellow",
            padding=(1, 2)
        )
        self.console.print(action_panel)
        self.console.print()
    
    def display_graph_statistics(self, stats: Dict[str, Any]):
        """
        Display topology graph statistics with enhanced visual formatting.
        
        Args:
            stats: Statistics dictionary
        """
        # Create two-column layout for better space utilization
        left_panel = Table(show_header=False, box=SIMPLE, padding=(0, 2))
        left_panel.add_column("Metric", style="cyan", width=20)
        left_panel.add_column("Value", style="bold white", width=15)
        
        left_panel.add_row("[#] Total Nodes", str(stats['total_nodes']))
        left_panel.add_row("[=] Total Edges", str(stats['total_edges']))
        left_panel.add_row("[<->] Graph Connected", f"{self.symbol_map['success']} Yes" if stats['is_connected'] else f"{self.symbol_map['error']} No")
        
        right_panel = Table(show_header=False, box=SIMPLE, padding=(0, 2))
        right_panel.add_column("Resource Type", style="cyan", width=20)
        right_panel.add_column("Count", style="bold white", width=15)
        
        for resource_type, count in stats['resource_type_counts'].items():
            symbol = self.symbol_map.get(resource_type, '[?]')
            right_panel.add_row(f"{symbol} {resource_type.title()}s", str(count))
        
        # Exposed databases highlight
        exposed_style = "bold red" if stats['exposed_databases'] > 0 else "bold green"
        exposed_text = f"{self.symbol_map['critical']} {stats['exposed_databases']}" if stats['exposed_databases'] > 0 else f"{self.symbol_map['success']} {stats['exposed_databases']}"
        left_panel.add_row("[DB] Exposed DBs", f"[{exposed_style}]{exposed_text}[/{exposed_style}]")
        
        # Combine panels
        combined = Columns([left_panel, right_panel], equal=True)
        
        self.console.print(Panel(
            combined,
            title=f"[^] Topology Statistics",
            border_style="cyan",
            box=HEAVY,
            padding=(1, 1)
        ))
        self.console.print()
    
    def display_remediation_code(self, code: str, title: str = "Generated Remediation Code"):
        """
        Display generated remediation code with enhanced syntax highlighting and warnings.
        
        Args:
            code: Python code to display
            title: Code block title
        """
        # Warning panel
        warning = Panel(
            Text.assemble(
                (f"{self.symbol_map['warning']} ", "bold yellow"),
                ("This code will be executed in a sandboxed environment", "yellow"),
                ("\n", ""),
                (f"{self.symbol_map['info']} ", "bold cyan"),
                ("Review the code before allowing execution", "cyan")
            ),
            border_style="yellow",
            padding=(0, 2)
        )
        self.console.print(warning)
        
        # Code display with better theme
        syntax = Syntax(code, "python", theme="github-dark", line_numbers=True, word_wrap=True)
        panel = Panel(
            syntax,
            title=f"[#] {title}",
            border_style="green",
            box=HEAVY,
            padding=(0, 1)
        )
        self.console.print(panel)
        self.console.print()
    
    def display_incident_report(self, drift_events: List[Any], topology_stats: Dict[str, Any]):
        """
        Display a comprehensive incident report with enhanced formatting.
        
        Args:
            drift_events: List of drift events
            topology_stats: Topology statistics
        """
        self.print_header("AeroDrift Incident Report")
        
        # Executive Summary with health score
        critical_count = len([e for e in drift_events if e.severity.value == 'critical'])
        high_count = len([e for e in drift_events if e.severity.value == 'high'])
        total_events = len(drift_events)
        
        # Calculate health score (0-100)
        health_score = max(0, 100 - (critical_count * 25) - (high_count * 10))
        health_color = "green" if health_score >= 80 else "yellow" if health_score >= 50 else "red"
        
        summary_table = Table(show_header=False, box=SIMPLE, padding=(0, 2))
        summary_table.add_column("Metric", style="cyan", width=25)
        summary_table.add_column("Value", style="bold white", width=25)
        
        summary_table.add_row("[@] Report Timestamp", datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC'))
        summary_table.add_row("[<3] Health Score", f"[{health_color}]{health_score}/100[/{health_color}]")
        summary_table.add_row(f"{self.symbol_map['critical']} Critical Events", f"[bold red]{critical_count}[/bold red]")
        summary_table.add_row(f"{self.symbol_map['high']} High Severity", f"[bold orange]{high_count}[/bold orange]")
        summary_table.add_row("[#] Total Events", str(total_events))
        
        self.console.print(Panel(
            summary_table,
            title="[*] Executive Summary",
            border_style="yellow",
            box=HEAVY,
            padding=(1, 2)
        ))
        self.console.print()
        
        # Topology Stats
        self.display_graph_statistics(topology_stats)
        
        # Drift Events
        self.display_drift_events(drift_events)
        
        # Footer with branding
        footer = Panel(
            Text.assemble(
                ("Generated by ", "dim"),
                ("AeroDrift", "bold cyan"),
                (" - Agentic Cloud Healer", "dim"),
                (f" {self.symbol_map['success']}", "green")
            ),
            box=ROUNDED,
            padding=(0, 2),
            border_style="dim"
        )
        self.console.print(footer)
    
    def display_live_monitoring(self, update_callback, refresh_rate: float = 1.0):
        """
        Display a live monitoring dashboard with enhanced visuals.
        
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
        Create an enhanced layout for live monitoring.
        
        Args:
            topology_engine: TopologyEngine instance
            drift_events: List of drift events
            
        Returns:
            Rich Layout object
        """
        layout = Layout()
        
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="stats", size=10),
            Layout(name="events", size=15),
            Layout(name="footer", size=3)
        )
        
        # Header with branding
        layout["header"].update(
            Panel(
                Text.assemble(
                    ("[*] AeroDrift ", "bold cyan"),
                    ("Live Monitoring", "bold white"),
                    (" | ", "dim"),
                    (f"[@] {datetime.now().strftime('%H:%M:%S')}", "dim")
                ),
                box=DOUBLE,
                border_style="cyan"
            )
        )
        
        # Statistics with symbols
        stats = topology_engine.get_graph_statistics()
        critical_count = len([e for e in drift_events if e.severity.value == 'critical'])
        high_count = len([e for e in drift_events if e.severity.value == 'high'])
        
        stats_text = Text.assemble(
            ("[#] Nodes: ", "cyan"),
            (str(stats['total_nodes']), "bold white"),
            (" | ", "dim"),
            ("[=] Edges: ", "cyan"),
            (str(stats['total_edges']), "bold white"),
            (" | ", "dim"),
            ("[DB] Exposed DBs: ", "red" if stats['exposed_databases'] > 0 else "green"),
            (str(stats['exposed_databases']), "bold"),
            (" | ", "dim"),
            ("[!] Critical: ", "red"),
            (str(critical_count), "bold red"),
            (" | ", "dim"),
            ("[!] High: ", "orange"),
            (str(high_count), "bold orange"),
            (" | ", "dim"),
            ("[#] Total Events: ", "cyan"),
            (str(len(drift_events)), "bold white"),
            ("\n\n", ""),
            ("[T] Last Update: ", "dim"),
            (datetime.utcnow().strftime('%H:%M:%S UTC'), "dim cyan")
        )
        
        layout["stats"].update(Panel(stats_text, title="[^] Real-time Statistics", border_style="cyan"))
        
        # Events with better formatting
        if drift_events:
            recent_events = drift_events[-5:]  # Show last 5 events
            events_text = Text()
            for event in recent_events:
                severity_symbol = self.symbol_map.get(event.severity.value, '[?]')
                events_text.append(f"{severity_symbol} ", style="bold")
                events_text.append(f"{event.description}\n", style="white")
        else:
            events_text = Text.assemble(
                (f"{self.symbol_map['success']} No recent events - System is healthy!", "green")
            )
        
        layout["events"].update(Panel(events_text, title="[?] Recent Events", border_style="yellow"))
        
        # Footer
        layout["footer"].update(
            Panel(
                Text("Press Ctrl+C to exit", style="dim", justify="center"),
                box=ROUNDED,
                border_style="dim"
            )
        )
        
        return layout
    
    def create_progress(self, task_name: str, total: int = 100):
        """
        Create an enhanced progress bar for long-running operations.
        
        Args:
            task_name: Name of the task
            total: Total items to process
        """
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeRemainingColumn(),
            console=self.console
        )
        task = progress.add_task(task_name, total=total)
        return progress, task
    
    def print_success(self, message: str):
        """Print a success message with symbol."""
        self.console.print(f"[green]{self.symbol_map['success']} {message}[/green]")
    
    def print_error(self, message: str):
        """Print an error message with symbol."""
        self.console.print(f"[red]{self.symbol_map['error']} {message}[/red]")
    
    def print_warning(self, message: str):
        """Print a warning message with symbol."""
        self.console.print(f"[yellow]{self.symbol_map['warning']} {message}[/yellow]")
    
    def print_info(self, message: str):
        """Print an info message with symbol."""
        self.console.print(f"[blue]{self.symbol_map['info']} {message}[/blue]")
    
    def display_interactive_menu(self):
        """
        Display an interactive menu for user actions.
        
        Returns:
            User's menu choice
        """
        menu_options = [
            "1. Run Drift Scan",
            "2. View Topology",
            "3. View Statistics",
            "4. Generate Report",
            "5. Start Monitoring",
            "6. Exit"
        ]
        
        menu_table = Table(show_header=False, box=HEAVY, padding=(0, 2))
        menu_table.add_column("Option", style="cyan", width=10)
        menu_table.add_column("Action", style="white", width=30)
        
        for option in menu_options:
            menu_table.add_row(option.split(".")[0], option.split(". ", 1)[1])
        
        self.console.print(Panel(menu_table, title="[$] Main Menu", border_style="cyan"))
        
        choice = Prompt.ask(
            "Select an option",
            choices=["1", "2", "3", "4", "5", "6"],
            default="1"
        )
        
        return choice
    
    def print(self):
        """Print an empty line for spacing."""
        self.console.print()

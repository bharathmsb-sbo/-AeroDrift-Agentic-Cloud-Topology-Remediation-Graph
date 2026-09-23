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
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.syntax import Syntax
from rich.box import DOUBLE, ROUNDED, HEAVY, SIMPLE
from rich.columns import Columns
from rich.align import Align
from rich.rule import Rule
from rich.emoji import Emoji
from rich.prompt import Prompt
from rich.markdown import Markdown

logger = logging.getLogger(__name__)


class CLIDashboard:
    """
    Beautiful CLI reporting tool using Rich library.
    
    Features:
    - Interactive text tree for cloud topology
    - Color-coded drift events with emojis
    - Real-time monitoring dashboard
    - Detailed incident reports
    - Interactive menu system
    - ASCII art headers
    - Progress indicators
    """
    
    def __init__(self):
        """Initialize the CLI dashboard."""
        self.console = Console()
        self.current_layout = None
        self.emoji_map = {
            'critical': '🚨',
            'high': '⚠️',
            'medium': '🔶',
            'low': '🔵',
            'info': 'ℹ️',
            'success': '✅',
            'error': '❌',
            'warning': '⚡',
            'database': '🗄️',
            'vpc': '🌐',
            'ec2': '💻',
            'security_group': '🔒',
            'subnet': '📡',
            'internet': '🌍'
        }
    
    def print_header(self, title: str = "AeroDrift - Agentic Cloud Healer"):
        """
        Print the application header with ASCII art and enhanced styling.
        
        Args:
            title: Header title
        """
        # ASCII Art Header
        ascii_art = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║     ██╗   ██╗██╗██████╗ ████████╗██╗   ██╗██████╗ ███████╗    ║
    ║     ██║   ██║██║██╔══██╗╚══██╔══╝██║   ██║██╔══██╗██╔════╝    ║
    ║     ██║   ██║██║██████╔╝   ██║   ██║   ██║██████╔╝█████╗      ║
    ║     ╚██╗ ██╔╝██║██╔══██╗   ██║   ██║   ██║██╔══██╗██╔══╝      ║
    ║      ╚████╔╝ ██║██████╔╝   ██║   ╚██████╔╝██████╔╝███████╗    ║
    ║       ╚═══╝  ╚═╝╚═════╝    ╚═╝    ╚═════╝ ╚═════╝ ╚══════╝    ║
    ║                                                               ║
    ║                    Agentic Cloud Healer                        ║
    ║               Self-Healing Infrastructure Engine               ║
    ╚═══════════════════════════════════════════════════════════════╝
"""
        
        self.console.print(ascii_art, style="bold cyan")
        
        # Subtitle with timestamp
        subtitle = Text.assemble(
            ("🛡️ ", "bold yellow"),
            (title, "bold white"),
            (" | ", "dim"),
            (f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "dim cyan")
        )
        
        self.console.print(Align.center(subtitle))
        self.console.print(Rule(style="cyan"))
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
        Get icon and color for a resource type with emojis.
        
        Args:
            resource_type: Type of resource
            
        Returns:
            Tuple of (icon, color)
        """
        icons = {
            'vpc': (f"{self.emoji_map['vpc']} VPC", 'cyan'),
            'subnet': (f"{self.emoji_map['subnet']} Subnet", 'green'),
            'security_group': (f"{self.emoji_map['security_group']} SG", 'yellow'),
            'ec2_instance': (f"{self.emoji_map['ec2']} EC2", 'blue'),
            'database': (f"{self.emoji_map['database']} DB", 'magenta'),
            'internet': (f"{self.emoji_map['internet']} Internet", 'red')
        }
        return icons.get(resource_type, ('❓ Resource', 'white'))
    
    def _get_drift_type_emoji(self, drift_type: str) -> str:
        """Get emoji for drift type."""
        emoji_map = {
            'exposed_database': '🗄️',
            'security_group_change': '🔒',
            'new_public_instance': '💻',
            'new_path_to_internet': '🌍',
            'removed_resource': '🗑️',
            'added_resource': '➕'
        }
        return emoji_map.get(drift_type, '📋')
    
    def display_drift_events(self, drift_events: List[Any], title: str = "Detected Drift Events"):
        """
        Display detected drift events in an enhanced table with emojis and better formatting.
        
        Args:
            drift_events: List of DriftEvent objects
            title: Table title
        """
        if not drift_events:
            self.console.print(Panel(
                f"{self.emoji_map['success']} No drift events detected - System is healthy!",
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
            (f"{self.emoji_map['critical']} Critical: ", "bold red"),
            (str(critical_count), "bold red"),
            (" | ", "dim"),
            (f"{self.emoji_map['high']} High: ", "bold orange"),
            (str(high_count), "bold orange"),
            (" | ", "dim"),
            (f"{self.emoji_map['medium']} Medium: ", "bold yellow"),
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
        table.add_column("🆔 ID", style="dim", width=10)
        table.add_column("⚡ Severity", style="bold", width=12)
        table.add_column("📋 Type", width=18)
        table.add_column("🎯 Resource", width=18)
        table.add_column("📝 Description", width=35)
        table.add_column("⏰ Time", width=12)
        
        for event in drift_events:
            severity_emoji = self.emoji_map.get(event.severity.value, '❓')
            severity_style = {
                'critical': 'bold red',
                'high': 'bold orange',
                'medium': 'bold yellow',
                'low': 'bold blue',
                'info': 'dim'
            }.get(event.severity.value, 'white')
            
            type_emoji = self._get_drift_type_emoji(event.drift_type.value)
            
            table.add_row(
                event.event_id,
                f"{severity_emoji} [{severity_style}]{event.severity.value.upper()}[/{severity_style}]",
                f"{type_emoji} {event.drift_type.value.replace('_', ' ').title()}",
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
                f"{self.emoji_map['success']} No exposed databases found - All databases are secure!",
                title="Database Security Status",
                border_style="green",
                padding=(1, 2)
            ))
            self.console.print()
            return
        
        # Critical warning banner
        warning_banner = Text.assemble(
            (f"{self.emoji_map['critical']} CRITICAL SECURITY ALERT ", "bold red"),
            (f"{self.emoji_map['database']} {len(exposed_dbs)} EXPOSED DATABASE(S) DETECTED", "bold red"),
            (f" {self.emoji_map['critical']}", "bold red")
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
            content.append(f"{self.emoji_map['database']} Database: ", style="bold red")
            content.append(db['name'], style="bold white")
            content.append("\n\n")
            content.append(f"{self.emoji_map['internet']} Attack Path from Internet:\n", style="bold yellow")
            content.append(db['path_description'], style="dim white")
            content.append("\n\n")
            content.append("🔗 Resource ID: ", style="dim")
            content.append(db['resource_id'], style="cyan")
            
            panel = Panel(
                content,
                title=f"[red]🚨 EXPOSURE #{idx}[/red]",
                border_style="red",
                box=HEAVY,
                padding=(1, 2)
            )
            self.console.print(panel)
            self.console.print()
        
        # Action recommendation
        action_panel = Panel(
            Text.assemble(
                ("💡 RECOMMENDED ACTION: ", "bold yellow"),
                ("Review and revoke security group rules allowing internet access", "white"),
                ("\n\n", ""),
                ("🔧 Use auto-remediation or manually revoke the rules shown above", "bold cyan")
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
        
        left_panel.add_row("📊 Total Nodes", str(stats['total_nodes']))
        left_panel.add_row("🔗 Total Edges", str(stats['total_edges']))
        left_panel.add_row("🌐 Graph Connected", f"{self.emoji_map['success']} Yes" if stats['is_connected'] else f"{self.emoji_map['error']} No")
        
        right_panel = Table(show_header=False, box=SIMPLE, padding=(0, 2))
        right_panel.add_column("Resource Type", style="cyan", width=20)
        right_panel.add_column("Count", style="bold white", width=15)
        
        for resource_type, count in stats['resource_type_counts'].items():
            emoji = self.emoji_map.get(resource_type, '📋')
            right_panel.add_row(f"{emoji} {resource_type.title()}s", str(count))
        
        # Exposed databases highlight
        exposed_style = "bold red" if stats['exposed_databases'] > 0 else "bold green"
        exposed_text = f"{self.emoji_map['critical']} {stats['exposed_databases']}" if stats['exposed_databases'] > 0 else f"{self.emoji_map['success']} {stats['exposed_databases']}"
        left_panel.add_row("🗄️ Exposed DBs", f"[{exposed_style}]{exposed_text}[/{exposed_style}]")
        
        # Combine panels
        combined = Columns([left_panel, right_panel], equal=True)
        
        self.console.print(Panel(
            combined,
            title=f"📈 Topology Statistics",
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
                (f"{self.emoji_map['warning']} ", "bold yellow"),
                ("This code will be executed in a sandboxed environment", "yellow"),
                ("\n", ""),
                (f"{self.emoji_map['info']} ", "bold cyan"),
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
            title=f"🔧 {title}",
            border_style="green",
            box=HEAVY,
            padding=(0, 1)
        )
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

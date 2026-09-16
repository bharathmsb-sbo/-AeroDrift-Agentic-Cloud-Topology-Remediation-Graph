"""
AeroDrift Main Daemon: Entry point for the Agentic Cloud Healer.
"""

import asyncio
import logging
import argparse
import sys
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

from aerodrift.cloud_ingestion import AWSIngestion
from aerodrift.topology_engine import TopologyEngine
from aerodrift.drift_detection import DriftDetector
from aerodrift.code_generator import CodeGenerator
from aerodrift.cli_dashboard import CLIDashboard
from aerodrift.state_persistence import StatePersistence
from aerodrift.utils import Config, ExecutionSandbox


class AeroDriftDaemon:
    """
    Main daemon that orchestrates all AeroDrift components.
    
    This is the core engine that:
    - Ingests cloud data
    - Builds topology graphs
    - Detects configuration drift
    - Generates remediation code
    - Executes autonomous healing
    """
    
    def __init__(self, config: Config):
        """
        Initialize the AeroDrift daemon.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.config.setup_logging()
        
        # Initialize components
        self.ingestion = AWSIngestion(
            region=config.aws_region,
            use_mock=config.aws_use_mock
        )
        
        self.topology = TopologyEngine()
        self.drift_detector = DriftDetector()
        self.code_generator = CodeGenerator()
        self.dashboard = CLIDashboard()
        self.persistence = StatePersistence(config.db_path)
        self.sandbox = ExecutionSandbox()
        
        self.running = False
        logger.info("AeroDrift daemon initialized")
    
    async def initialize(self):
        """Initialize the daemon by collecting initial baseline data."""
        self.dashboard.print_header("AeroDrift Daemon")
        self.dashboard.print_info("Initializing AeroDrift daemon...")
        
        # Collect initial AWS data
        self.dashboard.print_info("Collecting initial AWS resources...")
        aws_data = await self.ingestion.collect_all_resources()
        
        # Build initial topology
        self.dashboard.print_info("Building initial topology graph...")
        self.topology.build_from_aws_data(aws_data)
        
        # Set baseline
        self.drift_detector.set_baseline(self.topology)
        
        # Save initial snapshot
        self.persistence.save_topology_snapshot(aws_data)
        
        self.dashboard.print_success("AeroDrift daemon initialized successfully")
        self.dashboard.print()
    
    async def run_single_scan(self):
        """Run a single scan for drift detection."""
        self.dashboard.print_header("AeroDrift Scan")
        self.dashboard.print_info("Running single drift scan...")
        
        # Collect current AWS data
        self.dashboard.print_info("Collecting current AWS resources...")
        aws_data = await self.ingestion.collect_all_resources()
        
        # Build current topology
        self.dashboard.print_info("Building current topology graph...")
        current_topology = TopologyEngine()
        current_topology.build_from_aws_data(aws_data)
        
        # Update drift detector
        self.drift_detector.update_current_state(current_topology)
        
        # Detect drift
        self.dashboard.print_info("Detecting configuration drift...")
        drift_events = self.drift_detector.detect_drift()
        
        # Save drift events to database
        for event in drift_events:
            self.persistence.save_drift_event(event)
        
        # Save current snapshot
        self.persistence.save_topology_snapshot(aws_data)
        
        # Display results
        self.dashboard.print()
        self.dashboard.display_drift_events(drift_events)
        
        # Check for exposed databases
        exposed_dbs = current_topology.find_exposed_databases()
        if exposed_dbs:
            self.dashboard.display_exposed_databases(exposed_dbs)
        
        # Display topology statistics
        stats = current_topology.get_graph_statistics()
        self.dashboard.display_graph_statistics(stats)
        
        # Display topology tree
        self.dashboard.display_topology_tree(current_topology)
        
        # Handle remediation if configured
        if drift_events and self.config.auto_remediate:
            await self.handle_remediation(drift_events)
        
        return drift_events
    
    async def handle_remediation(self, drift_events):
        """
        Handle remediation of detected drift events.
        
        Args:
            drift_events: List of drift events requiring remediation
        """
        events_requiring_remediation = [
            event for event in drift_events if event.remediation_required
        ]
        
        if not events_requiring_remediation:
            return
        
        self.dashboard.print_warning(f"Found {len(events_requiring_remediation)} events requiring remediation")
        
        if self.config.require_approval:
            self.dashboard.print_info("Auto-remediation requires approval. Set require_approval=False to enable.")
            return
        
        for event in events_requiring_remediation:
            self.dashboard.print_info(f"Generating remediation for {event.event_id}...")
            
            # Generate remediation code
            code = self.code_generator.generate_remediation_script(event)
            
            # Display generated code
            self.dashboard.display_remediation_code(code)
            
            # Execute in sandbox
            self.dashboard.print_info("Executing remediation in sandbox...")
            result = self.sandbox.execute_remediation(code, timeout=self.config.remediation_timeout)
            
            if result['success']:
                self.dashboard.print_success(f"Remediation successful for {event.event_id}")
                self.persistence.mark_event_remediated(event.event_id, success=True)
            else:
                self.dashboard.print_error(f"Remediation failed for {event.event_id}: {result['error']}")
                self.persistence.mark_event_remediated(event.event_id, success=False)
    
    async def run_continuous_monitoring(self):
        """Run continuous monitoring with polling."""
        self.dashboard.print_header("AeroDrift Monitoring")
        self.dashboard.print_info(f"Starting continuous monitoring (interval: {self.config.polling_interval}s)")
        self.dashboard.print_info("Press Ctrl+C to stop")
        self.dashboard.print()
        
        self.running = True
        
        try:
            while self.running:
                # Run scan
                drift_events = await self.run_single_scan()
                
                # Wait for next interval
                await asyncio.sleep(self.config.polling_interval)
                
        except KeyboardInterrupt:
            self.dashboard.print_warning("Monitoring stopped by user")
            self.running = False
    
    async def run_live_dashboard(self):
        """Run live dashboard mode."""
        self.dashboard.print_header("AeroDrift Live Dashboard")
        self.dashboard.print_info("Starting live dashboard mode...")
        self.dashboard.print_info("Press Ctrl+C to stop")
        self.dashboard.print()
        
        def update_layout():
            # Collect current data
            try:
                current_topology = TopologyEngine()
                # In a real implementation, you'd collect fresh data here
                # For now, use the existing topology
                if self.topology.graph.number_of_nodes() > 0:
                    current_topology = self.topology
                
                drift_events = self.drift_detector.detected_events
                return self.dashboard.create_monitoring_layout(current_topology, drift_events)
            except Exception as e:
                self.dashboard.print_error(f"Error updating dashboard: {e}")
                return self.dashboard.create_monitoring_layout(self.topology, [])
        
        try:
            self.dashboard.display_live_monitoring(update_layout, self.config.dashboard_refresh_rate)
        except KeyboardInterrupt:
            self.dashboard.print_warning("Live dashboard stopped by user")
    
    def generate_incident_report(self):
        """Generate and display an incident report."""
        self.dashboard.print_header()
        self.dashboard.print_info("Generating incident report...")
        
        # Get latest drift events
        drift_events = self.drift_detector.detected_events
        if not drift_events:
            # Load from database
            db_events = self.persistence.get_drift_events(limit=20)
            drift_events = db_events
        
        # Get topology statistics
        stats = self.topology.get_graph_statistics()
        
        # Display report
        self.dashboard.display_incident_report(drift_events, stats)
    
    def show_statistics(self):
        """Show database and runtime statistics."""
        self.dashboard.print_header("AeroDrift Statistics")
        
        # Database statistics
        db_stats = self.persistence.get_statistics()
        
        stats_table = self.dashboard.console.table
        self.dashboard.console.print("[bold]Database Statistics[/bold]")
        self.dashboard.console.print(f"Total Snapshots: {db_stats['total_snapshots']}")
        self.dashboard.console.print(f"Total Drift Events: {db_stats['total_drift_events']}")
        self.dashboard.console.print(f"Remediated Events: {db_stats['remediated_events']}")
        self.dashboard.console.print(f"Pending Remediation: {db_stats['pending_remediation']}")
        self.dashboard.console.print()
        
        # Topology statistics
        topology_stats = self.topology.get_graph_statistics()
        self.dashboard.display_graph_statistics(topology_stats)
        
        # Sandbox statistics
        sandbox_history = self.sandbox.get_execution_history()
        self.dashboard.console.print(f"[bold]Sandbox Executions:[/bold] {len(sandbox_history)}")
        self.dashboard.console.print()


async def main():
    """Main entry point for AeroDrift."""
    parser = argparse.ArgumentParser(
        description="AeroDrift - Agentic Cloud Topology & Remediation Graph"
    )
    parser.add_argument(
        '--config',
        default='aerodrift_config.json',
        help='Path to configuration file'
    )
    parser.add_argument(
        '--mode',
        choices=['init', 'scan', 'monitor', 'dashboard', 'report', 'stats'],
        default='scan',
        help='Operation mode'
    )
    parser.add_argument(
        '--region',
        help='AWS region (overrides config)'
    )
    parser.add_argument(
        '--mock',
        action='store_true',
        help='Use mock AWS data'
    )
    parser.add_argument(
        '--auto-remediate',
        action='store_true',
        help='Enable automatic remediation'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = Config.from_file(args.config)
    config.override_from_env()
    
    # Override with command-line arguments
    if args.region:
        config.aws_region = args.region
    if args.mock:
        config.aws_use_mock = True
    if args.auto_remediate:
        config.auto_remediate = True
    
    # Validate configuration
    if not config.validate():
        sys.exit(1)
    
    # Initialize daemon
    daemon = AeroDriftDaemon(config)
    
    try:
        # Run based on mode
        if args.mode == 'init':
            await daemon.initialize()
        elif args.mode == 'scan':
            await daemon.initialize()
            await daemon.run_single_scan()
        elif args.mode == 'monitor':
            await daemon.initialize()
            await daemon.run_continuous_monitoring()
        elif args.mode == 'dashboard':
            await daemon.initialize()
            await daemon.run_live_dashboard()
        elif args.mode == 'report':
            await daemon.initialize()
            daemon.generate_incident_report()
        elif args.mode == 'stats':
            await daemon.initialize()
            daemon.show_statistics()
            
    except Exception as e:
        logger.error(f"Error running AeroDrift: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

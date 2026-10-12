"""
Basic usage example for AeroDrift.

This example demonstrates how to use AeroDrift to detect cloud configuration drift.
"""

import asyncio
from aerodrift.cloud_ingestion import AWSIngestion
from aerodrift.topology_engine import TopologyEngine
from aerodrift.drift_detection import DriftDetector
from aerodrift.cli_dashboard import CLIDashboard


async def basic_drift_detection():
    """Demonstrate basic drift detection workflow."""
    
    # Initialize components
    print("Initializing AeroDrift components...")
    ingestion = AWSIngestion(use_mock=True)  # Use mock data for demo
    topology = TopologyEngine()
    detector = DriftDetector()
    dashboard = CLIDashboard()
    
    # Collect AWS data
    print("Collecting AWS resources...")
    aws_data = await ingestion.collect_all_resources()
    
    # Build topology graph
    print("Building topology graph...")
    topology.build_from_aws_data(aws_data)
    
    # Set baseline
    print("Setting baseline...")
    detector.set_baseline(topology)
    
    # Display initial topology
    dashboard.print_header("Initial Cloud Topology")
    dashboard.display_topology_tree(topology)
    
    # Display statistics
    stats = topology.get_graph_statistics()
    dashboard.display_graph_statistics(stats)
    
    # Check for exposed databases
    print("Checking for exposed databases...")
    exposed_dbs = topology.find_exposed_databases()
    
    if exposed_dbs:
        dashboard.print_warning(f"Found {len(exposed_dbs)} exposed databases!")
        dashboard.display_exposed_databases(exposed_dbs)
    else:
        dashboard.print_success("No exposed databases found")
    
    print("\n[+] Basic drift detection completed!")


if __name__ == "__main__":
    asyncio.run(basic_drift_detection())

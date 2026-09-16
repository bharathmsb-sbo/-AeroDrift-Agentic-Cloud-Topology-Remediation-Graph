"""
Drift simulation example for AeroDrift.

This example demonstrates how to simulate configuration drift and detect it.
"""

import asyncio
from aerodrift.cloud_ingestion import AWSIngestion
from aerodrift.topology_engine import TopologyEngine
from aerodrift.drift_detection import DriftDetector
from aerodrift.cli_dashboard import CLIDashboard


async def simulate_and_detect_drift():
    """Simulate configuration drift and detect it."""
    
    # Initialize components
    print("Initializing AeroDrift for drift simulation...")
    ingestion = AWSIngestion(use_mock=True)
    topology = TopologyEngine()
    detector = DriftDetector()
    dashboard = CLIDashboard()
    
    # Collect initial AWS data (baseline)
    print("\n1. Collecting baseline AWS data...")
    aws_data_baseline = await ingestion.collect_all_resources()
    
    # Build baseline topology
    print("2. Building baseline topology...")
    topology.build_from_aws_data(aws_data_baseline)
    detector.set_baseline(topology)
    
    dashboard.print_success("Baseline established")
    baseline_stats = topology.get_graph_statistics()
    dashboard.display_graph_statistics(baseline_stats)
    
    # Simulate drift by modifying mock data
    print("\n3. Simulating configuration drift...")
    if hasattr(ingestion, 'mock_data'):
        # Add a vulnerable rule to the secure database security group
        ingestion.mock_data.add_vulnerable_rule("sg-secure-db", cidr="0.0.0.0/0", port=3306)
        print("   - Added internet access to secure database (port 3306)")
        
        # Add SSH access to application tier
        ingestion.mock_data.add_vulnerable_rule("sg-app-tier", cidr="0.0.0.0/0", port=22)
        print("   - Added SSH access to application tier")
    
    # Collect current AWS data (with drift)
    print("\n4. Collecting current AWS data (with drift)...")
    aws_data_current = await ingestion.collect_all_resources()
    
    # Build current topology
    print("5. Building current topology...")
    current_topology = TopologyEngine()
    current_topology.build_from_aws_data(aws_data_current)
    detector.update_current_state(current_topology)
    
    # Detect drift
    print("\n6. Detecting configuration drift...")
    drift_events = detector.detect_drift()
    
    # Display results
    dashboard.print_header("Drift Detection Results")
    
    if drift_events:
        dashboard.print_warning(f"Detected {len(drift_events)} drift events!")
        dashboard.display_drift_events(drift_events)
        
        # Show critical events
        critical_events = detector.get_critical_events()
        if critical_events:
            dashboard.print_error(f"Critical events: {len(critical_events)}")
            dashboard.display_drift_events(critical_events)
    else:
        dashboard.print_success("No drift detected")
    
    # Show exposed databases
    print("\n7. Checking for exposed databases...")
    exposed_dbs = current_topology.find_exposed_databases()
    
    if exposed_dbs:
        dashboard.print_error(f"Found {len(exposed_dbs)} exposed databases!")
        dashboard.display_exposed_databases(exposed_dbs)
    else:
        dashboard.print_success("No exposed databases")
    
    # Display current topology
    print("\n8. Current topology after drift:")
    dashboard.display_topology_tree(current_topology)
    
    print("\n[+] Drift simulation completed!")


if __name__ == "__main__":
    asyncio.run(simulate_and_detect_drift())

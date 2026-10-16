"""
End-to-End Integration Test for AeroDrift.
Validates the complete autonomous agentic loop:
Ingestion -> Topology Graph -> Baseline Snapshot -> Drift Detection ->
AST Remediation -> State Verification -> Graph Diff -> PDF Incident Report.
"""

from src.ingestion.mock_aws import MockAWSProvider
from src.topology.graph_engine import CloudTopology
from src.detection.drift_detector import detect_drift
from src.remediation.code_generator import generate_remediation_code
from src.remediation.executor import RemediationExecutor
from src.remediation.verifier import verify_remediation
from src.history.database import HistoryDatabase
from src.history.diff import compare_snapshots
from src.history.incident_report import IncidentReportGenerator


def test_full_aerodrift_agentic_pipeline(tmp_path):
    """
    Validates complete agentic closed-loop execution without side effects,
    using an isolated SQLite database and isolated report directory.
    """
    # 0. Setup isolated test environment
    test_db_path = tmp_path / "integration_history.db"
    test_reports_dir = tmp_path / "integration_reports"
    history_db = HistoryDatabase(database_path=str(test_db_path))
    history_db.initialize()

    # 1. Ingestion: Fetch mock AWS cloud resources
    provider = MockAWSProvider()
    resources = provider.get_all_resources()
    assert "security_groups" in resources
    assert "ec2_instances" in resources

    # 2. Topology Construction: Build NetworkX DiGraph
    topology = CloudTopology(resources)
    graph = topology.build()
    assert graph.number_of_nodes() == 6
    assert graph.number_of_edges() == 4
    assert graph.has_edge("internet", "sg-001")

    # 3. Baseline Persistence: Save initial topology snapshot
    history_db.save_snapshot(graph)
    initial_snapshot = history_db.get_latest_snapshot()
    assert initial_snapshot is not None
    assert initial_snapshot["node_count"] == 6

    # 4. Drift Detection: Identify unauthorized exposure
    findings = detect_drift(graph)
    assert len(findings) == 1
    finding = findings[0]
    assert finding["security_group"] == "sg-001"
    assert finding["port"] == 22
    assert finding["source"] == "0.0.0.0/0"

    # 5. AST Remediation: Synthesize and execute fix in sandbox
    ast_code = generate_remediation_code(finding)
    assert "revoke_security_group_ingress" in ast_code

    executor = RemediationExecutor(resources=resources)
    executor.execute(ast_code)

    # 6. Verification: Confirm drift removal in resource state
    is_resolved = verify_remediation(resources, finding)
    assert is_resolved is True
    remediation_status = "DRIFT RESOLVED" if is_resolved else "DRIFT STILL PRESENT"
    assert remediation_status == "DRIFT RESOLVED"

    # 7. Post-Remediation Topology & Graph Diff Check
    # Simulate remediated topology by revoking the public ingress edge
    graph_remediated = graph.copy()
    graph_remediated.remove_edge("internet", "sg-001")
    history_db.save_snapshot(graph_remediated)

    current_snapshot = history_db.get_latest_snapshot()
    assert current_snapshot["id"] == 2

    diff = compare_snapshots(initial_snapshot, current_snapshot)
    assert diff["added_nodes"] == []
    assert diff["removed_nodes"] == []
    assert len(diff["removed_edges"]) == 1
    assert "internet" in diff["removed_edges"][0]
    assert "sg-001" in diff["removed_edges"][0]

    # 8. Incident Reporting: Compile PDF audit trail
    report_gen = IncidentReportGenerator(output_directory=str(test_reports_dir))
    report_file = report_gen.generate(finding, remediation_status)
    assert report_file.exists()
    assert report_file.stat().st_size > 0
    assert report_file.suffix == ".pdf"
"""
Unit tests for the AeroDrift Rich CLI dashboard.
Verifies topology loading, drift detection trigger, summary displays,
and full dashboard orchestration.
"""

from unittest.mock import patch
from src.history.database import HistoryDatabase
from src.dashboard.cli import AeroDriftDashboard, run_dashboard


def test_dashboard_initialization():
    """Verify default initial state of AeroDriftDashboard."""
    dashboard = AeroDriftDashboard()
    assert dashboard.graph is None
    assert dashboard.resources is None
    assert dashboard.findings == []
    assert isinstance(dashboard.history_db, HistoryDatabase)


def test_dashboard_load_topology_and_drift_detection():
    """Verify that load_cloud_topology and detect_cloud_drift populate findings."""
    dashboard = AeroDriftDashboard()
    dashboard.load_cloud_topology()

    assert dashboard.graph is not None
    assert dashboard.resources is not None
    assert dashboard.graph.number_of_nodes() == 6
    assert dashboard.graph.number_of_edges() == 4

    dashboard.detect_cloud_drift()
    assert len(dashboard.findings) > 0
    assert dashboard.findings[0]["security_group"] == "sg-001"
    assert dashboard.findings[0]["port"] == 22


def test_dashboard_run_lifecycle_execution(tmp_path, monkeypatch):
    """Smoke test to verify run() completes without crashing using an isolated test DB."""
    test_db = tmp_path / "dashboard_test.db"
    test_reports = tmp_path / "test_reports"

    # Patch console.clear to prevent clearing the test terminal
    monkeypatch.setattr("src.dashboard.cli.console.clear", lambda: None)

    dashboard = AeroDriftDashboard()
    dashboard.history_db = HistoryDatabase(database_path=str(test_db))

    with patch(
        "src.history.incident_report.IncidentReportGenerator.__init__",
        lambda self, output_directory="reports": (
            setattr(self, "output_directory", test_reports)
            or test_reports.mkdir(parents=True, exist_ok=True)
        ),
    ):
        dashboard.run()

    assert dashboard.graph is not None
    assert dashboard.resources is not None


def test_run_dashboard_helper(monkeypatch):
    """Verify the top-level run_dashboard helper instantiates and runs the dashboard."""
    called = False

    def mock_run(self):
        nonlocal called
        called = True

    monkeypatch.setattr(AeroDriftDashboard, "run", mock_run)
    run_dashboard()
    assert called is True
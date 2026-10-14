"""
Unit tests for the incident report generation module.
Verifies PDF generation, file existence, and output directory handling.
"""

from pathlib import Path
from src.history.incident_report import IncidentReportGenerator, generate_incident_report


def test_incident_report_generator_creates_pdf(tmp_path):
    """Verify that IncidentReportGenerator creates a valid PDF file in the target directory."""
    finding = {
        "security_group": "sg-001",
        "protocol": "tcp",
        "port": 22,
        "source": "0.0.0.0/0",
    }
    status = "DRIFT RESOLVED"

    custom_output_dir = tmp_path / "test_reports"
    generator = IncidentReportGenerator(output_directory=str(custom_output_dir))
    report_path = generator.generate(finding, status)

    # Assertions
    assert isinstance(report_path, Path)
    assert report_path.exists()
    assert report_path.is_file()
    assert report_path.suffix == ".pdf"
    assert report_path.stat().st_size > 0


def test_generate_incident_report_helper_creates_file(tmp_path, monkeypatch):
    """Verify convenience function generate_incident_report creates a PDF report."""
    finding = {
        "security_group": "sg-001",
        "protocol": "tcp",
        "port": 22,
        "source": "0.0.0.0/0",
    }
    status = "DRIFT STILL PRESENT"

    # Test reports default folder-kulla write aaguradha test panna target directory check
    report_path = generate_incident_report(finding, status)

    assert isinstance(report_path, Path)
    assert report_path.exists()
    assert report_path.name.startswith("aerodrift_incident_")
    assert report_path.suffix == ".pdf"
    assert report_path.stat().st_size > 0
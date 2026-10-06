"""
Unit tests for drift detection module.
"""

import pytest
from datetime import datetime, timezone
from aerodrift.drift_detection import DriftDetector, DriftEvent, DriftType, DriftSeverity
from aerodrift.topology_engine import TopologyEngine


@pytest.mark.unit
class TestDriftDetector:
    """Test cases for DriftDetector class."""

    def test_initialization(self):
        """Test that DriftDetector initializes correctly."""
        detector = DriftDetector()
        assert detector.baseline_graph is None
        assert detector.current_graph is None
        assert detector.detected_events == []
        assert detector.event_counter == 0

    def test_set_baseline(self):
        """Test setting baseline graph."""
        detector = DriftDetector()
        engine = TopologyEngine()
        detector.set_baseline(engine)
        assert detector.baseline_graph is not None

    def test_update_current_state(self):
        """Test updating current state."""
        detector = DriftDetector()
        engine = TopologyEngine()
        detector.update_current_state(engine)
        assert detector.current_graph is not None

    def test_detect_drift_without_baseline(self):
        """Test drift detection without baseline returns empty list."""
        detector = DriftDetector()
        engine = TopologyEngine()
        detector.update_current_state(engine)
        events = detector.detect_drift()
        assert events == []

    def test_create_drift_event(self):
        """Test creating a drift event."""
        detector = DriftDetector()
        detector._create_drift_event(
            drift_type=DriftType.EXPOSED_DATABASE,
            severity=DriftSeverity.CRITICAL,
            resource_id="db-123",
            resource_type="database",
            description="Test database exposed",
            affected_resources=["db-123"],
            remediation_required=True
        )
        assert len(detector.detected_events) == 1
        assert detector.detected_events[0].event_id == "drift-1"
        assert detector.detected_events[0].severity == DriftSeverity.CRITICAL

    def test_get_critical_events(self):
        """Test getting only critical events."""
        detector = DriftDetector()
        detector._create_drift_event(
            drift_type=DriftType.EXPOSED_DATABASE,
            severity=DriftSeverity.CRITICAL,
            resource_id="db-123",
            resource_type="database",
            description="Critical event",
            affected_resources=["db-123"],
            remediation_required=True
        )
        detector._create_drift_event(
            drift_type=DriftType.ADDED_RESOURCE,
            severity=DriftSeverity.INFO,
            resource_id="res-456",
            resource_type="resource",
            description="Info event",
            affected_resources=["res-456"],
            remediation_required=False
        )
        critical_events = detector.get_critical_events()
        assert len(critical_events) == 1
        assert critical_events[0].severity == DriftSeverity.CRITICAL

    def test_get_events_requiring_remediation(self):
        """Test getting events that require remediation."""
        detector = DriftDetector()
        detector._create_drift_event(
            drift_type=DriftType.EXPOSED_DATABASE,
            severity=DriftSeverity.CRITICAL,
            resource_id="db-123",
            resource_type="database",
            description="Critical event",
            affected_resources=["db-123"],
            remediation_required=True
        )
        detector._create_drift_event(
            drift_type=DriftType.ADDED_RESOURCE,
            severity=DriftSeverity.INFO,
            resource_id="res-456",
            resource_type="resource",
            description="Info event",
            affected_resources=["res-456"],
            remediation_required=False
        )
        remediation_events = detector.get_events_requiring_remediation()
        assert len(remediation_events) == 1
        assert remediation_events[0].remediation_required is True

    def test_clear_events(self):
        """Test clearing all detected events."""
        detector = DriftDetector()
        detector._create_drift_event(
            drift_type=DriftType.EXPOSED_DATABASE,
            severity=DriftSeverity.CRITICAL,
            resource_id="db-123",
            resource_type="database",
            description="Test event",
            affected_resources=["db-123"],
            remediation_required=True
        )
        assert len(detector.detected_events) == 1
        
        detector.clear_events()
        assert len(detector.detected_events) == 0
        assert detector.event_counter == 0


@pytest.mark.unit
class TestDriftEvent:
    """Test cases for DriftEvent dataclass."""

    def test_drift_event_creation(self):
        """Test creating a drift event."""
        event = DriftEvent(
            event_id="test-1",
            drift_type=DriftType.EXPOSED_DATABASE,
            severity=DriftSeverity.CRITICAL,
            timestamp=datetime.now(timezone.utc),
            resource_id="db-123",
            resource_type="database",
            description="Test event",
            affected_resources=["db-123"],
            remediation_required=True
        )
        assert event.event_id == "test-1"
        assert event.drift_type == DriftType.EXPOSED_DATABASE
        assert event.severity == DriftSeverity.CRITICAL

    def test_drift_event_to_dict(self):
        """Test converting drift event to dictionary."""
        event = DriftEvent(
            event_id="test-1",
            drift_type=DriftType.EXPOSED_DATABASE,
            severity=DriftSeverity.CRITICAL,
            timestamp=datetime.now(timezone.utc),
            resource_id="db-123",
            resource_type="database",
            description="Test event",
            affected_resources=["db-123"],
            remediation_required=True
        )
        event_dict = event.to_dict()
        assert event_dict['event_id'] == "test-1"
        assert event_dict['drift_type'] == "exposed_database"
        assert event_dict['severity'] == "critical"

"""
Drift Detector: Detects configuration drift by comparing graph states and identifying security issues.
"""

import logging
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import copy

logger = logging.getLogger(__name__)


class DriftSeverity(Enum):
    """Severity levels for drift events."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DriftType(Enum):
    """Types of configuration drift."""
    NEW_PATH_TO_INTERNET = "new_path_to_internet"
    EXPOSED_DATABASE = "exposed_database"
    SECURITY_GROUP_CHANGE = "security_group_change"
    NEW_PUBLIC_INSTANCE = "new_public_instance"
    REMOVED_RESOURCE = "removed_resource"
    ADDED_RESOURCE = "added_resource"


@dataclass
class DriftEvent:
    """Represents a detected drift event."""
    event_id: str
    drift_type: DriftType
    severity: DriftSeverity
    timestamp: datetime
    resource_id: str
    resource_type: str
    description: str
    affected_resources: List[str] = field(default_factory=list)
    remediation_required: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert drift event to dictionary."""
        return {
            'event_id': self.event_id,
            'drift_type': self.drift_type.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'resource_id': self.resource_id,
            'resource_type': self.resource_type,
            'description': self.description,
            'affected_resources': self.affected_resources,
            'remediation_required': self.remediation_required,
            'metadata': self.metadata
        }


class DriftDetector:
    """
    Detects configuration drift by comparing graph states and identifying security issues.
    
    Key capabilities:
    - Detect new paths from Internet to sensitive resources
    - Identify exposed databases
    - Track security group changes
    - Monitor for new public-facing instances
    """
    
    def __init__(self):
        """Initialize the drift detector."""
        self.baseline_graph = None
        self.current_graph = None
        self.detected_events: List[DriftEvent] = []
        self.event_counter = 0
    
    def set_baseline(self, topology_engine):
        """
        Set the baseline graph state for comparison.
        
        Args:
            topology_engine: TopologyEngine instance to use as baseline
        """
        self.baseline_graph = copy.deepcopy(topology_engine)
        logger.info("Baseline graph state set")
    
    def update_current_state(self, topology_engine):
        """
        Update the current graph state for comparison.
        
        Args:
            topology_engine: TopologyEngine instance representing current state
        """
        self.current_graph = copy.deepcopy(topology_engine)
        logger.info("Current graph state updated")
    
    def detect_drift(self) -> List[DriftEvent]:
        """
        Detect drift between baseline and current states.
        
        Returns:
            List of detected drift events
        """
        if not self.baseline_graph or not self.current_graph:
            logger.warning("Cannot detect drift: baseline or current state not set")
            return []
        
        self.detected_events = []
        
        # Detect new paths to Internet
        self._detect_new_internet_paths()
        
        # Detect exposed databases
        self._detect_exposed_databases()
        
        # Detect security group changes
        self._detect_security_group_changes()
        
        # Detect new public instances
        self._detect_new_public_instances()
        
        # Detect resource additions/removals
        self._detect_resource_changes()
        
        logger.info(f"Detected {len(self.detected_events)} drift events")
        return self.detected_events
    
    def _detect_new_internet_paths(self):
        """Detect resources that newly have paths to/from the Internet."""
        if not self.baseline_graph or not self.current_graph:
            return
        
        current_resources = set(self.current_graph.resource_index.keys())
        baseline_resources = set(self.baseline_graph.resource_index.keys())
        
        for resource_id in current_resources:
            # Check if resource can now reach Internet
            current_has_path = self.current_graph.find_path_to_internet(resource_id)
            baseline_has_path = self.baseline_graph.find_path_to_internet(resource_id) if resource_id in baseline_resources else False
            
            if current_has_path and not baseline_has_path:
                resource = self.current_graph.get_resource_details(resource_id)
                if resource and resource.resource_type.value != 'internet':
                    self._create_drift_event(
                        drift_type=DriftType.NEW_PATH_TO_INTERNET,
                        severity=DriftSeverity.HIGH,
                        resource_id=resource_id,
                        resource_type=resource.resource_type.value,
                        description=f"Resource {resource.name} can now reach the Internet",
                        affected_resources=current_has_path,
                        metadata={'path': self.current_graph._describe_path(current_has_path)}
                    )
    
    def _detect_exposed_databases(self):
        """Detect databases that are exposed to the Internet."""
        if not self.current_graph:
            return
        
        exposed_dbs = self.current_graph.find_exposed_databases()
        
        for db_info in exposed_dbs:
            # Check if this is a new exposure
            is_new_exposure = True
            if self.baseline_graph:
                baseline_exposed = [
                    db['resource_id'] for db in self.baseline_graph.find_exposed_databases()
                ]
                if db_info['resource_id'] in baseline_exposed:
                    is_new_exposure = False
            
            if is_new_exposure:
                self._create_drift_event(
                    drift_type=DriftType.EXPOSED_DATABASE,
                    severity=DriftSeverity.CRITICAL,
                    resource_id=db_info['resource_id'],
                    resource_type='database',
                    description=f"Database {db_info['name']} is exposed to the Internet",
                    affected_resources=db_info['path'],
                    remediation_required=True,
                    metadata={
                        'path': db_info['path_description'],
                        'exposure_path': db_info['path']
                    }
                )
    
    def _detect_security_group_changes(self):
        """Detect changes in security group rules."""
        if not self.baseline_graph or not self.current_graph:
            return
        
        current_sgs = {
            rid: resource for rid, resource in self.current_graph.resource_index.items()
            if resource.resource_type.value == 'security_group'
        }
        
        baseline_sgs = {
            rid: resource for rid, resource in self.baseline_graph.resource_index.items()
            if resource.resource_type.value == 'security_group'
        }
        
        for sg_id, current_sg in current_sgs.items():
            if sg_id in baseline_sgs:
                baseline_sg = baseline_sgs[sg_id]
                
                # Compare ingress rules
                current_rules = current_sg.attributes.get('ingress_rules', [])
                baseline_rules = baseline_sg.attributes.get('ingress_rules', [])
                
                new_rules = self._find_new_rules(current_rules, baseline_rules)
                removed_rules = self._find_new_rules(baseline_rules, current_rules)
                
                if new_rules:
                    for rule in new_rules:
                        if rule.get('cidr') == '0.0.0.0/0':
                            self._create_drift_event(
                                drift_type=DriftType.SECURITY_GROUP_CHANGE,
                                severity=DriftSeverity.CRITICAL,
                                resource_id=sg_id,
                                resource_type='security_group',
                                description=f"Security group {current_sg.name} now allows Internet access on port {rule.get('from_port')}",
                                affected_resources=[sg_id],
                                remediation_required=True,
                                metadata={'new_rule': rule}
                            )
                        else:
                            self._create_drift_event(
                                drift_type=DriftType.SECURITY_GROUP_CHANGE,
                                severity=DriftSeverity.MEDIUM,
                                resource_id=sg_id,
                                resource_type='security_group',
                                description=f"Security group {current_sg.name} has new ingress rule",
                                affected_resources=[sg_id],
                                remediation_required=False,
                                metadata={'new_rule': rule}
                            )
    
    def _detect_new_public_instances(self):
        """Detect EC2 instances that now have public IPs."""
        if not self.baseline_graph or not self.current_graph:
            return
        
        current_instances = {
            rid: resource for rid, resource in self.current_graph.resource_index.items()
            if resource.resource_type.value == 'ec2_instance'
        }
        
        baseline_instances = {
            rid: resource for rid, resource in self.baseline_graph.resource_index.items()
            if resource.resource_type.value == 'ec2_instance'
        }
        
        for instance_id, current_instance in current_instances.items():
            if instance_id in baseline_instances:
                baseline_instance = baseline_instances[instance_id]
                
                current_public_ip = current_instance.attributes.get('public_ip')
                baseline_public_ip = baseline_instance.attributes.get('public_ip')
                
                if current_public_ip and not baseline_public_ip:
                    self._create_drift_event(
                        drift_type=DriftType.NEW_PUBLIC_INSTANCE,
                        severity=DriftSeverity.HIGH,
                        resource_id=instance_id,
                        resource_type='ec2_instance',
                        description=f"Instance {current_instance.name} now has public IP: {current_public_ip}",
                        affected_resources=[instance_id],
                        remediation_required=True,
                        metadata={'public_ip': current_public_ip}
                    )
    
    def _detect_resource_changes(self):
        """Detect added or removed resources."""
        if not self.baseline_graph or not self.current_graph:
            return
        
        current_resources = set(self.current_graph.resource_index.keys())
        baseline_resources = set(self.baseline_graph.resource_index.keys())
        
        added_resources = current_resources - baseline_resources
        removed_resources = baseline_resources - current_resources
        
        for resource_id in added_resources:
            resource = self.current_graph.get_resource_details(resource_id)
            if resource and resource.resource_type.value != 'internet':
                self._create_drift_event(
                    drift_type=DriftType.ADDED_RESOURCE,
                    severity=DriftSeverity.INFO,
                    resource_id=resource_id,
                    resource_type=resource.resource_type.value,
                    description=f"New resource added: {resource.name}",
                    affected_resources=[resource_id],
                    remediation_required=False
                )
        
        for resource_id in removed_resources:
            resource = self.baseline_graph.get_resource_details(resource_id)
            if resource and resource.resource_type.value != 'internet':
                self._create_drift_event(
                    drift_type=DriftType.REMOVED_RESOURCE,
                    severity=DriftSeverity.INFO,
                    resource_id=resource_id,
                    resource_type=resource.resource_type.value,
                    description=f"Resource removed: {resource.name}",
                    affected_resources=[resource_id],
                    remediation_required=False
                )
    
    def _find_new_rules(self, current_rules: List[Dict], baseline_rules: List[Dict]) -> List[Dict]:
        """
        Find rules that exist in current but not in baseline.
        
        Args:
            current_rules: Current set of rules
            baseline_rules: Baseline set of rules
            
        Returns:
            List of new rules
        """
        new_rules = []
        for rule in current_rules:
            if rule not in baseline_rules:
                new_rules.append(rule)
        return new_rules
    
    def _create_drift_event(self, drift_type: DriftType, severity: DriftSeverity,
                           resource_id: str, resource_type: str, description: str,
                           affected_resources: List[str], remediation_required: bool = True,
                           metadata: Optional[Dict[str, Any]] = None):
        """
        Create a drift event and add it to the detected events list.
        
        Args:
            drift_type: Type of drift
            severity: Severity level
            resource_id: Affected resource ID
            resource_type: Type of affected resource
            description: Human-readable description
            affected_resources: List of affected resource IDs
            remediation_required: Whether remediation is required
            metadata: Additional metadata
        """
        self.event_counter += 1
        event = DriftEvent(
            event_id=f"drift-{self.event_counter}",
            drift_type=drift_type,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            resource_id=resource_id,
            resource_type=resource_type,
            description=description,
            affected_resources=affected_resources,
            remediation_required=remediation_required,
            metadata=metadata or {}
        )
        self.detected_events.append(event)
        logger.info(f"Drift event created: {event.event_id} - {description}")
    
    def get_critical_events(self) -> List[DriftEvent]:
        """Get only critical and high severity events."""
        return [
            event for event in self.detected_events
            if event.severity in [DriftSeverity.CRITICAL, DriftSeverity.HIGH]
        ]
    
    def get_events_requiring_remediation(self) -> List[DriftEvent]:
        """Get events that require remediation."""
        return [event for event in self.detected_events if event.remediation_required]
    
    def clear_events(self):
        """Clear all detected events."""
        self.detected_events = []
        self.event_counter = 0
        logger.info("Drift events cleared")

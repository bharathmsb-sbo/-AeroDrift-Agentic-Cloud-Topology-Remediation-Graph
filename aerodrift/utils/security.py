"""
Security Enhancements and Auditing for AeroDrift.

This module provides security features including audit logging,
sensitive data handling, and security policy enforcement.
"""

import logging
import hashlib
import json
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
import re

logger = logging.getLogger(__name__)


class SecuritySeverity(Enum):
    """Security severity levels for operations."""
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class SecurityEventType(Enum):
    """Types of security events."""
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION_CHANGE = "configuration_change"
    REMEDIATION_EXECUTION = "remediation_execution"
    TOPOLOGY_EXPORT = "topology_export"


@dataclass
class SecurityEvent:
    """Represents a security event for auditing."""
    event_id: str
    event_type: SecurityEventType
    timestamp: datetime
    user_id: Optional[str]
    resource_id: Optional[str]
    action: str
    details: Dict[str, Any]
    severity: SecuritySeverity = SecuritySeverity.INTERNAL
    ip_address: Optional[str] = None
    success: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert security event to dictionary."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'timestamp': self.timestamp.isoformat(),
            'user_id': self.user_id,
            'resource_id': self.resource_id,
            'action': self.action,
            'details': self.details,
            'severity': self.severity.value,
            'ip_address': self.ip_address,
            'success': self.success
        }


class SensitiveDataHandler:
    """
    Handler for sensitive data with masking and hashing capabilities.
    
    Provides secure handling of sensitive information like credentials,
    API keys, and personal data.
    """
    
    # Patterns for detecting sensitive data
    SENSITIVE_PATTERNS = {
        'aws_access_key': re.compile(r'AKIA[0-9A-Z]{16}'),
        'aws_secret_key': re.compile(r'[0-9a-zA-Z/+]{40}'),
        'api_key': re.compile(r'[a-zA-Z0-9]{32,}'),
        'password': re.compile(r'password["\']?\s*[:=]\s*["\']?[^"\']+', re.IGNORECASE),
        'token': re.compile(r'token["\']?\s*[:=]\s*["\']?[^"\']+', re.IGNORECASE),
        'credit_card': re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'),
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'ip_address': re.compile(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b')
    }
    
    def __init__(self, mask_char: str = '*', mask_length: int = 8):
        """
        Initialize sensitive data handler.
        
        Args:
            mask_char: Character to use for masking
            mask_length: Length of mask for sensitive data
        """
        self.mask_char = mask_char
        self.mask_length = mask_length
    
    def mask_sensitive_data(self, data: str) -> str:
        """
        Mask sensitive data in a string.
        
        Args:
            data: String potentially containing sensitive data
            
        Returns:
            String with sensitive data masked
        """
        masked_data = data
        
        for data_type, pattern in self.SENSITIVE_PATTERNS.items():
            matches = pattern.finditer(masked_data)
            for match in matches:
                sensitive_value = match.group()
                masked_value = self.mask_char * min(len(sensitive_value), self.mask_length)
                masked_data = masked_data.replace(sensitive_value, masked_value)
        
        return masked_data
    
    def mask_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively mask sensitive data in a dictionary.
        
        Args:
            data: Dictionary potentially containing sensitive data
            
        Returns:
            Dictionary with sensitive data masked
        """
        masked = {}
        sensitive_keys = {'password', 'secret', 'key', 'token', 'credential', 'api_key'}
        
        for key, value in data.items():
            if isinstance(value, str):
                if any(sensitive in key.lower() for sensitive in sensitive_keys):
                    masked[key] = self.mask_char * min(len(value), self.mask_length)
                else:
                    masked[key] = self.mask_sensitive_data(value)
            elif isinstance(value, dict):
                masked[key] = self.mask_dict(value)
            elif isinstance(value, list):
                masked[key] = [
                    self.mask_dict(item) if isinstance(item, dict) else 
                    self.mask_sensitive_data(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                masked[key] = value
        
        return masked
    
    def hash_sensitive_value(self, value: str) -> str:
        """
        Hash a sensitive value for comparison without storing the actual value.
        
        Args:
            value: Sensitive value to hash
            
        Returns:
            Hashed value
        """
        return hashlib.sha256(value.encode()).hexdigest()
    
    def redact_log_message(self, message: str) -> str:
        """
        Redact sensitive information from log messages.
        
        Args:
            message: Log message to redact
            
        Returns:
            Redacted log message
        """
        return self.mask_sensitive_data(message)


class SecurityAuditor:
    """
    Security auditor for tracking and logging security events.
    
    Provides comprehensive audit logging for all security-relevant operations.
    """
    
    def __init__(self, log_file: str = "security_audit.log"):
        """
        Initialize security auditor.
        
        Args:
            log_file: Path to security audit log file
        """
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.sensitive_handler = SensitiveDataHandler()
        self._event_counter = 0
    
    def log_event(self, event: SecurityEvent):
        """
        Log a security event to the audit log.
        
        Args:
            event: Security event to log
        """
        self._event_counter += 1
        
        # Mask sensitive data in event details
        masked_details = self.sensitive_handler.mask_dict(event.details)
        event.details = masked_details
        
        # Convert to JSON and write to log
        event_dict = event.to_dict()
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(event_dict) + '\n')
            
            logger.info(f"Security event logged: {event.event_type.value} - {event.action}")
        except Exception as e:
            logger.error(f"Failed to write security audit log: {e}")
    
    def create_event(
        self,
        event_type: SecurityEventType,
        action: str,
        user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        severity: SecuritySeverity = SecuritySeverity.INTERNAL,
        success: bool = True
    ) -> SecurityEvent:
        """
        Create a security event.
        
        Args:
            event_type: Type of security event
            action: Action performed
            user_id: User ID performing the action
            resource_id: Resource ID affected
            details: Additional event details
            severity: Security level of the event
            success: Whether the action was successful
            
        Returns:
            SecurityEvent object
        """
        self._event_counter += 1
        
        return SecurityEvent(
            event_id=f"sec-{self._event_counter}",
            event_type=event_type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            resource_id=resource_id,
            action=action,
            details=details or {},
            severity=severity,
            success=success
        )
    
    def get_recent_events(self, limit: int = 100) -> List[SecurityEvent]:
        """
        Get recent security events from the audit log.
        
        Args:
            limit: Maximum number of events to return
            
        Returns:
            List of recent security events
        """
        events = []
        
        try:
            with open(self.log_file, 'r') as f:
                lines = f.readlines()
                
            for line in lines[-limit:]:
                try:
                    event_data = json.loads(line.strip())
                    event = SecurityEvent(
                        event_id=event_data['event_id'],
                        event_type=SecurityEventType(event_data['event_type']),
                        timestamp=datetime.fromisoformat(event_data['timestamp']),
                        user_id=event_data.get('user_id'),
                        resource_id=event_data.get('resource_id'),
                        action=event_data['action'],
                        details=event_data.get('details', {}),
                        severity=SecuritySeverity(event_data.get('severity', 'internal')),
                        ip_address=event_data.get('ip_address'),
                        success=event_data.get('success', True)
                    )
                    events.append(event)
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.warning(f"Failed to parse audit log entry: {e}")
        
        except FileNotFoundError:
            logger.info("No security audit log found")
        
        return events
    
    def get_security_summary(self) -> Dict[str, Any]:
        """
        Get a summary of security events.
        
        Returns:
            Dictionary with security statistics
        """
        events = self.get_recent_events(limit=1000)
        
        summary = {
            'total_events': len(events),
            'successful_events': sum(1 for e in events if e.success),
            'failed_events': sum(1 for e in events if not e.success),
            'events_by_type': {},
            'events_by_severity': {},
            'recent_critical_events': []
        }
        
        for event in events:
            # Count by type
            event_type = event.event_type.value
            summary['events_by_type'][event_type] = summary['events_by_type'].get(event_type, 0) + 1
            
            # Count by severity
            severity = event.severity.value
            summary['events_by_severity'][severity] = summary['events_by_severity'].get(severity, 0) + 1
            
            # Track critical events
            if event.severity == SecuritySeverity.RESTRICTED and not event.success:
                summary['recent_critical_events'].append({
                    'event_id': event.event_id,
                    'timestamp': event.timestamp.isoformat(),
                    'action': event.action,
                    'resource_id': event.resource_id
                })
        
        return summary


class SecurityPolicy:
    """
    Security policy enforcement for AeroDrift operations.
    
    Defines and enforces security policies for various operations.
    """
    
    def __init__(self):
        """Initialize security policy with default rules."""
        self.policies = {
            'auto_remediation': {
                'allowed': False,
                'require_approval': True,
                'allowed_severities': ['critical', 'high'],
                'max_parallel_remediations': 1
            },
            'topology_export': {
                'allowed': True,
                'require_authorization': False,
                'allowed_formats': ['json', 'gexf'],
                'max_export_size_mb': 10
            },
            'data_retention': {
                'max_days': 90,
                'min_encryption_level': 'AES256',
                'require_audit_log': True
            },
            'api_access': {
                'rate_limit_per_minute': 100,
                'require_authentication': True,
                'allowed_regions': ['us-east-1', 'us-west-2', 'eu-west-1']
            }
        }
    
    def check_policy(self, policy_name: str, **kwargs) -> tuple[bool, List[str]]:
        """
        Check if an operation complies with security policy.
        
        Args:
            policy_name: Name of the policy to check
            **kwargs: Policy-specific parameters
            
        Returns:
            Tuple of (is_compliant, list of violations)
        """
        if policy_name not in self.policies:
            return False, [f"Unknown policy: {policy_name}"]
        
        policy = self.policies[policy_name]
        violations = []
        
        if policy_name == 'auto_remediation':
            if not policy['allowed']:
                violations.append("Auto-remediation is not allowed")
            
            if kwargs.get('severity') not in policy['allowed_severities']:
                violations.append(f"Severity {kwargs.get('severity')} not allowed for auto-remediation")
            
            if kwargs.get('parallel_count', 1) > policy['max_parallel_remediations']:
                violations.append(f"Exceeds maximum parallel remediations: {policy['max_parallel_remediations']}")
        
        elif policy_name == 'topology_export':
            if not policy['allowed']:
                violations.append("Topology export is not allowed")
            
            if kwargs.get('format') not in policy['allowed_formats']:
                violations.append(f"Format {kwargs.get('format')} not allowed for export")
            
            if kwargs.get('size_mb', 0) > policy['max_export_size_mb']:
                violations.append(f"Export size exceeds maximum: {policy['max_export_size_mb']}MB")
        
        return len(violations) == 0, violations
    
    def update_policy(self, policy_name: str, policy_config: Dict[str, Any]):
        """
        Update a security policy.
        
        Args:
            policy_name: Name of the policy to update
            policy_config: New policy configuration
        """
        if policy_name in self.policies:
            self.policies[policy_name].update(policy_config)
            logger.info(f"Security policy '{policy_name}' updated")
        else:
            self.policies[policy_name] = policy_config
            logger.info(f"New security policy '{policy_name}' added")
    
    def get_policy(self, policy_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a security policy configuration.
        
        Args:
            policy_name: Name of the policy
            
        Returns:
            Policy configuration or None if not found
        """
        return self.policies.get(policy_name)


# Global security auditor instance
global_security_auditor = SecurityAuditor()
global_security_policy = SecurityPolicy()
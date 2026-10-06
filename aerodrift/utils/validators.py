"""
Input Validation and Sanitization Utilities for AeroDrift.

This module provides comprehensive input validation, data sanitization,
and security checks for all user inputs and external data.
"""

import re
import logging
from typing import Any, List, Optional, Dict, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


class ValidationSecurityLevel(Enum):
    """Security levels for validation."""
    STRICT = "strict"
    MODERATE = "moderate"
    LENIENT = "lenient"


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    sanitized_value: Any = None
    
    def add_error(self, error: str):
        """Add an error to the validation result."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning to the validation result."""
        self.warnings.append(warning)


class InputValidator:
    """
    Comprehensive input validation and sanitization.
    
    Validates and sanitizes user inputs, configuration values,
    and external data to prevent security issues and ensure data integrity.
    """
    
    # Patterns for validation
    AWS_RESOURCE_ID_PATTERN = re.compile(r'^[a-zA-Z0-9\-]+$')
    CIDR_PATTERN = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{1,2}$')
    REGION_PATTERN = re.compile(r'^[a-z]{2}-[a-z]+-\d{1}$')
    TAG_KEY_PATTERN = re.compile(r'^[a-zA-Z0-9\s_\-:]+$')
    TAG_VALUE_PATTERN = re.compile(r'^[a-zA-Z0-9\s_\-:.@/]+$')
    
    # Security constraints
    MAX_STRING_LENGTH = 1024
    MAX_ARRAY_LENGTH = 1000
    MAX_NESTING_DEPTH = 10
    
    def __init__(self, security_level: ValidationSecurityLevel = ValidationSecurityLevel.MODERATE):
        """
        Initialize the validator with specified security level.
        
        Args:
            security_level: Security strictness level
        """
        self.security_level = security_level
    
    def validate_aws_resource_id(self, resource_id: str) -> ValidationResult:
        """
        Validate AWS resource ID format.
        
        Args:
            resource_id: AWS resource ID to validate
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not resource_id:
            result.add_error("Resource ID cannot be empty")
            return result
        
        if len(resource_id) > self.MAX_STRING_LENGTH:
            result.add_error(f"Resource ID exceeds maximum length of {self.MAX_STRING_LENGTH}")
        
        if not self.AWS_RESOURCE_ID_PATTERN.match(resource_id):
            result.add_error(f"Invalid AWS resource ID format: {resource_id}")
        
        return result
    
    def validate_cidr(self, cidr: str) -> ValidationResult:
        """
        Validate CIDR notation.
        
        Args:
            cidr: CIDR string to validate
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not cidr:
            result.add_error("CIDR cannot be empty")
            return result
        
        if not self.CIDR_PATTERN.match(cidr):
            result.add_error(f"Invalid CIDR format: {cidr}")
            return result
        
        # Validate IP octets
        ip_part = cidr.split('/')[0]
        octets = ip_part.split('.')
        for octet in octets:
            try:
                val = int(octet)
                if val < 0 or val > 255:
                    result.add_error(f"Invalid IP octet: {octet}")
            except ValueError:
                result.add_error(f"Invalid IP octet: {octet}")
        
        # Validate prefix length
        try:
            prefix = int(cidr.split('/')[1])
            if prefix < 0 or prefix > 32:
                result.add_error(f"Invalid CIDR prefix length: {prefix}")
        except (ValueError, IndexError):
            result.add_error("Invalid CIDR prefix length")
        
        return result
    
    def validate_aws_region(self, region: str) -> ValidationResult:
        """
        Validate AWS region format.
        
        Args:
            region: AWS region string to validate
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not region:
            result.add_error("Region cannot be empty")
            return result
        
        if not self.REGION_PATTERN.match(region):
            result.add_error(f"Invalid AWS region format: {region}")
        
        return result
    
    def validate_tag(self, key: str, value: str) -> ValidationResult:
        """
        Validate AWS tag key and value.
        
        Args:
            key: Tag key
            value: Tag value
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not key:
            result.add_error("Tag key cannot be empty")
            return result
        
        if len(key) > 128:
            result.add_error("Tag key exceeds maximum length of 128 characters")
        
        if not self.TAG_KEY_PATTERN.match(key):
            result.add_error(f"Invalid tag key format: {key}")
        
        if value and len(value) > 256:
            result.add_error("Tag value exceeds maximum length of 256 characters")
        
        if value and not self.TAG_VALUE_PATTERN.match(value):
            result.add_error(f"Invalid tag value format: {value}")
        
        return result
    
    def sanitize_string(self, input_string: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize string input by removing dangerous characters and limiting length.
        
        Args:
            input_string: String to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not input_string:
            return ""
        
        # Remove null bytes and other control characters
        sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', input_string)
        
        # Limit length
        max_len = max_length or self.MAX_STRING_LENGTH
        if len(sanitized) > max_len:
            sanitized = sanitized[:max_len]
            logger.warning(f"String truncated to {max_len} characters")
        
        return sanitized.strip()
    
    def validate_config_value(self, key: str, value: Any, expected_type: type) -> ValidationResult:
        """
        Validate configuration value against expected type.
        
        Args:
            key: Configuration key
            value: Configuration value
            expected_type: Expected type
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if value is None:
            result.add_warning(f"Configuration key '{key}' is None")
            return result
        
        if not isinstance(value, expected_type):
            result.add_error(
                f"Configuration key '{key}' has wrong type. "
                f"Expected {expected_type.__name__}, got {type(value).__name__}"
            )
        
        return result
    
    def validate_json_structure(self, data: Dict, required_keys: List[str]) -> ValidationResult:
        """
        Validate JSON structure has required keys.
        
        Args:
            data: Dictionary to validate
            required_keys: List of required keys
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not isinstance(data, dict):
            result.add_error("Input must be a dictionary")
            return result
        
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            result.add_error(f"Missing required keys: {', '.join(missing_keys)}")
        
        return result
    
    def validate_port_number(self, port: int) -> ValidationResult:
        """
        Validate port number is in valid range.
        
        Args:
            port: Port number to validate
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not isinstance(port, int):
            result.add_error("Port must be an integer")
            return result
        
        if port < 1 or port > 65535:
            result.add_error(f"Port number {port} is out of valid range (1-65535)")
        
        return result
    
    def validate_file_path(self, file_path: str) -> ValidationResult:
        """
        Validate file path for security and format.
        
        Args:
            file_path: File path to validate
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        if not file_path:
            result.add_error("File path cannot be empty")
            return result
        
        # Check for path traversal attempts
        if '..' in file_path:
            result.add_error("File path contains directory traversal attempt")
        
        # Check for absolute paths in strict mode
        if self.security_level == ValidationSecurityLevel.STRICT and file_path.startswith('/'):
            result.add_warning("Absolute file path detected")
        
        # Check length
        if len(file_path) > 4096:
            result.add_error("File path exceeds maximum length")
        
        return result
    
    def sanitize_dict(self, data: Dict, max_depth: int = MAX_NESTING_DEPTH) -> Dict:
        """
        Recursively sanitize dictionary values.
        
        Args:
            data: Dictionary to sanitize
            max_depth: Maximum nesting depth
            
        Returns:
            Sanitized dictionary
        """
        if max_depth <= 0:
            logger.warning("Maximum nesting depth exceeded during sanitization")
            return {}
        
        sanitized = {}
        for key, value in data.items():
            # Sanitize keys
            safe_key = self.sanitize_string(str(key)) if isinstance(key, str) else key
            
            # Sanitize values based on type
            if isinstance(value, str):
                sanitized[safe_key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[safe_key] = self.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[safe_key] = [
                    self.sanitize_dict(item, max_depth - 1) if isinstance(item, dict) else item
                    for item in value[:self.MAX_ARRAY_LENGTH]
                ]
            else:
                sanitized[safe_key] = value
        
        return sanitized
    
    def validate_drift_event(self, event_data: Dict) -> ValidationResult:
        """
        Validate drift event data structure.
        
        Args:
            event_data: Drift event dictionary to validate
            
        Returns:
            ValidationResult with validation status
        """
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        required_fields = ['event_id', 'drift_type', 'severity', 'timestamp', 'resource_id']
        structure_result = self.validate_json_structure(event_data, required_fields)
        
        if not structure_result.is_valid:
            result.errors.extend(structure_result.errors)
            result.is_valid = False
        
        # Validate event_id format
        if 'event_id' in event_data:
            event_id_result = self.validate_aws_resource_id(event_data['event_id'])
            if not event_id_result.is_valid:
                result.errors.extend(event_id_result.errors)
                result.is_valid = False
        
        # Validate resource_id format
        if 'resource_id' in event_data:
            resource_id_result = self.validate_aws_resource_id(event_data['resource_id'])
            if not resource_id_result.is_valid:
                result.errors.extend(resource_id_result.errors)
                result.is_valid = False
        
        return result


def validate_all_inputs(data: Dict, validator: Optional[InputValidator] = None) -> ValidationResult:
    """
    Validate all inputs in a data dictionary.
    
    Args:
        data: Dictionary containing all inputs to validate
        validator: InputValidator instance (creates default if None)
        
    Returns:
            ValidationResult with overall validation status
    """
    if validator is None:
        validator = InputValidator()
    
    result = ValidationResult(is_valid=True, errors=[], warnings=[])
    
    for key, value in data.items():
        try:
            if key == 'resource_id' and isinstance(value, str):
                id_result = validator.validate_aws_resource_id(value)
                if not id_result.is_valid:
                    result.errors.extend(id_result.errors)
                    result.is_valid = False
            
            elif key == 'cidr' and isinstance(value, str):
                cidr_result = validator.validate_cidr(value)
                if not cidr_result.is_valid:
                    result.errors.extend(cidr_result.errors)
                    result.is_valid = False
            
            elif key == 'region' and isinstance(value, str):
                region_result = validator.validate_aws_region(value)
                if not region_result.is_valid:
                    result.errors.extend(region_result.errors)
                    result.is_valid = False
            
            elif key == 'port' and isinstance(value, int):
                port_result = validator.validate_port_number(value)
                if not port_result.is_valid:
                    result.errors.extend(port_result.errors)
                    result.is_valid = False
            
        except Exception as e:
            logger.error(f"Error validating field '{key}': {e}")
            result.add_error(f"Validation error for field '{key}': {str(e)}")
            result.is_valid = False
    
    return result
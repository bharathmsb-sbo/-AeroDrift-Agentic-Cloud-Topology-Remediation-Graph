"""
Unit tests for input validation utilities.
"""

import pytest
from aerodrift.utils.validators import (
    InputValidator, ValidationResult, ValidationSecurityLevel,
    ValidationError, validate_all_inputs
)


class TestInputValidator:
    """Test cases for InputValidator class."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return InputValidator(security_level=ValidationSecurityLevel.MODERATE)
    
    def test_validate_aws_resource_id_valid(self, validator):
        """Test validation of valid AWS resource IDs."""
        result = validator.validate_aws_resource_id("vpc-12345678")
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_aws_resource_id_invalid(self, validator):
        """Test validation of invalid AWS resource IDs."""
        result = validator.validate_aws_resource_id("invalid@id!")
        assert not result.is_valid
        assert len(result.errors) > 0
    
    def test_validate_aws_resource_id_empty(self, validator):
        """Test validation of empty resource ID."""
        result = validator.validate_aws_resource_id("")
        assert not result.is_valid
        assert "cannot be empty" in result.errors[0]
    
    def test_validate_aws_resource_id_too_long(self, validator):
        """Test validation of resource ID exceeding max length."""
        long_id = "x" * 2000
        result = validator.validate_aws_resource_id(long_id)
        assert not result.is_valid
        assert "exceeds maximum length" in result.errors[0]
    
    def test_validate_cidr_valid(self, validator):
        """Test validation of valid CIDR notation."""
        result = validator.validate_cidr("10.0.0.0/24")
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_cidr_invalid_format(self, validator):
        """Test validation of invalid CIDR format."""
        result = validator.validate_cidr("invalid-cidr")
        assert not result.is_valid
        assert "Invalid CIDR format" in result.errors[0]
    
    def test_validate_cidr_invalid_octets(self, validator):
        """Test validation of CIDR with invalid octets."""
        result = validator.validate_cidr("300.0.0.0/24")
        assert not result.is_valid
        assert "Invalid IP octet" in result.errors[0]
    
    def test_validate_cidr_invalid_prefix(self, validator):
        """Test validation of CIDR with invalid prefix."""
        result = validator.validate_cidr("10.0.0.0/33")
        assert not result.is_valid
        assert "Invalid CIDR prefix length" in result.errors[0]
    
    def test_validate_aws_region_valid(self, validator):
        """Test validation of valid AWS regions."""
        result = validator.validate_aws_region("us-east-1")
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_aws_region_invalid(self, validator):
        """Test validation of invalid AWS regions."""
        result = validator.validate_aws_region("invalid-region")
        assert not result.is_valid
        assert "Invalid AWS region format" in result.errors[0]
    
    def test_validate_tag_valid(self, validator):
        """Test validation of valid AWS tags."""
        result = validator.validate_tag("Environment", "production")
        assert result.is_valid
        assert len(result.errors) == 0
    
    def test_validate_tag_empty_key(self, validator):
        """Test validation of tag with empty key."""
        result = validator.validate_tag("", "value")
        assert not result.is_valid
        assert "cannot be empty" in result.errors[0]
    
    def test_validate_tag_key_too_long(self, validator):
        """Test validation of tag key exceeding max length."""
        long_key = "x" * 200
        result = validator.validate_tag(long_key, "value")
        assert not result.is_valid
        assert "exceeds maximum length" in result.errors[0]
    
    def test_sanitize_string_normal(self, validator):
        """Test sanitization of normal string."""
        result = validator.sanitize_string("normal string")
        assert result == "normal string"
    
    def test_sanitize_string_control_chars(self, validator):
        """Test sanitization of string with control characters."""
        result = validator.sanitize_string("test\x00string")
        assert "\x00" not in result
    
    def test_sanitize_string_truncation(self, validator):
        """Test string truncation."""
        long_string = "x" * 2000
        result = validator.sanitize_string(long_string, max_length=100)
        assert len(result) <= 100
    
    def test_validate_config_value_valid(self, validator):
        """Test validation of valid config value."""
        result = validator.validate_config_value("interval", 60, int)
        assert result.is_valid
    
    def test_validate_config_value_invalid_type(self, validator):
        """Test validation of config value with wrong type."""
        result = validator.validate_config_value("interval", "60", int)
        assert not result.is_valid
        assert "wrong type" in result.errors[0]
    
    def test_validate_json_structure_valid(self, validator):
        """Test validation of valid JSON structure."""
        data = {"key1": "value1", "key2": "value2"}
        result = validator.validate_json_structure(data, ["key1"])
        assert result.is_valid
    
    def test_validate_json_structure_missing_keys(self, validator):
        """Test validation of JSON structure with missing keys."""
        data = {"key1": "value1"}
        result = validator.validate_json_structure(data, ["key1", "key2"])
        assert not result.is_valid
        assert "Missing required keys" in result.errors[0]
    
    def test_validate_port_number_valid(self, validator):
        """Test validation of valid port numbers."""
        result = validator.validate_port_number(8080)
        assert result.is_valid
    
    def test_validate_port_number_invalid_range(self, validator):
        """Test validation of port number out of range."""
        result = validator.validate_port_number(70000)
        assert not result.is_valid
        assert "out of valid range" in result.errors[0]
    
    def test_validate_port_number_invalid_type(self, validator):
        """Test validation of port number with wrong type."""
        result = validator.validate_port_number("8080")
        assert not result.is_valid
        assert "must be an integer" in result.errors[0]
    
    def test_validate_file_path_valid(self, validator):
        """Test validation of valid file path."""
        result = validator.validate_file_path("config.json")
        assert result.is_valid
    
    def test_validate_file_path_traversal(self, validator):
        """Test validation of file path with traversal attempt."""
        result = validator.validate_file_path("../../../etc/passwd")
        assert not result.is_valid
        assert "directory traversal" in result.errors[0]
    
    def test_sanitize_dict_simple(self, validator):
        """Test sanitization of simple dictionary."""
        data = {"key": "value", "number": 42}
        result = validator.sanitize_dict(data)
        assert result["key"] == "value"
        assert result["number"] == 42
    
    def test_sanitize_dict_nested(self, validator):
        """Test sanitization of nested dictionary."""
        data = {"outer": {"inner": "value"}}
        result = validator.sanitize_dict(data)
        assert result["outer"]["inner"] == "value"
    
    def test_sanitize_dict_with_list(self, validator):
        """Test sanitization of dictionary with list values."""
        data = {"items": ["item1", "item2"]}
        result = validator.sanitize_dict(data)
        assert result["items"] == ["item1", "item2"]
    
    def test_validate_drift_event_valid(self, validator):
        """Test validation of valid drift event."""
        event_data = {
            "event_id": "drift-1",
            "drift_type": "exposed_database",
            "severity": "critical",
            "timestamp": "2024-01-01T00:00:00Z",
            "resource_id": "resource-123"
        }
        result = validator.validate_drift_event(event_data)
        assert result.is_valid
    
    def test_validate_drift_event_missing_fields(self, validator):
        """Test validation of drift event with missing fields."""
        event_data = {"event_id": "drift-1"}
        result = validator.validate_drift_event(event_data)
        assert not result.is_valid


class TestValidateAllInputs:
    """Test cases for validate_all_inputs function."""
    
    @pytest.fixture
    def validator(self):
        """Create a validator instance for testing."""
        return InputValidator(security_level=ValidationSecurityLevel.MODERATE)
    
    def test_validate_all_inputs_valid(self, validator):
        """Test validation of all valid inputs."""
        data = {
            "resource_id": "vpc-12345678",
            "cidr": "10.0.0.0/24",
            "region": "us-east-1",
            "port": 8080
        }
        result = validate_all_inputs(data, validator)
        assert result.is_valid
    
    def test_validate_all_inputs_invalid_cidr(self, validator):
        """Test validation with invalid CIDR."""
        data = {
            "resource_id": "vpc-12345678",
            "cidr": "invalid",
            "region": "us-east-1"
        }
        result = validate_all_inputs(data, validator)
        assert not result.is_valid
    
    def test_validate_all_inputs_multiple_errors(self, validator):
        """Test validation with multiple errors."""
        data = {
            "resource_id": "invalid@id!",
            "cidr": "invalid",
            "region": "invalid",
            "port": 99999
        }
        result = validate_all_inputs(data, validator)
        assert not result.is_valid
        assert len(result.errors) >= 2
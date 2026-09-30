"""
Unit tests for configuration management.
"""

import pytest
import json
import tempfile
from pathlib import Path
from aerodrift.utils.config import Config


class TestConfig:
    """Test cases for Config class."""
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        config = Config()
        assert config.aws_region == "us-east-1"
        assert config.aws_use_mock == True
        assert config.polling_interval == 60
        assert config.auto_remediate == False
        assert config.log_level == "INFO"
    
    def test_from_file_not_exists(self):
        """Test loading config from non-existent file."""
        config = Config.from_file("nonexistent.json")
        assert config.aws_region == "us-east-1"  # Should use defaults
    
    def test_from_file_valid(self):
        """Test loading config from valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            config_data = {
                "aws_region": "us-west-2",
                "aws_use_mock": False,
                "polling_interval": 120
            }
            json.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = Config.from_file(temp_path)
            assert config.aws_region == "us-west-2"
            assert config.aws_use_mock == False
            assert config.polling_interval == 120
        finally:
            Path(temp_path).unlink()
    
    def test_from_file_invalid_json(self):
        """Test loading config from invalid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError):
                Config.from_file(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_to_file(self):
        """Test saving config to file."""
        config = Config(aws_region="eu-west-1", polling_interval=90)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            config.to_file(temp_path)
            
            # Verify file was created and contains correct data
            with open(temp_path, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data["aws_region"] == "eu-west-1"
            assert loaded_data["polling_interval"] == 90
        finally:
            Path(temp_path).unlink()
    
    def test_override_from_env(self, monkeypatch):
        """Test overriding config from environment variables."""
        monkeypatch.setenv("AWS_REGION", "ap-southeast-1")
        monkeypatch.setenv("POLLING_INTERVAL", "300")
        monkeypatch.setenv("AUTO_REMEDIATE", "true")
        
        config = Config()
        config.override_from_env()
        
        assert config.aws_region == "ap-southeast-1"
        assert config.polling_interval == 300
        assert config.auto_remediate == True
    
    def test_validate_valid_config(self):
        """Test validation of valid configuration."""
        config = Config(
            aws_use_mock=True,
            polling_interval=60,
            db_retention_days=30,
            remediation_timeout=30,
            log_level="INFO"
        )
        assert config.validate() == True
    
    def test_validate_missing_credentials(self):
        """Test validation fails when AWS credentials missing and not using mock."""
        config = Config(
            aws_use_mock=False,
            aws_access_key_id=None,
            aws_secret_access_key=None
        )
        assert config.validate() == False
    
    def test_validate_invalid_polling_interval(self):
        """Test validation fails with invalid polling interval."""
        config = Config(polling_interval=0)
        assert config.validate() == False
    
    def test_validate_invalid_log_level(self):
        """Test validation fails with invalid log level."""
        config = Config(log_level="INVALID")
        assert config.validate() == False
    
    def test_validate_invalid_retention_days(self):
        """Test validation fails with invalid retention days."""
        config = Config(db_retention_days=0)
        assert config.validate() == False
    
    def test_validate_invalid_remediation_timeout(self):
        """Test validation fails with invalid remediation timeout."""
        config = Config(remediation_timeout=0)
        assert config.validate() == False
    
    def test_setup_logging(self):
        """Test logging setup."""
        config = Config(log_level="DEBUG")
        config.setup_logging()
        # If no exception is raised, test passes
        assert True
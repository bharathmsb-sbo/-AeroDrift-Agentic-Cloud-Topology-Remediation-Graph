"""
Configuration management for AeroDrift.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Configuration settings for AeroDrift."""
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_use_mock: bool = True
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    
    # Polling Configuration
    polling_interval: int = 60
    polling_enabled: bool = True
    
    # Database Configuration
    db_path: str = "aerodrift_states.db"
    db_retention_days: int = 30
    
    # Remediation Configuration
    auto_remediate: bool = False
    remediation_timeout: int = 30
    require_approval: bool = True
    
    # Logging Configuration
    log_level: str = "INFO"
    log_file: Optional[str] = "aerodrift.log"
    
    # Dashboard Configuration
    dashboard_refresh_rate: float = 1.0
    enable_live_monitoring: bool = False
    
    # Notification Configuration
    enable_notifications: bool = False
    notification_webhook: Optional[str] = None
    
    # Advanced Configuration
    max_execution_history: int = 100
    snapshot_batch_size: int = 10
    
    @classmethod
    def from_file(cls, config_path: str = "aerodrift_config.json") -> 'Config':
        """
        Load configuration from a JSON file with validation.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Config object
        """
        config_file = Path(config_path)
        
        if not config_file.exists():
            logger.info(f"Config file not found at {config_path}, using defaults")
            return cls()
        
        try:
            with open(config_file, 'r') as f:
                config_data = json.load(f)
            
            # Validate configuration structure
            validation_result = cls._validate_config_structure(config_data)
            if not validation_result['is_valid']:
                logger.error(f"Configuration validation failed: {validation_result['errors']}")
                raise ValueError(f"Invalid configuration: {validation_result['errors']}")
            
            config = cls(**config_data)
            logger.info(f"Configuration loaded from {config_path}")
            return config
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {config_path}: {e}")
            raise ValueError(f"Invalid JSON in configuration file: {e}")
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
            raise
    
    def to_file(self, config_path: str = "aerodrift_config.json"):
        """
        Save configuration to a JSON file.
        
        Args:
            config_path: Path to save configuration file
        """
        config_file = Path(config_path)
        
        try:
            config_data = {
                'aws_region': self.aws_region,
                'aws_use_mock': self.aws_use_mock,
                'aws_access_key_id': self.aws_access_key_id,
                'aws_secret_access_key': self.aws_secret_access_key,
                'polling_interval': self.polling_interval,
                'polling_enabled': self.polling_enabled,
                'db_path': self.db_path,
                'db_retention_days': self.db_retention_days,
                'auto_remediate': self.auto_remediate,
                'remediation_timeout': self.remediation_timeout,
                'require_approval': self.require_approval,
                'log_level': self.log_level,
                'log_file': self.log_file,
                'dashboard_refresh_rate': self.dashboard_refresh_rate,
                'enable_live_monitoring': self.enable_live_monitoring,
                'enable_notifications': self.enable_notifications,
                'notification_webhook': self.notification_webhook,
                'max_execution_history': self.max_execution_history,
                'snapshot_batch_size': self.snapshot_batch_size
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info(f"Configuration saved to {config_path}")
            
        except Exception as e:
            logger.error(f"Error saving config to {config_path}: {e}")
    
    def override_from_env(self):
        """Override configuration values from environment variables."""
        env_mappings = {
            'AWS_REGION': 'aws_region',
            'AWS_USE_MOCK': 'aws_use_mock',
            'AWS_ACCESS_KEY_ID': 'aws_access_key_id',
            'AWS_SECRET_ACCESS_KEY': 'aws_secret_access_key',
            'POLLING_INTERVAL': 'polling_interval',
            'DB_PATH': 'db_path',
            'AUTO_REMEDIATE': 'auto_remediate',
            'LOG_LEVEL': 'log_level',
            'LOG_FILE': 'log_file'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.environ.get(env_var)
            if env_value is not None:
                # Convert string to appropriate type
                if config_key in ['aws_use_mock', 'polling_enabled', 'auto_remediate', 
                                  'require_approval', 'enable_notifications', 'enable_live_monitoring']:
                    env_value = env_value.lower() in ('true', '1', 'yes')
                elif config_key in ['polling_interval', 'db_retention_days', 'remediation_timeout',
                                    'max_execution_history', 'snapshot_batch_size']:
                    env_value = int(env_value)
                elif config_key in ['dashboard_refresh_rate']:
                    env_value = float(env_value)
                
                setattr(self, config_key, env_value)
                logger.info(f"Overrode {config_key} from environment variable {env_var}")
    
    @classmethod
    def _validate_config_structure(cls, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration file structure and values.
        
        Args:
            config_data: Configuration dictionary to validate
            
        Returns:
            Dictionary with validation results
        """
        result = {'is_valid': True, 'errors': [], 'warnings': []}
        
        # Check required fields
        optional_fields = [
            'aws_region', 'aws_use_mock', 'aws_access_key_id', 'aws_secret_access_key',
            'polling_interval', 'polling_enabled', 'db_path', 'db_retention_days',
            'auto_remediate', 'remediation_timeout', 'require_approval',
            'log_level', 'log_file', 'dashboard_refresh_rate', 'enable_live_monitoring',
            'enable_notifications', 'notification_webhook', 'max_execution_history',
            'snapshot_batch_size'
        ]
        
        # Validate field types
        type_validations = {
            'aws_region': str,
            'aws_use_mock': bool,
            'aws_access_key_id': (str, type(None)),
            'aws_secret_access_key': (str, type(None)),
            'polling_interval': int,
            'polling_enabled': bool,
            'db_path': str,
            'db_retention_days': int,
            'auto_remediate': bool,
            'remediation_timeout': int,
            'require_approval': bool,
            'log_level': str,
            'log_file': (str, type(None)),
            'dashboard_refresh_rate': float,
            'enable_live_monitoring': bool,
            'enable_notifications': bool,
            'notification_webhook': (str, type(None)),
            'max_execution_history': int,
            'snapshot_batch_size': int
        }
        
        for field, expected_type in type_validations.items():
            if field in config_data:
                if not isinstance(config_data[field], expected_type):
                    result['errors'].append(
                        f"Field '{field}' has invalid type. Expected {expected_type}, got {type(config_data[field])}"
                    )
                    result['is_valid'] = False
        
        # Validate specific field values
        if 'aws_region' in config_data:
            region = config_data['aws_region']
            if not isinstance(region, str) or not region:
                result['errors'].append("AWS region must be a non-empty string")
                result['is_valid'] = False
        
        if 'polling_interval' in config_data:
            interval = config_data['polling_interval']
            if not isinstance(interval, int) or interval < 1:
                result['errors'].append("Polling interval must be a positive integer")
                result['is_valid'] = False
        
        if 'remediation_timeout' in config_data:
            timeout = config_data['remediation_timeout']
            if not isinstance(timeout, int) or timeout < 1:
                result['errors'].append("Remediation timeout must be a positive integer")
                result['is_valid'] = False
        
        if 'log_level' in config_data:
            valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
            level = config_data['log_level']
            if not isinstance(level, str) or level.upper() not in valid_levels:
                result['errors'].append(f"Invalid log level: {level}. Must be one of {valid_levels}")
                result['is_valid'] = False
        
        # Security warnings
        if 'aws_access_key_id' in config_data and config_data['aws_access_key_id']:
            result['warnings'].append("AWS credentials found in configuration file")
        
        if 'aws_secret_access_key' in config_data and config_data['aws_secret_access_key']:
            result['warnings'].append("AWS secret key found in configuration file")
        
        return result
    
    def validate(self) -> bool:
        """
        Validate configuration settings.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        errors = []
        
        # Validate AWS settings
        if not self.aws_use_mock and (not self.aws_access_key_id or not self.aws_secret_access_key):
            errors.append("AWS credentials required when not using mock mode")
        
        # Validate polling settings
        if self.polling_interval < 1:
            errors.append("Polling interval must be at least 1 second")
        
        # Validate database settings
        if self.db_retention_days < 1:
            errors.append("Database retention days must be at least 1")
        
        # Validate remediation settings
        if self.remediation_timeout < 1:
            errors.append("Remediation timeout must be at least 1 second")
        
        # Validate log level
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"Invalid log level: {self.log_level}")
        
        if errors:
            logger.error(f"Configuration validation failed: {errors}")
            return False
        
        logger.info("Configuration validation passed")
        return True
    
    def setup_logging(self):
        """Setup logging based on configuration."""
        log_level = getattr(logging, self.log_level.upper())
        
        handlers = [logging.StreamHandler()]
        
        if self.log_file:
            handlers.append(logging.FileHandler(self.log_file))
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=handlers
        )
        
        logger.info(f"Logging configured at {self.log_level} level")

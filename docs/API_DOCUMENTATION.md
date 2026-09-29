# AeroDrift API Documentation

## Overview

AeroDrift is a self-healing infrastructure engine for enterprise CloudOps that uses graph theory to detect and automatically remediate configuration drift in cloud environments.

## Core Components

### 1. Cloud Ingestion Module

#### `AWSIngestion`

Asynchronous AWS API polling engine for concurrent data collection.

**Methods:**

- `__init__(region: str = "us-east-1", use_mock: bool = False)` - Initialize AWS ingestion engine
- `async def collect_vpcs() -> List[VPC]` - Collect all VPCs in the region
- `async def collect_subnets() -> List[Subnet]` - Collect all subnets in the region  
- `async def collect_security_groups() -> List[SecurityGroup]` - Collect all security groups
- `async def collect_ec2_instances() -> List[EC2Instance]` - Collect all EC2 instances
- `async def collect_all_resources() -> Dict[str, Any]` - Concurrently collect all AWS resources
- `async def continuous_polling(interval: int = 60, callback=None)` - Continuously poll AWS resources

**Data Models:**

- `VPC` - AWS VPC representation
- `Subnet` - AWS Subnet representation
- `SecurityGroup` - AWS Security Group representation
- `EC2Instance` - AWS EC2 Instance representation

**Example Usage:**

```python
from aerodrift.cloud_ingestion import AWSIngestion

ingestion = AWSIngestion(region="us-east-1", use_mock=True)
aws_data = await ingestion.collect_all_resources()
```

### 2. Topology Engine

#### `TopologyEngine`

NetworkX-based directed graph modeling for cloud architecture.

**Methods:**

- `__init__()` - Initialize topology engine with empty graph
- `add_resource(resource: ResourceNode)` - Add resource node to graph
- `add_network_edge(source_id: str, target_id: str, edge_type: str, attributes: Dict)` - Add network pathway edge
- `build_from_aws_data(aws_data: Dict)` - Build topology graph from AWS data
- `find_path_to_internet(resource_id: str) -> Optional[List[str]]` - Find path from resource to Internet
- `find_path_from_internet(resource_id: str) -> Optional[List[str]]` - Find path from Internet to resource
- `find_exposed_databases() -> List[Dict]` - Find all databases accessible from Internet
- `find_resources_with_internet_access() -> List[str]` - Find resources that can access Internet
- `get_resource_details(resource_id: str) -> Optional[ResourceNode]` - Get resource details
- `get_connected_resources(resource_id: str, direction: str) -> List[str]` - Get connected resources
- `get_graph_statistics() -> Dict` - Get topology graph statistics
- `export_graph(format: str) -> str` - Export graph to file
- `clear()` - Clear topology graph and cache

**Performance Features:**

- Path-finding cache with TTL support
- Thread-safe cache operations
- LRU cache for path description generation
- Performance tracking and statistics

**Example Usage:**

```python
from aerodrift.topology_engine import TopologyEngine

topology = TopologyEngine()
topology.build_from_aws_data(aws_data)
exposed_dbs = topology.find_exposed_databases()
```

### 3. Drift Detection

#### `DriftDetector`

Detects configuration drift by comparing graph states.

**Methods:**

- `__init__()` - Initialize drift detector
- `set_baseline(topology_engine)` - Set baseline graph state
- `update_current_state(topology_engine)` - Update current graph state
- `detect_drift() -> List[DriftEvent]` - Detect drift between states
- `get_critical_events() -> List[DriftEvent]` - Get critical/high severity events
- `get_events_requiring_remediation() -> List[DriftEvent]` - Get events requiring remediation
- `clear_events()` - Clear all detected events

**Drift Types:**

- `NEW_PATH_TO_INTERNET` - Resources that can now reach Internet
- `EXPOSED_DATABASE` - Databases accessible from Internet
- `SECURITY_GROUP_CHANGE` - Security group rule changes
- `NEW_PUBLIC_INSTANCE` - EC2 instances with public IPs
- `REMOVED_RESOURCE` - Resource removal
- `ADDED_RESOURCE` - Resource addition

**Severity Levels:**

- `CRITICAL` - Immediate attention required
- `HIGH` - Urgent attention required
- `MEDIUM` - Attention required
- `LOW` - Informational
- `INFO` - General information

**Example Usage:**

```python
from aerodrift.drift_detection import DriftDetector

detector = DriftDetector()
detector.set_baseline(baseline_topology)
detector.update_current_state(current_topology)
drift_events = detector.detect_drift()
```

### 4. Code Generator

#### `CodeGenerator`

Generates Python remediation scripts using AST module.

**Methods:**

- `__init__()` - Initialize code generator
- `generate_remediation_script(drift_event) -> str` - Generate remediation script for event
- `generate_batch_remediation(drift_events: List) -> str` - Generate batch remediation script
- `validate_generated_code(code: str) -> bool` - Validate generated code syntax

**Supported Remediation Types:**

- Security group rule revocation
- Database exposure mitigation
- Public instance handling
- Generic remediation logging

**Example Usage:**

```python
from aerodrift.code_generator import CodeGenerator

generator = CodeGenerator()
remediation_code = generator.generate_remediation_script(drift_event)
```

### 5. CLI Dashboard

#### `CLIDashboard`

Rich-based terminal UI for visualization and reporting.

**Methods:**

- `print_header(title: str)` - Print application header
- `display_topology_tree(topology_engine, title: str)` - Display cloud topology tree
- `display_drift_events(drift_events: List, title: str)` - Display drift events table
- `display_exposed_databases(exposed_dbs: List)` - Display exposed databases
- `display_graph_statistics(stats: Dict)` - Display topology statistics
- `display_remediation_code(code: str, title: str)` - Display remediation code
- `display_incident_report(drift_events: List, topology_stats: Dict)` - Display incident report
- `display_live_monitoring(update_callback, refresh_rate: float)` - Display live dashboard
- `create_monitoring_layout(topology_engine, drift_events: List) -> Layout` - Create monitoring layout
- `print_success(message: str)` - Print success message
- `print_error(message: str)` - Print error message
- `print_warning(message: str)` - Print warning message
- `print_info(message: str)` - Print info message

**Features:**

- ASCII art headers with branding
- Symbol-based resource indicators
- Health score calculation
- Enhanced table formatting
- Real-time monitoring dashboard
- Interactive menu system

### 6. State Persistence

#### `StatePersistence`

SQLite-based historical state storage and topology diffing.

**Methods:**

- `__init__(db_path: str)` - Initialize state persistence
- `save_topology_snapshot(aws_data: Dict)` - Save topology snapshot
- `get_latest_snapshot() -> Optional[Dict]` - Get latest snapshot
- `get_snapshots(limit: int) -> List[Dict]` - Get recent snapshots
- `save_drift_event(drift_event: DriftEvent)` - Save drift event
- `get_drift_events(limit: int) -> List[DriftEvent]` - Get drift events
- `mark_event_remediated(event_id: str, success: bool)` - Mark event as remediated
- `get_statistics() -> Dict` - Get database statistics

### 7. Execution Sandbox

#### `ExecutionSandbox`

Secure execution environment for dynamically generated code.

**Methods:**

- `__init__()` - Initialize execution sandbox
- `validate_code(code: str) -> Tuple[bool, Optional[str]]` - Validate code for security
- `execute(code: str, timeout: int, globals_dict: Dict) -> Dict` - Execute code in sandbox
- `execute_remediation(code: str, timeout: int) -> Dict` - Execute remediation code
- `get_execution_history(limit: int) -> List[Dict]` - Get execution history
- `clear_history()` - Clear execution history
- `test_sandbox() -> Dict` - Test sandbox with safe code

**Security Features:**

- Restricted global namespace
- Allowed imports whitelist
- Blocks dangerous operations (exec, eval, file operations)
- Output capture and error handling
- Execution timeout support

## Utility Modules

### Input Validation

#### `InputValidator`

Comprehensive input validation and sanitization.

**Methods:**

- `validate_aws_resource_id(resource_id: str) -> ValidationResult` - Validate AWS resource ID
- `validate_cidr(cidr: str) -> ValidationResult` - Validate CIDR notation
- `validate_aws_region(region: str) -> ValidationResult` - Validate AWS region
- `validate_tag(key: str, value: str) -> ValidationResult` - Validate AWS tags
- `sanitize_string(input_string: str, max_length: int) -> str` - Sanitize string input
- `validate_config_value(key: str, value: Any, expected_type: type) -> ValidationResult` - Validate config value
- `validate_json_structure(data: Dict, required_keys: List) -> ValidationResult` - Validate JSON structure
- `validate_port_number(port: int) -> ValidationResult` - Validate port number
- `validate_file_path(file_path: str) -> ValidationResult` - Validate file path
- `sanitize_dict(data: Dict, max_depth: int) -> Dict` - Recursively sanitize dictionary
- `validate_drift_event(event_data: Dict) -> ValidationResult` - Validate drift event data

### Structured Logging

#### `ContextualLogger`

Logger with contextual information support.

**Methods:**

- `with_context(**kwargs) -> ContextualLogger` - Create logger with additional context
- `debug(message: str, **kwargs)` - Log debug message
- `info(message: str, **kwargs)` - Log info message
- `warning(message: str, **kwargs)` - Log warning message
- `error(message: str, **kwargs)` - Log error message
- `critical(message: str, **kwargs)` - Log critical message
- `exception(message: str, **kwargs)` - Log exception with traceback

#### `PerformanceLogger`

Logger for performance monitoring and timing.

**Methods:**

- `start_operation(operation_name: str)` - Start timing an operation
- `end_operation(operation_name: str, **kwargs)` - End timing and log performance
- `time_operation(operation_name: str)` - Context manager for timing operations

### Retry Logic

#### `retry` Decorator

Decorator for retrying functions with configurable backoff.

**Parameters:**

- `max_attempts: int` - Maximum retry attempts (default: 3)
- `base_delay: float` - Base delay in seconds (default: 1.0)
- `max_delay: float` - Maximum delay in seconds (default: 60.0)
- `exponential_base: float` - Base for exponential backoff (default: 2.0)
- `jitter: bool` - Add random jitter to delays (default: True)
- `strategy: RetryStrategy` - Retry strategy (default: EXPONENTIAL_BACKOFF)
- `retryable_exceptions: Tuple` - Exceptions that trigger retry
- `non_retryable_exceptions: Tuple` - Exceptions that don't trigger retry
- `on_retry: Callable` - Callback on each retry

#### `CircuitBreaker`

Circuit breaker pattern for preventing cascading failures.

**Methods:**

- `__init__(failure_threshold: int, recovery_timeout: float, expected_exception: Type)` - Initialize circuit breaker
- `call(func: Callable, *args, **kwargs) -> Any` - Execute function with circuit breaker protection

### Security Features

#### `SensitiveDataHandler`

Handler for sensitive data with masking and hashing.

**Methods:**

- `mask_sensitive_data(data: str) -> str` - Mask sensitive data in string
- `mask_dict(data: Dict) -> Dict` - Recursively mask sensitive data in dictionary
- `hash_sensitive_value(value: str) -> str` - Hash sensitive value
- `redact_log_message(message: str) -> str` - Redact sensitive information from logs

#### `SecurityAuditor`

Security auditor for tracking and logging security events.

**Methods:**

- `log_event(event: SecurityEvent)` - Log security event to audit log
- `create_event(event_type, action, **kwargs) -> SecurityEvent` - Create security event
- `get_recent_events(limit: int) -> List[SecurityEvent]` - Get recent security events
- `get_security_summary() -> Dict` - Get security event summary

#### `SecurityPolicy`

Security policy enforcement for operations.

**Methods:**

- `check_policy(policy_name: str, **kwargs) -> Tuple[bool, List[str]]` - Check policy compliance
- `update_policy(policy_name: str, policy_config: Dict)` - Update security policy
- `get_policy(policy_name: str) -> Optional[Dict]` - Get policy configuration

## Configuration

### `Config` Class

Configuration settings for AeroDrift.

**Attributes:**

- `aws_region: str` - AWS region (default: "us-east-1")
- `aws_use_mock: bool` - Use mock data (default: True)
- `aws_access_key_id: Optional[str]` - AWS access key
- `aws_secret_access_key: Optional[str]` - AWS secret key
- `polling_interval: int` - Polling interval in seconds (default: 60)
- `polling_enabled: bool` - Enable polling (default: True)
- `db_path: str` - Database path (default: "aerodrift_states.db")
- `db_retention_days: int` - Data retention days (default: 30)
- `auto_remediate: bool` - Enable auto-remediation (default: False)
- `remediation_timeout: int` - Remediation timeout (default: 30)
- `require_approval: bool` - Require approval (default: True)
- `log_level: str` - Log level (default: "INFO")
- `log_file: Optional[str]` - Log file path
- `dashboard_refresh_rate: float` - Dashboard refresh rate (default: 1.0)

**Methods:**

- `classmethod from_file(config_path: str) -> Config` - Load from JSON file
- `to_file(config_path: str)` - Save to JSON file
- `override_from_env()` - Override from environment variables
- `validate() -> bool` - Validate configuration
- `setup_logging()` - Setup logging based on config

## Main Daemon

### `AeroDriftDaemon`

Main daemon that orchestrates all AeroDrift components.

**Methods:**

- `__init__(config: Config)` - Initialize daemon
- `async def initialize()` - Initialize daemon with baseline data
- `async def run_single_scan()` - Run single drift scan
- `async def handle_remediation(drift_events)` - Handle remediation of events
- `async def run_continuous_monitoring()` - Run continuous monitoring
- `async def run_live_dashboard()` - Run live dashboard
- `generate_incident_report()` - Generate incident report
- `show_statistics()` - Show database and runtime statistics

## Command Line Interface

### Usage

```bash
# Initialize with mock data
python -m aerodrift.main --mode init --mock

# Run single drift scan
python -m aerodrift.main --mode scan --mock

# Start continuous monitoring
python -m aerodrift.main --mode monitor --mock

# Generate incident report
python -m aerodrift.main --mode report --mock

# Show statistics
python -m aerodrift.main --mode stats --mock
```

### Arguments

- `--config PATH` - Path to configuration file
- `--mode MODE` - Operation mode (init, scan, monitor, dashboard, report, stats)
- `--region REGION` - AWS region
- `--mock` - Use mock AWS data
- `--auto-remediate` - Enable automatic remediation

## Error Handling

The application includes comprehensive error handling:

- **Connection Errors**: Handled with retry logic and circuit breakers
- **Timeout Errors**: Configurable timeouts with exponential backoff
- **Validation Errors**: Input validation with detailed error messages
- **Data Integrity**: Checks for empty or invalid data structures
- **Security Violations**: Policy enforcement and audit logging

## Performance Optimization

The topology engine includes several performance optimizations:

- **Path Caching**: Cached path-finding results with TTL
- **LRU Cache**: Path description generation caching
- **Batch Processing**: Efficient batch operations for large topologies
- **Performance Tracking**: Operation timing and statistics
- **Thread Safety**: Concurrent access protection

## Security Features

AeroDrift includes comprehensive security features:

- **Data Masking**: Automatic masking of sensitive information
- **Audit Logging**: Complete security event tracking
- **Policy Enforcement**: Configurable security policies
- **Sandboxed Execution**: Secure code execution environment
- **Input Validation**: Comprehensive input sanitization
- **Credential Safety**: No hardcoded credentials, environment variable support
# AeroDrift: Agentic Cloud Topology & Remediation Graph

A self-healing infrastructure engine for enterprise CloudOps that uses graph theory to detect and automatically remediate configuration drift in cloud environments.

## 🌟 Features

- **Cloud Ingestion**: Highly concurrent asynchronous AWS API polling using boto3 and asyncio
- **Topology Engine**: NetworkX-based directed graph modeling of entire cloud architecture
- **Drift Detection**: Real-time detection of security anomalies and configuration changes
- **Code Generation**: Python ast-based automatic generation of remediation scripts
- **Execution Sandbox**: Secure execution environment for dynamically generated code
- **State Persistence**: SQLite-based historical state storage and topology diffing
- **CLI Dashboard**: Beautiful Rich-based terminal UI for visualization and reporting

## 🚀 Quick Start

### Installation

```bash
# Install dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### Basic Usage

```bash
# Initialize with mock data (default)
python -m aerodrift.main --mode init --mock

# Run a single drift scan
python -m aerodrift.main --mode scan --mock

# Start continuous monitoring
python -m aerodrift.main --mode monitor --mock

# Generate incident report
python -m aerodrift.main --mode report --mock

# Show statistics
python -m aerodrift.main --mode stats --mock
```

### Configuration

Create a configuration file `aerodrift_config.json`:

```json
{
  "aws_region": "us-east-1",
  "aws_use_mock": true,
  "polling_interval": 60,
  "db_path": "aerodrift_states.db",
  "auto_remediate": false,
  "require_approval": true,
  "log_level": "INFO",
  "log_file": "aerodrift.log"
}
```

## 📖 Architecture

### Components

1. **Cloud Ingestion Module** (`aerodrift/cloud_ingestion/`)
   - Asynchronous AWS API polling
   - Mock data generation for testing
   - Concurrent resource collection

2. **Topology Engine** (`aerodrift/topology_engine/`)
   - NetworkX directed graph modeling
   - Path-finding algorithms
   - Resource relationship mapping

3. **Drift Detection** (`aerodrift/drift_detection/`)
   - Baseline vs current state comparison
   - Security anomaly detection
   - Multi-severity event classification

4. **Code Generator** (`aerodrift/code_generator/`)
   - Python ast-based code generation
   - Automatic remediation script creation
   - Batch remediation support

5. **CLI Dashboard** (`aerodrift/cli_dashboard/`)
   - Rich-based terminal UI
   - Interactive topology visualization
   - Real-time monitoring dashboard

6. **State Persistence** (`aerodrift/state_persistence/`)
   - SQLite database storage
   - Historical state tracking
   - Topology diff generation

7. **Execution Sandbox** (`aerodrift/utils/`)
   - Secure code execution
   - Restricted global namespace
   - Output capture and validation

## 🔧 Use Cases

### Scenario 1: Database Exposure Detection

A CloudOps engineer accidentally opens a security group to allow internet access to a private database:

```python
import asyncio
from aerodrift.cloud_ingestion import AWSIngestion
from aerodrift.topology_engine import TopologyEngine
from aerodrift.drift_detection import DriftDetector
from aerodrift.cli_dashboard import CLIDashboard

async def detect_database_exposure():
    # Initialize components
    ingestion = AWSIngestion(use_mock=True)
    topology = TopologyEngine()
    detector = DriftDetector()
    dashboard = CLIDashboard()
    
    # Collect AWS data
    aws_data = await ingestion.collect_all_resources()
    
    # Build topology
    topology.build_from_aws_data(aws_data)
    
    # Find exposed databases
    exposed_dbs = topology.find_exposed_databases()
    
    if exposed_dbs:
        dashboard.print_warning(f"Found {len(exposed_dbs)} exposed databases!")
        dashboard.display_exposed_databases(exposed_dbs)
    else:
        dashboard.print_success("No exposed databases found")

asyncio.run(detect_database_exposure())
```

### Scenario 2: Automatic Remediation

When a security drift is detected, AeroDrift can automatically generate and execute remediation code:

```python
from aerodrift.code_generator import CodeGenerator
from aerodrift.utils import ExecutionSandbox

# Generate remediation code
code_generator = CodeGenerator()
remediation_code = code_generator.generate_remediation_script(drift_event)

# Execute in sandbox
sandbox = ExecutionSandbox()
result = sandbox.execute_remediation(remediation_code)

if result['success']:
    print("Remediation successful!")
else:
    print(f"Remediation failed: {result['error']}")
```

### Scenario 3: Continuous Monitoring

Run the daemon in continuous monitoring mode:

```bash
python -m aerodrift.main --mode monitor --mock --polling-interval 30
```

## 🧪 Testing

The project includes mock AWS data for testing without real credentials:

```python
from aerodrift.cloud_ingestion.mock_data import MockAWSData

# Create mock data with intentional vulnerabilities
mock_data = MockAWSData()

# Add a vulnerable rule for testing
mock_data.add_vulnerable_rule("sg-secure-db", cidr="0.0.0.0/0", port=3306)

# Test drift detection
security_groups = mock_data.get_security_groups()
```

## 📊 CLI Reference

### Command-Line Options

```
--config PATH         Path to configuration file (default: aerodrift_config.json)
--mode MODE           Operation mode: init, scan, monitor, dashboard, report, stats
--region REGION       AWS region (overrides config)
--mock                Use mock AWS data
--auto-remediate      Enable automatic remediation
```

### Operation Modes

- **init**: Initialize daemon with baseline data
- **scan**: Run single drift detection scan
- **monitor**: Start continuous monitoring
- **dashboard**: Run live dashboard
- **report**: Generate incident report
- **stats**: Show database and runtime statistics

## 🔒 Security Features

- **Sandboxed Execution**: All generated code runs in a restricted environment
- **Code Validation**: AST-based validation before execution
- **Approval System**: Optional approval required for remediation
- **Audit Trail**: Complete logging of all actions and changes
- **Credential Safety**: No hardcoded credentials, uses environment variables

## 🛠️ Development

### Project Structure

```
aerodrift/
├── cloud_ingestion/      # AWS API polling and mock data
├── topology_engine/     # NetworkX graph modeling
├── drift_detection/     # Drift detection logic
├── code_generator/      # Python ast code generation
├── cli_dashboard/       # Rich-based terminal UI
├── state_persistence/   # SQLite database storage
├── utils/              # Configuration and execution sandbox
└── main.py             # Main daemon entry point
```

### Running Tests

```bash
# Run with pytest (when tests are implemented)
pytest tests/

# Run with coverage
pytest --cov=aerodrift tests/
```

### Code Style

```bash
# Format code with black
black aerodrift/

# Check with flake8
flake8 aerodrift/

# Type check with mypy
mypy aerodrift/
```

## 📝 Configuration Reference

### AWS Settings

- `aws_region`: AWS region to query (default: "us-east-1")
- `aws_use_mock`: Use mock data instead of real AWS (default: true)
- `aws_access_key_id`: AWS access key (required if not using mock)
- `aws_secret_access_key`: AWS secret key (required if not using mock)

### Polling Settings

- `polling_interval`: Polling interval in seconds (default: 60)
- `polling_enabled`: Enable continuous polling (default: true)

### Database Settings

- `db_path`: Path to SQLite database (default: "aerodrift_states.db")
- `db_retention_days`: Days to keep snapshots (default: 30)

### Remediation Settings

- `auto_remediate`: Enable automatic remediation (default: false)
- `remediation_timeout`: Execution timeout in seconds (default: 30)
- `require_approval`: Require approval before remediation (default: true)

### Logging Settings

- `log_level`: Logging level (default: "INFO")
- `log_file`: Path to log file (default: "aerodrift.log")

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

This project demonstrates advanced Python techniques including:
- Asynchronous programming with asyncio
- Graph theory with NetworkX
- Metaprogramming with Python ast
- Beautiful terminal UIs with Rich
- Safe code execution and sandboxing
- Cloud infrastructure automation

Built as part of advanced Python development training focusing on systems-level architecture and overcoming Python's traditional limitations.

# AeroDrift Architecture Documentation

## System Architecture

AeroDrift is designed as a modular, event-driven system for cloud infrastructure monitoring and automated remediation. The architecture follows a pipeline pattern with distinct phases for data ingestion, analysis, detection, and remediation.

## Core Architecture Components

### 1. Data Ingestion Layer

**Purpose**: Collect and normalize cloud infrastructure data

**Components**:
- **AWSIngestion**: Asynchronous AWS API client with concurrent polling
- **MockAWSData**: Testing data generator for development
- **Data Models**: VPC, Subnet, SecurityGroup, EC2Instance dataclasses

**Design Patterns**:
- **Async/Await Pattern**: Non-blocking I/O for high-performance data collection
- **Concurrent Execution**: Parallel API calls using asyncio.gather()
- **Data Normalization**: Consistent data models across cloud providers

**Flow**:
```
AWS APIs → Async Collection → Data Normalization → Structured Data → Topology Engine
```

### 2. Topology Analysis Layer

**Purpose**: Model cloud infrastructure as a directed graph for analysis

**Components**:
- **TopologyEngine**: NetworkX-based graph modeling
- **ResourceNode**: Graph node representation
- **ResourceType**: Enum for resource classification

**Design Patterns**:
- **Graph Theory**: NetworkX for complex relationship modeling
- **Path Finding**: Shortest path algorithms for security analysis
- **Caching Pattern**: Performance optimization with TTL-based caching

**Key Operations**:
- **Graph Construction**: Build directed graph from AWS data
- **Path Analysis**: Find attack paths from Internet to sensitive resources
- **Exposure Detection**: Identify resources accessible from external networks
- **Statistics**: Graph metrics and resource counts

**Flow**:
```
AWS Data → Graph Construction → Resource Indexing → Path Analysis → Security Queries
```

### 3. Drift Detection Layer

**Purpose**: Compare infrastructure states and detect configuration changes

**Components**:
- **DriftDetector**: State comparison engine
- **DriftEvent**: Structured drift event representation
- **DriftType/DriftSeverity**: Classification enums

**Design Patterns**:
- **State Comparison**: Baseline vs current state analysis
- **Event Classification**: Type and severity categorization
- **Change Detection**: Graph diffing and rule analysis

**Detection Types**:
- **Security Drift**: New attack paths, exposed databases
- **Configuration Drift**: Security group changes, new public instances
- **Infrastructure Drift**: Resource additions/removals

**Flow**:
```
Baseline State + Current State → State Comparison → Drift Classification → Event Generation
```

### 4. Remediation Layer

**Purpose**: Generate and execute automated remediation scripts

**Components**:
- **CodeGenerator**: AST-based Python code generation
- **ExecutionSandbox**: Secure code execution environment
- **RemediationAction**: Structured remediation representation

**Design Patterns**:
- **Metaprogramming**: AST-based code generation
- **Sandbox Pattern**: Restricted execution environment
- **Template Method**: Strategy pattern for different remediation types

**Security Features**:
- **Code Validation**: AST validation before execution
- **Namespace Restriction**: Limited global scope
- **Timeout Protection**: Execution time limits
- **Audit Trail**: Complete execution logging

**Flow**:
```
Drift Event → Code Generation → Security Validation → Sandboxed Execution → Result Logging
```

### 5. Persistence Layer

**Purpose**: Store historical states and enable temporal analysis

**Components**:
- **StatePersistence**: SQLite-based storage engine
- **Schema**: Versioned database schema
- **Query Methods**: Snapshot and event retrieval

**Design Patterns**:
- **Repository Pattern**: Data access abstraction
- **Temporal Storage**: Time-series data management
- **Batch Operations**: Efficient bulk operations

**Storage Schema**:
- **topology_snapshots**: Historical infrastructure states
- **drift_events**: Detected drift events with metadata
- **remediation_history**: Execution results and status

**Flow**:
```
Data → Serialization → Database Storage → Query Interface → Historical Analysis
```

### 6. User Interface Layer

**Purpose**: Provide visualization and user interaction

**Components**:
- **CLIDashboard**: Rich-based terminal UI
- **Interactive Components**: Tables, trees, panels
- **Live Monitoring**: Real-time dashboard updates

**Design Patterns**:
- **MVC Pattern**: Separation of data, view, and control
- **Observer Pattern**: Real-time updates for monitoring
- **Component Composition**: Reusable UI components

**Features**:
- **Topology Visualization**: Interactive tree view
- **Event Display**: Color-coded drift events
- **Health Scoring**: System health metrics
- **Real-time Monitoring**: Live dashboard updates

## Data Flow Architecture

### Main Pipeline Flow

```
1. DATA INGESTION
   AWS APIs → Async Collection → Data Normalization → Structured Output

2. TOPOLOGY MODELING
   Structured Data → Graph Construction → Resource Indexing → Cached Paths

3. DRIFT DETECTION
   Baseline + Current → State Comparison → Pattern Matching → Event Generation

4. REMEDIATION (if enabled)
   Drift Event → Code Generation → Security Validation → Execution → Logging

5. PERSISTENCE
   All States → Database Storage → Historical Tracking → Query Interface

6. USER INTERFACE
   All Data → Visualization → User Interaction → Display Updates
```

### Monitoring Flow

```
Continuous Loop:
┌─────────────────────────────────────────────────────────┐
│ 1. Collect Current State (AWS APIs)                    │
│ 2. Build Current Topology (Graph Engine)               │
│ 3. Compare with Baseline (Drift Detector)            │
│ 4. Detect Security Issues (Pattern Matching)          │
│ 5. Generate Events (Event Classification)             │
│ 6. Store Results (Persistence Layer)                  │
│ 7. Update Dashboard (UI Layer)                        │
│ 8. Wait for Interval (Configurable Delay)              │
└─────────────────────────────────────────────────────────┘
```

## Security Architecture

### Defense in Depth

1. **Input Layer**: Comprehensive validation and sanitization
2. **Execution Layer**: Sandboxed code execution with restrictions
3. **Data Layer**: Sensitive data masking and encryption
4. **Audit Layer**: Complete security event logging
5. **Policy Layer**: Security policy enforcement

### Security Components

- **InputValidator**: Validates all external inputs
- **SensitiveDataHandler**: Masks sensitive information
- **SecurityAuditor**: Tracks security events
- **SecurityPolicy**: Enforces security rules
- **ExecutionSandbox**: Restricted execution environment

### Threat Mitigation

- **Injection Attacks**: AST validation and namespace restriction
- **Data Exfiltration**: Output capture and validation
- **Privilege Escalation**: Limited execution scope
- **Credential Exposure**: Automatic masking and hashing
- **Supply Chain Attacks**: Dependency validation and sandboxing

## Performance Architecture

### Optimization Strategies

1. **Caching Layer**
   - Path-finding results with TTL
   - LRU cache for frequently used operations
   - Thread-safe cache operations

2. **Concurrency**
   - Async I/O for network operations
   - Parallel data collection
   - Non-blocking event processing

3. **Batch Processing**
   - Bulk database operations
   - Batch API calls
   - Efficient graph algorithms

4. **Resource Management**
   - Connection pooling
   - Memory-efficient data structures
   - Lazy loading where appropriate

### Performance Monitoring

- **Operation Timing**: Track duration of key operations
- **Cache Statistics**: Hit/miss ratios and efficiency
- **Resource Usage**: Memory and CPU monitoring
- **Throughput**: Operations per second metrics

## Scalability Architecture

### Horizontal Scaling

- **Component Isolation**: Each layer can be scaled independently
- **Stateless Design**: UI and detection components are stateless
- **Queue-based Processing**: Event-driven architecture for work distribution

### Vertical Scaling

- **Caching**: Reduces database load
- **Connection Pooling**: Efficient resource utilization
- **Batch Operations**: Reduces per-operation overhead

### Future Scalability Considerations

- **Multi-cloud Support**: Abstracted ingestion layer
- **Distributed Processing**: Event streaming with Kafka/RabbitMQ
- **Microservices**: Component decomposition for independent scaling
- **Load Balancing**: Multiple instance support

## Reliability Architecture

### Failure Handling

1. **Retry Logic**
   - Exponential backoff for transient failures
   - Circuit breaker pattern for cascading failure prevention
   - Configurable retry policies

2. **Error Recovery**
   - Graceful degradation on component failure
   - Fallback to previous known state
   - Automatic retry with increasing delays

3. **Data Integrity**
   - Transactional database operations
   - Data validation at each layer
   - Rollback capability for failed operations

### Monitoring and Alerting

- **Health Checks**: Component health monitoring
- **Performance Metrics**: Key performance indicators
- **Alert Thresholds**: Configurable alerting rules
- **Audit Trail**: Complete operation logging

## Configuration Architecture

### Configuration Hierarchy

1. **Default Values**: Built-in sensible defaults
2. **Configuration File**: JSON-based configuration
3. **Environment Variables**: Runtime overrides
4. **Command Line Arguments**: Session-specific overrides

### Configuration Management

- **Validation**: Configuration schema validation
- **Security Checks**: Sensitive data detection
- **Hot Reload**: Runtime configuration updates (future)
- **Versioning**: Configuration version tracking

## Extension Points

### Custom Cloud Providers

The architecture supports adding new cloud providers:

1. Implement provider-specific ingestion module
2. Create provider-specific data models
3. Add provider normalization layer
4. Extend topology engine for provider-specific resources

### Custom Drift Rules

Custom drift detection rules can be added:

1. Define new drift types in DriftType enum
2. Implement detection logic in DriftDetector
3. Add corresponding remediation logic
4. Update UI for new event types

### Custom Remediation

New remediation strategies can be implemented:

1. Add new remediation methods to CodeGenerator
2. Implement security validation
3. Add execution sandbox rules
4. Update policy enforcement

## Technology Stack

### Core Technologies

- **Python 3.8+**: Primary development language
- **asyncio**: Asynchronous programming
- **NetworkX**: Graph algorithms and modeling
- **boto3**: AWS SDK
- **Rich**: Terminal UI framework
- **SQLite**: Embedded database

### Dependencies

- **aiohttp**: Async HTTP client
- **python-dateutil**: Date/time parsing
- **dataclasses**: Data modeling
- **typing**: Type hints
- **logging**: Structured logging

### Development Tools

- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **flake8**: Linting

## Deployment Architecture

### Development Environment

- **Mock Data**: Complete mock AWS environment
- **Local Database**: SQLite for local development
- **Debug Logging**: Detailed logging for troubleshooting

### Production Environment

- **Real AWS Integration**: Production AWS credentials
- **Database Options**: SQLite or PostgreSQL
- **Structured Logging**: JSON logging for log aggregation
- **Monitoring**: Performance and security monitoring

### Container Deployment

- **Docker Support**: Containerized deployment
- **Configuration Management**: Environment-based configuration
- **Health Checks**: Container health monitoring
- **Log Aggregation**: Centralized log collection

## Maintenance Architecture

### Version Control

- **Semantic Versioning**: MAJOR.MINOR.PATCH
- **Branching Strategy**: Feature branches with main integration
- **Change Management**: Changelog and release notes

### Testing Strategy

- **Unit Tests**: Component-level testing
- **Integration Tests**: Cross-component testing
- **End-to-End Tests**: Full pipeline testing
- **Mock Testing**: Isolated component testing

### Documentation

- **API Documentation**: Complete API reference
- **Architecture Documentation**: System design documentation
- **User Documentation**: Usage guides and tutorials
- **Developer Documentation**: Contribution guidelines

This architecture provides a solid foundation for cloud infrastructure monitoring and automated remediation while maintaining security, performance, and extensibility.
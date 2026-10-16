# AeroDrift Architecture & Technical Specification

## Overview
AeroDrift is an autonomous agentic cloud security pipeline designed to detect and remediate infrastructure configuration drift using graph modeling and deterministic AST code synthesis.

---

## 1. Pipeline Stages

### Stage 1: Cloud Ingestion (`src/ingestion/mock_aws.py`)
- Emulates AWS API responses for EC2, VPC subnets, security groups, and RDS databases.
- Acts as a zero-cost local provider for simulation and deterministic testing.

### Stage 2: Topology Graph (`src/topology/graph_engine.py`)
- Maps multi-hop cloud dependencies using a **NetworkX Directed Graph (`DiGraph`)**.
- Nodes:
  - `internet` (External world)
  - `subnet-public`, `subnet-private` (VPC network boundaries)
  - `i-001` (Web EC2 instance)
  - `sg-001` (Security Group)
  - `db-001` (Private RDS database)
- Relational edges capture ingress rules and compute bindings to trace attack vectors.

### Stage 3: Drift Detection (`src/detection/drift_detector.py`)
- Algorithmically inspects edges originating from the `internet` node.
- Flags insecure rules such as unrestricted CIDR blocks (`0.0.0.0/0`) on sensitive ports (SSH port 22).
- Produces normalized JSON finding payloads.

### Stage 4: Deterministic AST Synthesis (`src/remediation/code_generator.py`)
- Programmatically constructs Python Abstract Syntax Trees using Python's native `ast` library.
- Compiles syntactically guaranteed `ec2.revoke_security_group_ingress()` calls.
- Eliminates syntax errors and runtime parsing exceptions.

### Stage 5: Sandboxed Execution & Verification (`src/remediation/`)
- `executor.py`: Executes synthesized AST in a controlled mock environment.
- `verifier.py`: Queries post-execution security group state to programmatically confirm rule removal (`DRIFT RESOLVED`).

### Stage 6: Audit History & Incident Reporting (`src/history/`)
- `database.py`: Persists serialized JSON topology snapshots in SQLite (`aerodrift_history.db`).
- `diff.py`: Computes set-theoretic differences between before and after graph snapshots.
- `incident_report.py`: Automatically generates formal PDF compliance reports using `ReportLab`.

---

## 2. Threat Model & Remediation Guarantee
- **Vulnerability**: Unauthorized ingress port exposure (CWE-284 / OWASP Cloud Top 10).
- **Remediation Guarantee**: 100% deterministic rule revocation without touching unauthorized resource attributes.
# AeroDrift: Agentic Cloud Topology Remediation Graph

![Tests](https://img.shields.io/badge/pytest-26%20passed-brightgreen)
![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.14-blue)
![Architecture](https://img.shields.io/badge/architecture-agentic--graph-purple)
![License](https://img.shields.io/badge/license-MIT-green)

AeroDrift is an autonomous, graph-based agentic cloud security remediation engine. It discovers cloud infrastructure assets, models multi-hop dependencies into directed graph topologies, flags unauthorized configuration drift, synthesizes deterministic AST Python remediation code, executes dry-run sandbox fixes, and preserves cryptographically verifiable audit trails with PDF incident reports.

---

## 🌟 Key Features

- **Relational Topology Engine**: Converts raw cloud resources into NetworkX directed graphs (`DiGraph`) to analyze attack paths and multi-hop blast radius.
- **Autonomous Drift Discovery**: Inspects topology edges starting from the external internet boundary to pinpoint open ingress security violations (e.g., SSH port 22 exposed to `0.0.0.0/0`).
- **Deterministic AST Code Synthesis**: Uses Python's native `ast` (Abstract Syntax Tree) module to programmatically construct validated Boto3 API remediation code—eliminating LLM hallucinations and syntax errors.
- **Sandboxed Execution & Verification**: Executes generated code against isolated mock providers and programmatically verifies remediation status (`DRIFT RESOLVED`).
- **Cryptographic Auditability & Diff Engine**: Persists graph state snapshots in SQLite, performs set-theoretic graph diffing to mathematically verify edge removals, and compiles formal PDF incident reports using ReportLab.
- **Terminal CLI Dashboard**: Real-time terminal orchestration with resource breakdown, live drift findings, and audit summaries powered by `Rich`.

---

## 🏗️ Architecture Pipeline

AeroDrift operates as a 6-stage closed-loop autonomous pipeline:

```text
[ 1. Ingestion ]      --> Discovers AWS compute, network, database, and security assets
       │
[ 2. Topology ]       --> Maps 6 nodes & 4 relational edges in NetworkX DiGraph
       │
[ 3. Detection ]      --> Detects unauthorized public ingress (0.0.0.0/0 on port 22)
       │
[ 4. AST Synthesis ]  --> Generates deterministic Boto3 revoke_security_group_ingress code
       │
[ 5. Verification ]   --> Executes safe sandbox dry-run and confirms rule removal
       │
[ 6. Audit & Report ] --> Saves snapshot diff to SQLite & compiles formal PDF report
<!-- Pipeline testing telemetry: 2026-10-15 -->

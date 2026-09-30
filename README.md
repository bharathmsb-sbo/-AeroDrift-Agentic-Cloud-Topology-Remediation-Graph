# AeroDrift – Agentic Cloud Topology & Remediation Graph

## About the Project

**AeroDrift – Agentic Cloud Topology & Remediation Graph** is a cloud infrastructure project designed to collect, understand, and analyze cloud resource information and their relationships.

The project focuses on ingesting cloud infrastructure state such as **VPCs, Subnets, Security Groups, and EC2 Instances**, and using this information to build a cloud topology, detect network security drift, and support future automated remediation workflows.

Since a live AWS account is not being used during the current development stage, the project uses **mock/sandbox AWS data** to simulate cloud infrastructure resources and their relationships.

The project is being developed incrementally, starting with cloud data ingestion and extending toward topology construction, network drift detection, graph auditing, and automated remediation.

## Project Architecture

```text
Mock / Sandbox AWS State
          ↓
   Cloud Ingestion
          ↓
   Topology Builder
          ↓
   Cloud Topology Graph
          ↓
    Drift Detector
          ↓
     Graph Audit
          ↓
 Future Remediation Workflows
```

## Cloud Ingestion

The project includes a basic cloud ingestion layer that collects simulated AWS infrastructure state.

### Supported Resources

* VPCs
* Subnets
* Security Groups
* EC2 Instances

### Sample Resources

```text
VPC
├── vpc-001
│   └── CIDR: 10.0.0.0/16
│
├── Subnet
│   └── subnet-001
│
├── Security Group
│   └── sg-001 (web-sg)
│
└── EC2 Instance
    └── i-001 (running)
```

The ingestion layer uses asynchronous Python patterns with `asyncio` and follows a Boto3-style structure so that it can later be connected to a live AWS environment.

## Cloud Topology

The **Topology Builder** converts the collected cloud resource information into a graph representation.

The topology contains:

* Resource nodes such as VPCs, Subnets, Security Groups, EC2 Instances, Internet, and Database resources.
* Relationships between resources represented as graph edges.
* Connectivity information that can be used for security and infrastructure analysis.

This graph provides the foundation for detecting unexpected or potentially unsafe network paths.

## Drift Detection

The project includes a **Drift Detector** that analyzes the network topology graph.

One of the implemented checks detects whether a path exists between:

```text
0.0.0.0/0 (Internet)
          ↓
     Private Database
```

The detector performs graph traversal to identify whether the Internet node can reach a private database node.

This helps identify a newly introduced network exposure in the cloud topology.

### Drift Detection Logic

The detector:

1. Builds an adjacency representation of the topology.
2. Identifies the `0.0.0.0/0` Internet node.
3. Identifies private database nodes.
4. Traverses the graph from the Internet node.
5. Reports whether a path to a database exists.

## Graph Audit

The project also includes a **Graph Audit** component for continuously checking the topology for newly introduced network paths.

The `graph_audit.py` module uses the existing Drift Detector and repeatedly checks the graph for an Internet-to-database path.

The audit records the detection time and verifies that the newly introduced path can be detected within the configured **5-second detection window**.

### Audit Flow

```text
Security Group Change
        ↓
Network Topology Change
        ↓
Graph Audit
        ↓
Drift Detector
        ↓
Internet → Private Database?
        ↓
Detection Result + Detection Time
```

Because the current project uses a mock/sandbox AWS environment, the Security Group change is currently **simulated** by modifying the topology graph.

The automated audit test verifies that:

* Initially there is no Internet-to-database path.
* A simulated network change creates a new path.
* The Graph Audit detects the new path.
* Detection occurs within the 5-second requirement.

## Project Structure

```text
AeroDrift-Agentic-Cloud-Topology-Remediation-Graph/
│
├── src/
│   ├── cloud_ingestion.py
│   ├── topology_builder.py
│   ├── drift_detector.py
│   └── graph_audit.py
│
├── test/
│   ├── test_cloud_ingestion.py
│   ├── test_topology_builder.py
│   ├── test_drift_detector.py
│   └── test_graph_audit.py
│
└── README.md
```

## Technologies Used

* Python
* AsyncIO
* AWS / Boto3-style ingestion
* Graph-based topology analysis
* Pytest
* Git
* GitHub

## Testing

Run the complete test suite using:

```bash
python -m pytest -q
```

The current automated test suite covers:

* Cloud ingestion
* Topology construction
* Network drift detection
* Graph audit and detection-time verification

### Current Test Result

```text
7 passed
```

The Graph Audit test specifically verifies that the simulated new network path is detected within the configured 5-second window.

## Current Status

The current implementation includes:

* Cloud/AWS mock data ingestion
* VPC, Subnet, Security Group, and EC2 resource simulation
* Asynchronous data collection
* Cloud topology construction
* Graph-based network path detection
* Internet-to-private-database drift detection
* Graph audit monitoring
* Simulated Security Group/network changes
* Automated unit tests
* Detection-time verification
* Git-based version control

The current test suite passes successfully with **7 tests passed**.

## Future Scope

* Integration with a live AWS environment using Boto3.
* Expanded AWS resource ingestion.
* More detailed cloud topology construction.
* Security Group rule analysis.
* Advanced network relationship analysis.
* Detection of additional infrastructure security issues.
* Continuous cloud-state monitoring.
* Remediation recommendations.
* Agentic remediation workflows.
* Automated infrastructure remediation.
* Improved resilience and monitoring.

# -AeroDrift-Agentic-Cloud-Topology-Remediation-Graph# AeroDrift – Agentic Cloud Topology & Remediation Graph

## About the Project

**AeroDrift – Agentic Cloud Topology & Remediation Graph** is a cloud infrastructure project designed to collect, understand, and analyze cloud resource information and their relationships.

The project focuses on building a cloud topology from infrastructure resources and detecting security-related configuration drift.

AeroDrift is being developed incrementally, starting with mock AWS infrastructure data and gradually extending toward topology analysis, drift detection, and automated remediation.

## Week 1 – Cloud Ingestion & Topology

The main objective of Week 1 is to build the foundation for collecting cloud infrastructure data and representing the relationships between resources.

Since a live AWS environment is not being used during the initial development, **mock AWS data** is used to simulate cloud resources.

### Week 1 Work

- Implemented the basic cloud ingestion module.
- Created mock AWS infrastructure data.
- Simulated **EC2 Instances**.
- Simulated **Subnets**.
- Simulated **Security Groups**.
- Simulated **Databases**.
- Built a cloud topology using **NetworkX**.
- Represented cloud resources as graph nodes.
- Represented resource relationships as graph edges.
- Added Internet ingress relationships.
- Implemented basic security drift detection.
- Detected publicly accessible security group ingress rules.

### Sample Resources

```text
Cloud Environment
│
├── Internet
│
├── Security Group
│   └── sg-001
│       └── TCP Port 22
│           └── 0.0.0.0/0
│
├── EC2 Instance
│   └── i-001 (web-server)
│
├── Subnets
│   ├── subnet-public
│   └── subnet-private
│
└── Database
    └── db-001 (production-db)
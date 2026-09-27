# AeroDrift – Agentic Cloud Topology & Remediation Graph

## About the Project

**AeroDrift – Agentic Cloud Topology & Remediation Graph** is a cloud infrastructure project designed to collect, understand, and analyze cloud resource information and their relationships.

The project focuses on ingesting cloud infrastructure state such as **VPCs, Subnets, Security Groups, and EC2 Instances** and using this information as the foundation for building a cloud topology and supporting future remediation workflows.

The project is being developed incrementally, starting with **AWS cloud data ingestion** and gradually extending toward topology analysis and automated remediation.

## Week 1 – AWS Ingestion

The main objective of Week 1 is to develop the **AWS ingestion layer** for collecting cloud infrastructure state.

Since a live AWS account is not being used during the initial development, **mock/sandbox AWS data** is used to simulate the required cloud resources.

### Week 1 Work

* Implemented the basic cloud ingestion module.
* Created mock/sandbox AWS infrastructure data.
* Simulated **VPCs**.
* Simulated **Subnets**.
* Simulated **Security Groups**.
* Simulated **EC2 Instances**.
* Added asynchronous data collection using Python `asyncio`.
* Added unit tests to validate the ingestion process.
* Verified that the required cloud resource data is collected correctly.

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

## Technologies Used

* Python
* AsyncIO
* AWS / Boto3-style ingestion
* Pytest
* Git
* GitHub

## Testing

Run the tests using:

```bash
python -m pytest -q
```

The tests verify the ingestion of VPC, Subnet, Security Group, and EC2 Instance data.

## Current Status

**Week 1 – AWS Ingestion: Completed**

The basic AWS ingestion layer is working with mock/sandbox data and provides the foundation for the next stages of the AeroDrift project.

## Future Scope

* Integration with a live AWS environment using Boto3.
* Expanded cloud resource ingestion.
* Cloud topology construction.
* Resource relationship analysis.
* Infrastructure issue detection.
* Remediation recommendations.
* Automated remediation workflows.

## Author

**Rinky Jadaun**

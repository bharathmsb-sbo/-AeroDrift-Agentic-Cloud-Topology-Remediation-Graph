
import asyncio


class CloudIngestion:
    def __init__(self):
        self.resources = {
            "vpcs": [],
            "subnets": [],
            "security_groups": [],
            "ec2_instances": []
        }

    async def collect_mock_data(self):
        await asyncio.sleep(0.1)

        self.resources = {
            "vpcs": [
                {"vpc_id": "vpc-001", "cidr": "10.0.0.0/16"}
            ],
            "subnets": [
                {"subnet_id": "subnet-001", "vpc_id": "vpc-001"}
            ],
            "security_groups": [
                {"group_id": "sg-001", "name": "web-sg"}
            ],
            "ec2_instances": [
                {"instance_id": "i-001", "state": "running"}
            ]
        }

        return self.resources


async def main():
    ingestion = CloudIngestion()
    data = await ingestion.collect_mock_data()

    for resource_type, resources in data.items():
        print(f"{resource_type}: {resources}")


if __name__ == "__main__":
    asyncio.run(main())
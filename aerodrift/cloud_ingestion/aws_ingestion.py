"""
AWS Ingestion: Asynchronous boto3 wrappers for concurrent AWS API polling.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


@dataclass
class VPC:
    """Represents an AWS VPC."""
    vpc_id: str
    cidr_block: str
    state: str
    tags: Dict[str, str]


@dataclass
class Subnet:
    """Represents an AWS Subnet."""
    subnet_id: str
    vpc_id: str
    cidr_block: str
    availability_zone: str
    state: str


@dataclass
class SecurityGroup:
    """Represents an AWS Security Group."""
    group_id: str
    group_name: str
    description: str
    vpc_id: str
    ingress_rules: List[Dict[str, Any]]
    egress_rules: List[Dict[str, Any]]


@dataclass
class EC2Instance:
    """Represents an AWS EC2 Instance."""
    instance_id: str
    instance_type: str
    state: str
    vpc_id: str
    subnet_id: str
    private_ip: str
    public_ip: Optional[str]
    security_groups: List[str]


class AWSIngestion:
    """
    Asynchronous AWS ingestion engine for concurrent API polling.
    
    This class provides high-performance concurrent collection of AWS state data
    including VPCs, EC2 instances, subnets, and security groups.
    """
    
    def __init__(self, region: str = "us-east-1", use_mock: bool = False):
        """
        Initialize AWS ingestion engine.
        
        Args:
            region: AWS region to query
            use_mock: If True, use mock data instead of real AWS APIs
        """
        self.region = region
        self.use_mock = use_mock
        
        if not use_mock:
            self.ec2_client = boto3.client('ec2', region_name=region)
            self.ec2_resource = boto3.resource('ec2', region_name=region)
        else:
            from .mock_data import MockAWSData
            self.mock_data = MockAWSData()
            logger.info("Using mock AWS data for testing")
    
    async def collect_vpcs(self) -> List[VPC]:
        """
        Asynchronously collect all VPCs in the region.
        
        Returns:
            List of VPC objects
        """
        if self.use_mock:
            return await asyncio.to_thread(self.mock_data.get_vpcs)
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.ec2_client.describe_vpcs()
            )
            
            vpcs = []
            for vpc_data in response['Vpcs']:
                vpcs.append(VPC(
                    vpc_id=vpc_data['VpcId'],
                    cidr_block=vpc_data['CidrBlock'],
                    state=vpc_data['State'],
                    tags={tag['Key']: tag['Value'] for tag in vpc_data.get('Tags', [])}
                ))
            
            logger.info(f"Collected {len(vpcs)} VPCs")
            return vpcs
            
        except ClientError as e:
            logger.error(f"Error collecting VPCs: {e}")
            raise
    
    async def collect_subnets(self) -> List[Subnet]:
        """
        Asynchronously collect all subnets in the region.
        
        Returns:
            List of Subnet objects
        """
        if self.use_mock:
            return await asyncio.to_thread(self.mock_data.get_subnets)
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.ec2_client.describe_subnets()
            )
            
            subnets = []
            for subnet_data in response['Subnets']:
                subnets.append(Subnet(
                    subnet_id=subnet_data['SubnetId'],
                    vpc_id=subnet_data['VpcId'],
                    cidr_block=subnet_data['CidrBlock'],
                    availability_zone=subnet_data['AvailabilityZone'],
                    state=subnet_data['State']
                ))
            
            logger.info(f"Collected {len(subnets)} subnets")
            return subnets
            
        except ClientError as e:
            logger.error(f"Error collecting subnets: {e}")
            raise
    
    async def collect_security_groups(self) -> List[SecurityGroup]:
        """
        Asynchronously collect all security groups in the region.
        
        Returns:
            List of SecurityGroup objects
        """
        if self.use_mock:
            return await asyncio.to_thread(self.mock_data.get_security_groups)
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.ec2_client.describe_security_groups()
            )
            
            security_groups = []
            for sg_data in response['SecurityGroups']:
                ingress_rules = []
                for rule in sg_data.get('IpPermissions', []):
                    for ip_range in rule.get('IpRanges', []):
                        ingress_rules.append({
                            'protocol': rule.get('IpProtocol', '-1'),
                            'from_port': rule.get('FromPort'),
                            'to_port': rule.get('ToPort'),
                            'cidr': ip_range.get('CidrIp'),
                            'description': ip_range.get('Description', '')
                        })
                
                egress_rules = []
                for rule in sg_data.get('IpPermissionsEgress', []):
                    for ip_range in rule.get('IpRanges', []):
                        egress_rules.append({
                            'protocol': rule.get('IpProtocol', '-1'),
                            'from_port': rule.get('FromPort'),
                            'to_port': rule.get('ToPort'),
                            'cidr': ip_range.get('CidrIp'),
                            'description': ip_range.get('Description', '')
                        })
                
                security_groups.append(SecurityGroup(
                    group_id=sg_data['GroupId'],
                    group_name=sg_data['GroupName'],
                    description=sg_data['Description'],
                    vpc_id=sg_data.get('VpcId', ''),
                    ingress_rules=ingress_rules,
                    egress_rules=egress_rules
                ))
            
            logger.info(f"Collected {len(security_groups)} security groups")
            return security_groups
            
        except ClientError as e:
            logger.error(f"Error collecting security groups: {e}")
            raise
    
    async def collect_ec2_instances(self) -> List[EC2Instance]:
        """
        Asynchronously collect all EC2 instances in the region.
        
        Returns:
            List of EC2Instance objects
        """
        if self.use_mock:
            return await asyncio.to_thread(self.mock_data.get_ec2_instances)
        
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.ec2_client.describe_instances()
            )
            
            instances = []
            for reservation in response['Reservations']:
                for instance_data in reservation['Instances']:
                    security_groups = [
                        sg['GroupId'] for sg in instance_data.get('SecurityGroups', [])
                    ]
                    
                    instances.append(EC2Instance(
                        instance_id=instance_data['InstanceId'],
                        instance_type=instance_data['InstanceType'],
                        state=instance_data['State']['Name'],
                        vpc_id=instance_data.get('VpcId', ''),
                        subnet_id=instance_data.get('SubnetId', ''),
                        private_ip=instance_data.get('PrivateIpAddress', ''),
                        public_ip=instance_data.get('PublicIpAddress'),
                        security_groups=security_groups
                    ))
            
            logger.info(f"Collected {len(instances)} EC2 instances")
            return instances
            
        except ClientError as e:
            logger.error(f"Error collecting EC2 instances: {e}")
            raise
    
    async def collect_all_resources(self) -> Dict[str, Any]:
        """
        Concurrently collect all AWS resources.
        
        Returns:
            Dictionary containing all collected resources
        """
        logger.info("Starting concurrent AWS resource collection...")
        
        # Run all collection tasks concurrently
        vpcs, subnets, security_groups, instances = await asyncio.gather(
            self.collect_vpcs(),
            self.collect_subnets(),
            self.collect_security_groups(),
            self.collect_ec2_instances()
        )
        
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'region': self.region,
            'vpcs': vpcs,
            'subnets': subnets,
            'security_groups': security_groups,
            'instances': instances
        }
    
    async def continuous_polling(self, interval: int = 60, callback=None):
        """
        Continuously poll AWS resources at specified intervals.
        
        Args:
            interval: Polling interval in seconds
            callback: Optional callback function to process collected data
        """
        logger.info(f"Starting continuous polling with {interval}s interval")
        
        while True:
            try:
                data = await self.collect_all_resources()
                if callback:
                    await callback(data)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error during polling: {e}")
                await asyncio.sleep(interval)  # Wait before retrying

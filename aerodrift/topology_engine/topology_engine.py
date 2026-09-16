"""
Topology Engine: NetworkX-based cloud architecture modeling for path-finding queries.
"""

import networkx as nx
import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ResourceType(Enum):
    """Types of cloud resources."""
    VPC = "vpc"
    SUBNET = "subnet"
    SECURITY_GROUP = "security_group"
    EC2_INSTANCE = "ec2_instance"
    INTERNET = "internet"
    DATABASE = "database"


@dataclass
class ResourceNode:
    """Represents a node in the cloud topology graph."""
    resource_id: str
    resource_type: ResourceType
    name: str
    attributes: Dict[str, Any]
    
    def __hash__(self):
        return hash(self.resource_id)


class TopologyEngine:
    """
    Models cloud architecture as a directed graph using NetworkX.
    
    Enables complex path-finding queries such as:
    - "Is there a path from the Internet to Database X?"
    - "What resources can access this security group?"
    - "Find all exposed databases"
    """
    
    def __init__(self):
        """Initialize the topology engine with an empty directed graph."""
        self.graph = nx.DiGraph()
        self.resource_index: Dict[str, ResourceNode] = {}
        self.internet_gateway_id = "internet-gateway-0.0.0.0/0"
    
    def add_resource(self, resource: ResourceNode):
        """
        Add a resource node to the topology graph.
        
        Args:
            resource: ResourceNode to add
        """
        self.graph.add_node(resource.resource_id, **resource.attributes)
        self.resource_index[resource.resource_id] = resource
        logger.debug(f"Added resource node: {resource.resource_id} ({resource.resource_type.value})")
    
    def add_network_edge(self, source_id: str, target_id: str, 
                        edge_type: str, attributes: Optional[Dict[str, Any]] = None):
        """
        Add a network pathway edge between resources.
        
        Args:
            source_id: Source resource ID
            target_id: Target resource ID
            edge_type: Type of network connection (e.g., 'ingress', 'egress', 'contains')
            attributes: Additional edge attributes
        """
        edge_attrs = attributes or {}
        edge_attrs['edge_type'] = edge_type
        
        self.graph.add_edge(source_id, target_id, **edge_attrs)
        logger.debug(f"Added edge: {source_id} -> {target_id} ({edge_type})")
    
    def build_from_aws_data(self, aws_data: Dict[str, Any]):
        """
        Build the topology graph from collected AWS data.
        
        Args:
            aws_data: Dictionary containing VPCs, subnets, security groups, and instances
        """
        logger.info("Building topology graph from AWS data...")
        
        # Add Internet gateway node
        internet_node = ResourceNode(
            resource_id=self.internet_gateway_id,
            resource_type=ResourceType.INTERNET,
            name="Internet (0.0.0.0/0)",
            attributes={"cidr": "0.0.0.0/0", "is_internet": True}
        )
        self.add_resource(internet_node)
        
        # Add VPCs
        for vpc in aws_data.get('vpcs', []):
            vpc_node = ResourceNode(
                resource_id=vpc.vpc_id,
                resource_type=ResourceType.VPC,
                name=vpc.tags.get('Name', vpc.vpc_id),
                attributes={
                    'cidr_block': vpc.cidr_block,
                    'state': vpc.state,
                    'tags': vpc.tags
                }
            )
            self.add_resource(vpc_node)
        
        # Add Subnets and connect to VPCs
        for subnet in aws_data.get('subnets', []):
            subnet_node = ResourceNode(
                resource_id=subnet.subnet_id,
                resource_type=ResourceType.SUBNET,
                name=subnet.subnet_id,
                attributes={
                    'cidr_block': subnet.cidr_block,
                    'availability_zone': subnet.availability_zone,
                    'state': subnet.state
                }
            )
            self.add_resource(subnet_node)
            self.add_network_edge(subnet.vpc_id, subnet.subnet_id, 'contains')
        
        # Add Security Groups and connect to VPCs
        for sg in aws_data.get('security_groups', []):
            sg_node = ResourceNode(
                resource_id=sg.group_id,
                resource_type=ResourceType.SECURITY_GROUP,
                name=sg.group_name,
                attributes={
                    'description': sg.description,
                    'vpc_id': sg.vpc_id,
                    'ingress_rules': sg.ingress_rules,
                    'egress_rules': sg.egress_rules
                }
            )
            self.add_resource(sg_node)
            
            if sg.vpc_id:
                self.add_network_edge(sg.vpc_id, sg.group_id, 'contains')
            
            # Add edges for ingress rules (who can access this SG)
            for rule in sg.ingress_rules:
                cidr = rule.get('cidr', '')
                if cidr == '0.0.0.0/0':
                    # Internet can access this SG
                    self.add_network_edge(
                        self.internet_gateway_id,
                        sg.group_id,
                        'ingress',
                        {
                            'protocol': rule.get('protocol'),
                            'from_port': rule.get('from_port'),
                            'to_port': rule.get('to_port'),
                            'description': rule.get('description', '')
                        }
                    )
                elif cidr:
                    # Create a CIDR node for internal networks
                    cidr_node_id = f"cidr-{cidr.replace('/', '-')}"
                    if cidr_node_id not in self.resource_index:
                        cidr_node = ResourceNode(
                            resource_id=cidr_node_id,
                            resource_type=ResourceType.SUBNET,
                            name=f"CIDR: {cidr}",
                            attributes={'cidr': cidr, 'is_cidr': True}
                        )
                        self.add_resource(cidr_node)
                    
                    self.add_network_edge(
                        cidr_node_id,
                        sg.group_id,
                        'ingress',
                        {
                            'protocol': rule.get('protocol'),
                            'from_port': rule.get('from_port'),
                            'to_port': rule.get('to_port'),
                            'description': rule.get('description', '')
                        }
                    )
        
        # Add EC2 Instances and connect to Subnets and Security Groups
        for instance in aws_data.get('instances', []):
            # Determine if this is a database based on instance type or name
            is_database = 'db' in instance.instance_type.lower() or 'database' in instance.instance_id.lower()
            
            instance_node = ResourceNode(
                resource_id=instance.instance_id,
                resource_type=ResourceType.DATABASE if is_database else ResourceType.EC2_INSTANCE,
                name=instance.instance_id,
                attributes={
                    'instance_type': instance.instance_type,
                    'state': instance.state,
                    'private_ip': instance.private_ip,
                    'public_ip': instance.public_ip,
                    'is_database': is_database
                }
            )
            self.add_resource(instance_node)
            
            # Connect to subnet
            if instance.subnet_id:
                self.add_network_edge(instance.subnet_id, instance.instance_id, 'contains')
            
            # Connect to security groups
            for sg_id in instance.security_groups:
                self.add_network_edge(sg_id, instance.instance_id, 'protects')
        
        logger.info(f"Topology graph built with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
    
    def find_path_to_internet(self, resource_id: str) -> Optional[List[str]]:
        """
        Find if there's a path from a resource to the Internet.
        
        Args:
            resource_id: Resource ID to check
            
        Returns:
            List of resource IDs representing the path, or None if no path exists
        """
        try:
            path = nx.shortest_path(self.graph, resource_id, self.internet_gateway_id)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def find_path_from_internet(self, resource_id: str) -> Optional[List[str]]:
        """
        Find if there's a path from the Internet to a resource (external access).
        
        Args:
            resource_id: Resource ID to check
            
        Returns:
            List of resource IDs representing the path, or None if no path exists
        """
        try:
            path = nx.shortest_path(self.graph, self.internet_gateway_id, resource_id)
            return path
        except nx.NetworkXNoPath:
            return None
    
    def find_exposed_databases(self) -> List[Dict[str, Any]]:
        """
        Find all database resources that are accessible from the Internet.
        
        Returns:
            List of dictionaries containing exposed database info and paths
        """
        exposed_databases = []
        
        for resource_id, resource in self.resource_index.items():
            if resource.resource_type == ResourceType.DATABASE:
                path = self.find_path_from_internet(resource_id)
                if path:
                    exposed_databases.append({
                        'resource_id': resource_id,
                        'name': resource.name,
                        'path': path,
                        'path_description': self._describe_path(path)
                    })
        
        return exposed_databases
    
    def find_resources_with_internet_access(self) -> List[str]:
        """
        Find all resources that can access the Internet.
        
        Returns:
            List of resource IDs
        """
        resources_with_access = []
        
        for resource_id in self.graph.nodes():
            if resource_id != self.internet_gateway_id:
                if self.find_path_to_internet(resource_id):
                    resources_with_access.append(resource_id)
        
        return resources_with_access
    
    def get_resource_details(self, resource_id: str) -> Optional[ResourceNode]:
        """
        Get details about a specific resource.
        
        Args:
            resource_id: Resource ID to look up
            
        Returns:
            ResourceNode or None if not found
        """
        return self.resource_index.get(resource_id)
    
    def get_connected_resources(self, resource_id: str, direction: str = 'both') -> List[str]:
        """
        Get resources connected to a given resource.
        
        Args:
            resource_id: Resource ID
            direction: 'in', 'out', or 'both' for incoming/outgoing/both edges
            
        Returns:
            List of connected resource IDs
        """
        if direction == 'in':
            return list(self.graph.predecessors(resource_id))
        elif direction == 'out':
            return list(self.graph.successors(resource_id))
        else:
            return list(self.graph.predecessors(resource_id)) + list(self.graph.successors(resource_id))
    
    def _describe_path(self, path: List[str]) -> str:
        """
        Generate a human-readable description of a path.
        
        Args:
            path: List of resource IDs
            
        Returns:
            Human-readable path description
        """
        descriptions = []
        for resource_id in path:
            resource = self.resource_index.get(resource_id)
            if resource:
                descriptions.append(f"{resource.resource_type.value}: {resource.name}")
            else:
                descriptions.append(f"Unknown: {resource_id}")
        
        return " -> ".join(descriptions)
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the topology graph.
        
        Returns:
            Dictionary containing graph statistics
        """
        resource_type_counts = {}
        for resource in self.resource_index.values():
            resource_type_counts[resource.resource_type.value] = \
                resource_type_counts.get(resource.resource_type.value, 0) + 1
        
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'resource_type_counts': resource_type_counts,
            'is_connected': nx.is_weakly_connected(self.graph),
            'exposed_databases': len(self.find_exposed_databases())
        }
    
    def export_graph(self, format: str = 'gexf') -> str:
        """
        Export the graph to a file for visualization.
        
        Args:
            format: Export format ('gexf', 'graphml', 'json')
            
        Returns:
            Path to the exported file
        """
        import tempfile
        import os
        
        temp_dir = tempfile.gettempdir()
        timestamp = str(int(__import__('time').time()))
        filename = f"aerodrift_topology_{timestamp}.{format}"
        filepath = os.path.join(temp_dir, filename)
        
        if format == 'gexf':
            nx.write_gexf(self.graph, filepath)
        elif format == 'graphml':
            nx.write_graphml(self.graph, filepath)
        elif format == 'json':
            from networkx.readwrite import json_graph
            import json
            data = json_graph.node_link_data(self.graph)
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Graph exported to {filepath}")
        return filepath
    
    def clear(self):
        """Clear the topology graph."""
        self.graph.clear()
        self.resource_index.clear()
        logger.info("Topology graph cleared")

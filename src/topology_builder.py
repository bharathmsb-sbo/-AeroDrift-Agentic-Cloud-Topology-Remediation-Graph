
class TopologyBuilder:
    def build_topology(self, resources):
        topology = {
            "nodes": [],
            "edges": []
        }

        for vpc in resources["vpcs"]:
            topology["nodes"].append({
                "id": vpc["vpc_id"],
                "type": "vpc"
            })

        for subnet in resources["subnets"]:
            topology["nodes"].append({
                "id": subnet["subnet_id"],
                "type": "subnet"
            })

            topology["edges"].append({
                "source": subnet["vpc_id"],
                "target": subnet["subnet_id"],
                "relationship": "contains"
            })

        for group in resources["security_groups"]:
            topology["nodes"].append({
                "id": group["group_id"],
                "type": "security_group"
            })

        for instance in resources["ec2_instances"]:
            topology["nodes"].append({
                "id": instance["instance_id"],
                "type": "ec2"
            })

        return topology
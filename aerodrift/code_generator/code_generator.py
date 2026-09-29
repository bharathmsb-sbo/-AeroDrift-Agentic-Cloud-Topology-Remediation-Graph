"""
Code Generator: Programmatically writes Python remediation scripts using ast module.
"""

import ast
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class RemediationAction:
    """Represents a remediation action to be generated."""
    action_type: str
    resource_id: str
    parameters: Dict[str, Any]
    description: str


class CodeGenerator:
    """
    Generates Python remediation scripts using the ast module.
    
    This engine programmatically writes Python code on the fly based on the
    specific drift detected, enabling autonomous self-healing of cloud infrastructure.
    """
    
    def __init__(self):
        """Initialize the code generator."""
        self.imports = [
            "import boto3",
            "from botocore.exceptions import ClientError"
        ]
    
    def generate_remediation_script(self, drift_event) -> str:
        """
        Generate a remediation script for a given drift event.
        
        Args:
            drift_event: DriftEvent object requiring remediation
            
        Returns:
            Generated Python code as string
        """
        logger.info(f"Generating remediation script for event: {drift_event.event_id}")
        
        # Build the AST
        module = ast.Module(body=[], type_ignores=[])
        
        # Add imports
        for import_stmt in self.imports:
            module.body.append(ast.parse(import_stmt).body[0])
        
        # Add function definition
        function_name = f"remediate_{drift_event.drift_type.value}"
        function_def = self._create_remediation_function(drift_event, function_name)
        module.body.append(function_def)
        
        # Add main execution block
        main_call = ast.parse(f"""
if __name__ == "__main__":
    {function_name}()
""").body
        module.body.extend(main_call)
        
        # Fix line numbers and compile
        module = ast.fix_missing_locations(module)
        
        # Convert AST to code
        code = ast.unparse(module)
        
        logger.info("Remediation script generated successfully")
        return code
    
    def _create_remediation_function(self, drift_event, function_name: str) -> ast.FunctionDef:
        """
        Create a function definition for remediation.
        
        Args:
            drift_event: DriftEvent object
            function_name: Name of the function
            
        Returns:
            AST FunctionDef node
        """
        # Function body
        body = []
        
        # Add docstring
        docstring = ast.Expr(
            value=ast.Constant(
                value=f"Remediate {drift_event.description}",
                kind=None
            )
        )
        body.append(docstring)
        
        # Generate specific remediation logic based on drift type
        if drift_event.drift_type.value == "security_group_change":
            body.extend(self._generate_security_group_remediation(drift_event))
        elif drift_event.drift_type.value == "exposed_database":
            body.extend(self._generate_database_exposure_remediation(drift_event))
        elif drift_event.drift_type.value == "new_public_instance":
            body.extend(self._generate_public_instance_remediation(drift_event))
        else:
            body.extend(self._generate_generic_remediation(drift_event))
        
        # Create function definition
        function_def = ast.FunctionDef(
            name=function_name,
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                kwarg=None,
                vararg=None
            ),
            body=body,
            decorator_list=[],
            returns=None
        )
        
        return function_def
    
    def _generate_security_group_remediation(self, drift_event) -> List[ast.stmt]:
        """
        Generate remediation code for security group changes.
        
        Args:
            drift_event: DriftEvent for security group change
            
        Returns:
            List of AST statements
        """
        body = []
        
        # Extract security group details from metadata
        metadata = drift_event.metadata
        new_rule = metadata.get('new_rule', {})
        sg_id = drift_event.resource_id
        
        # Create boto3 client
        body.append(ast.parse("ec2 = boto3.client('ec2')").body[0])
        
        # Build revoke parameters
        revoke_params = {
            'GroupId': sg_id,
            'IpPermissions': [{
                'IpProtocol': new_rule.get('protocol', '-1'),
                'FromPort': new_rule.get('from_port'),
                'ToPort': new_rule.get('to_port'),
                'IpRanges': [{
                    'CidrIp': new_rule.get('cidr', '0.0.0.0/0')
                }]
            }]
        }
        
        # Create the revoke call
        revoke_call = ast.parse(f"""
try:
    response = ec2.revoke_security_group_ingress(
        GroupId='{sg_id}',
        IpPermissions=[{{
            'IpProtocol': '{new_rule.get('protocol', '-1')}',
            'FromPort': {new_rule.get('from_port') if new_rule.get('from_port') is not None else 'None'},
            'ToPort': {new_rule.get('to_port') if new_rule.get('to_port') is not None else 'None'},
            'IpRanges': [{{
                'CidrIp': '{new_rule.get('cidr', '0.0.0.0/0')}'
            }}]
        }}]
    )
    print(f"Successfully revoked ingress rule from {{'{sg_id}'}}")
except ClientError as e:
    print(f"Error revoking ingress rule: {{e}}")
""").body
        
        body.extend(revoke_call)
        
        return body
    
    def _generate_database_exposure_remediation(self, drift_event) -> List[ast.stmt]:
        """
        Generate remediation code for exposed database.
        
        Args:
            drift_event: DriftEvent for exposed database
            
        Returns:
            List of AST statements
        """
        body = []
        
        # Get the exposure path from metadata
        metadata = drift_event.metadata
        exposure_path = metadata.get('exposure_path', [])
        
        # Find the security group in the path that has the internet-facing rule
        if len(exposure_path) >= 2:
            # The security group is typically the second node in the path
            sg_id = exposure_path[1] if len(exposure_path) > 1 else drift_event.resource_id
            
            # Create boto3 client
            body.append(ast.parse("ec2 = boto3.client('ec2')").body[0])
            
            # For database exposure, we typically need to revoke the specific rule
            # This is a simplified version - in production, you'd analyze the specific rule
            revoke_code = f"""
try:
    # Get security group rules
    sg_info = ec2.describe_security_groups(GroupIds=['{sg_id}'])
    
    # Revoke any internet-facing ingress rules (except necessary ones)
    for rule in sg_info['SecurityGroups'][0]['IpPermissions']:
        for ip_range in rule.get('IpRanges', []):
            if ip_range.get('CidrIp') == '0.0.0.0/0':
                ec2.revoke_security_group_ingress(
                    GroupId='{sg_id}',
                    IpPermissions=[rule]
                )
                print(f"Revoked internet-facing rule from {{'{sg_id}'}}")
    
    print(f"Database exposure remediated for {{'{drift_event.resource_id}'}}")
except ClientError as e:
    print(f"Error remediating database exposure: {{e}}")
"""
            body.extend(ast.parse(revoke_code).body)
        else:
            # Fallback: log the issue
            body.append(ast.parse(f"print('Cannot auto-remediate: insufficient path information')").body[0])
        
        return body
    
    def _generate_public_instance_remediation(self, drift_event) -> List[ast.stmt]:
        """
        Generate remediation code for public instance.
        
        Args:
            drift_event: DriftEvent for public instance
            
        Returns:
            List of AST statements
        """
        body = []
        
        instance_id = drift_event.resource_id
        
        # Create boto3 client
        body.append(ast.parse("ec2 = boto3.client('ec2')").body[0])
        
        # To remove public IP, we typically need to:
        # 1. Disassociate the elastic IP (if exists)
        # 2. Or modify the instance to be in a private subnet
        
        # For safety, we'll just log and suggest manual review
        remediation_code = f"""
try:
    # Note: Removing public IP requires subnet changes or elastic IP disassociation
    # This is a sensitive operation that requires manual verification
    
    response = ec2.describe_instances(InstanceIds=['{instance_id}'])
    instance = response['Reservations'][0]['Instances'][0]
    
    print(f"Instance {{'{instance_id}'}} has public IP: {{instance.get('PublicIpAddress')}}")
    print("REMEDIATION REQUIRED: Review instance subnet configuration")
    print("Consider moving instance to a private subnet")
    
except ClientError as e:
    print(f"Error describing instance: {{e}}")
"""
        body.extend(ast.parse(remediation_code).body)
        
        return body
    
    def _generate_generic_remediation(self, drift_event) -> List[ast.stmt]:
        """
        Generate generic remediation code for unknown drift types.
        
        Args:
            drift_event: DriftEvent object
            
        Returns:
            List of AST statements
        """
        body = []
        
        # Generic logging and notification
        code = f"""
print(f"Drift event detected: {{'{drift_event.event_id}'}}")
print(f"Type: {{'{drift_event.drift_type.value}'}}")
print(f"Resource: {{'{drift_event.resource_id}'}}")
print(f"Description: {{'{drift_event.description}'}}")
print("Manual remediation required for this drift type")
"""
        body.extend(ast.parse(code).body)
        
        return body
    
    def generate_batch_remediation(self, drift_events: List[Any]) -> str:
        """
        Generate a batch remediation script for multiple drift events.
        
        Args:
            drift_events: List of DriftEvent objects
            
        Returns:
            Generated Python code as string
        """
        logger.info(f"Generating batch remediation script for {len(drift_events)} events")
        
        # Build the AST
        module = ast.Module(body=[], type_ignores=[])
        
        # Add imports
        for import_stmt in self.imports:
            module.body.append(ast.parse(import_stmt).body[0])
        
        # Add individual remediation functions
        for event in drift_events:
            if event.remediation_required:
                function_name = f"remediate_{event.event_id.replace('-', '_')}"
                function_def = self._create_remediation_function(event, function_name)
                module.body.append(function_def)
        
        # Add main function that calls all remediations
        main_function = self._create_batch_main_function(drift_events)
        module.body.append(main_function)
        
        # Add main execution block
        main_call = ast.parse("""
if __name__ == "__main__":
    main()
""").body
        module.body.extend(main_call)
        
        # Fix line numbers and compile
        module = ast.fix_missing_locations(module)
        
        # Convert AST to code
        code = ast.unparse(module)
        
        logger.info("Batch remediation script generated successfully")
        return code
    
    def _create_batch_main_function(self, drift_events: List[Any]) -> ast.FunctionDef:
        """
        Create a main function that calls all individual remediation functions.
        
        Args:
            drift_events: List of DriftEvent objects
            
        Returns:
            AST FunctionDef node
        """
        body = []
        
        # Add docstring
        body.append(ast.Expr(
            value=ast.Constant(
                value="Execute all remediation functions",
                kind=None
            )
        ))
        
        # Add function calls for each event
        for event in drift_events:
            if event.remediation_required:
                function_name = f"remediate_{event.event_id.replace('-', '_')}"
                call = ast.Expr(
                    value=ast.Call(
                        func=ast.Name(id=function_name, ctx=ast.Load()),
                        args=[],
                        keywords=[]
                    )
                )
                body.append(call)
        
        # Create function definition
        function_def = ast.FunctionDef(
            name="main",
            args=ast.arguments(
                posonlyargs=[],
                args=[],
                kwonlyargs=[],
                kw_defaults=[],
                defaults=[],
                kwarg=None,
                vararg=None
            ),
            body=body,
            decorator_list=[],
            returns=None
        )
        
        return function_def
    
    def validate_generated_code(self, code: str) -> bool:
        """
        Validate that generated code is syntactically correct.
        
        Args:
            code: Generated Python code
            
        Returns:
            True if code is valid, False otherwise
        """
        try:
            ast.parse(code)
            logger.info("Generated code validation passed")
            return True
        except SyntaxError as e:
            logger.error(f"Generated code validation failed: {e}")
            return False

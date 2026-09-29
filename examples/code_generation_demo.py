"""
Code generation demonstration for AeroDrift.

This example shows how the code generator creates remediation scripts.
"""

from aerodrift.drift_detection import DriftDetector, DriftEvent, DriftType, DriftSeverity
from aerodrift.code_generator import CodeGenerator
from aerodrift.cli_dashboard import CLIDashboard
from datetime import datetime, timezone


def demonstrate_code_generation():
    """Demonstrate automatic code generation for remediation."""
    
    print("Initializing code generation demonstration...")
    code_generator = CodeGenerator()
    dashboard = CLIDashboard()
    
    # Create a sample drift event
    drift_event = DriftEvent(
        event_id="drift-sample-001",
        drift_type=DriftType.SECURITY_GROUP_CHANGE,
        severity=DriftSeverity.CRITICAL,
        timestamp=datetime.now(timezone.utc),
        resource_id="sg-secure-db",
        resource_type="security_group",
        description="Security group secure-database-sg now allows Internet access on port 3306",
        affected_resources=["sg-secure-db", "i-db-prod-001"],
        remediation_required=True,
        metadata={
            'new_rule': {
                'protocol': 'tcp',
                'from_port': 3306,
                'to_port': 3306,
                'cidr': '0.0.0.0/0',
                'description': 'VULNERABLE: Accidentally opened to internet'
            }
        }
    )
    
    print(f"\n1. Sample drift event: {drift_event.event_id}")
    print(f"   Type: {drift_event.drift_type.value}")
    print(f"   Severity: {drift_event.severity.value}")
    print(f"   Description: {drift_event.description}")
    
    # Generate remediation code
    print("\n2. Generating remediation code...")
    remediation_code = code_generator.generate_remediation_script(drift_event)
    
    # Validate the generated code
    print("\n3. Validating generated code...")
    is_valid = code_generator.validate_generated_code(remediation_code)
    
    if is_valid:
        dashboard.print_success("Generated code is valid!")
    else:
        dashboard.print_error("Generated code validation failed!")
        return
    
    # Display the generated code
    print("\n4. Generated remediation code:")
    dashboard.display_remediation_code(remediation_code)
    
    # Demonstrate batch code generation
    print("\n5. Demonstrating batch code generation...")
    
    # Create multiple drift events
    drift_events = [
        drift_event,
        DriftEvent(
            event_id="drift-sample-002",
            drift_type=DriftType.SECURITY_GROUP_CHANGE,
            severity=DriftSeverity.HIGH,
            timestamp=datetime.now(timezone.utc),
            resource_id="sg-web-server",
            resource_type="security_group",
            description="Security group web-server-sg has new SSH rule",
            affected_resources=["sg-web-server"],
            remediation_required=True,
            metadata={
                'new_rule': {
                    'protocol': 'tcp',
                    'from_port': 22,
                    'to_port': 22,
                    'cidr': '0.0.0.0/0',
                    'description': 'SSH access - TEMPORARY'
                }
            }
        )
    ]
    
    batch_code = code_generator.generate_batch_remediation(drift_events)
    
    print("\n6. Batch remediation code:")
    dashboard.display_remediation_code(batch_code)
    
    print("\n[+] Code generation demonstration completed!")


if __name__ == "__main__":
    demonstrate_code_generation()

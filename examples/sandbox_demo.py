"""
Execution sandbox demonstration for AeroDrift.

This example shows how the execution sandbox securely runs generated code.
"""

from aerodrift.utils import ExecutionSandbox
from aerodrift.cli_dashboard import CLIDashboard


def demonstrate_sandbox():
    """Demonstrate secure code execution in sandbox."""
    
    print("Initializing execution sandbox demonstration...")
    sandbox = ExecutionSandbox()
    dashboard = CLIDashboard()
    
    # Test 1: Safe code execution
    print("\n1. Testing safe code execution...")
    safe_code = """
print("Hello from the sandbox!")
result = 2 + 2
print(f"Calculation result: {result}")
data = {"status": "success", "value": 42}
print(f"Data: {data}")
"""
    
    result = sandbox.execute(safe_code)
    
    if result['success']:
        dashboard.print_success("Safe code executed successfully")
        print(f"Output: {result['output']}")
    else:
        dashboard.print_error(f"Safe code execution failed: {result['error']}")
    
    # Test 2: Code validation (dangerous code)
    print("\n2. Testing code validation with dangerous code...")
    dangerous_code = """
import os
print("Attempting to access operating system...")
os.system("echo 'This should be blocked'")
"""
    
    is_valid, error_msg = sandbox.validate_code(dangerous_code)
    
    if not is_valid:
        dashboard.print_success("Dangerous code was correctly blocked")
        print(f"Validation error: {error_msg}")
    else:
        dashboard.print_error("Dangerous code validation should have failed!")
    
    # Test 3: Invalid syntax
    print("\n3. Testing code validation with invalid syntax...")
    invalid_code = """
print("Missing closing parenthesis"
"""
    
    is_valid, error_msg = sandbox.validate_code(invalid_code)
    
    if not is_valid:
        dashboard.print_success("Invalid syntax was correctly detected")
        print(f"Validation error: {error_msg}")
    else:
        dashboard.print_error("Invalid syntax should have been detected!")
    
    # Test 4: Remediation-style code
    print("\n4. Testing remediation-style code execution...")
    remediation_code = """
print("Starting remediation simulation...")
security_groups = ["sg-123", "sg-456"]
for sg in security_groups:
    print(f"Processing security group: {sg}")
    
print("Remediation simulation completed")
result = {"remediated": True, "groups_processed": len(security_groups)}
print(f"Result: {result}")
"""
    
    result = sandbox.execute_remediation(remediation_code)
    
    if result['success']:
        dashboard.print_success("Remediation code executed successfully")
        print(f"Output: {result['output']}")
    else:
        dashboard.print_error(f"Remediation code execution failed: {result['error']}")
    
    # Test 5: Execution history
    print("\n5. Checking execution history...")
    history = sandbox.get_execution_history()
    dashboard.print_info(f"Total executions in history: {len(history)}")
    
    for i, entry in enumerate(history, 1):
        status = "[+]" if entry['success'] else "[-]"
        print(f"   {status} Execution {i}: {entry['timestamp']}")
        print(f"      Success: {entry['success']}, Output length: {entry['output_length']}")
    
    # Test 6: Sandbox self-test
    print("\n6. Running sandbox self-test...")
    test_result = sandbox.test_sandbox()
    
    if test_result['success']:
        dashboard.print_success("Sandbox self-test passed")
        print(f"Test output: {test_result['output']}")
    else:
        dashboard.print_error(f"Sandbox self-test failed: {test_result['error']}")
    
    print("\n[+] Sandbox demonstration completed!")


if __name__ == "__main__":
    demonstrate_sandbox()

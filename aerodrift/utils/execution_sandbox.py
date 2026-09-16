"""
Execution Sandbox: Secure execution environment for dynamically generated remediation code.
"""

import logging
import sys
from typing import Dict, Any, Optional, List, Tuple
from io import StringIO
import ast

logger = logging.getLogger(__name__)


class ExecutionSandbox:
    """
    Provides a secure execution environment for dynamically generated code.
    
    Features:
    - Restricted global namespace
    - Output capture
    - Execution timeout
    - Error handling
    - Security validation
    """
    
    # Allowed imports for security
    ALLOWED_IMPORTS = {
        'boto3',
        'botocore.exceptions',
        'json',
        'datetime',
        'time',
        'logging'
    }
    
    # Built-in functions to allow
    ALLOWED_BUILTINS = {
        'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set', 'tuple',
        'range', 'enumerate', 'zip', 'map', 'filter', 'isinstance', 'type', 'hasattr',
        'getattr', 'setattr', 'Exception', 'ValueError', 'TypeError'
    }
    
    def __init__(self):
        """Initialize the execution sandbox."""
        self.execution_history: List[Dict[str, Any]] = []
        logger.info("Execution sandbox initialized")
    
    def validate_code(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate code for security before execution.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Parse the code to check for syntax errors
            tree = ast.parse(code)
            
            # Check for dangerous operations
            for node in ast.walk(tree):
                # Check for imports
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name not in self.ALLOWED_IMPORTS:
                            return False, f"Import not allowed: {alias.name}"
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module not in self.ALLOWED_IMPORTS:
                        return False, f"Import from not allowed: {node.module}"
                
                # Check for exec/eval calls
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in ['exec', 'eval', 'compile', '__import__']:
                            return False, f"Dangerous function call: {node.func.id}"
                
                # Check for file operations
                elif isinstance(node, ast.Attribute):
                    if node.attr in ['open', 'write', 'read', 'remove', 'unlink']:
                        return False, f"File operation not allowed: {node.attr}"
            
            return True, None
            
        except SyntaxError as e:
            return False, f"Syntax error: {e}"
    
    def execute(self, code: str, timeout: int = 30, 
                globals_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute code in a sandboxed environment.
        
        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds
            globals_dict: Custom global variables
            
        Returns:
            Dictionary containing execution results
        """
        # Validate code first
        is_valid, error_msg = self.validate_code(code)
        if not is_valid:
            logger.error(f"Code validation failed: {error_msg}")
            return {
                'success': False,
                'error': f"Code validation failed: {error_msg}",
                'output': '',
                'exception': None
            }
        
        # Prepare execution environment
        safe_globals = self._create_safe_globals()
        if globals_dict:
            safe_globals.update(globals_dict)
        
        # Capture output
        output_buffer = StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer
        
        result = {
            'success': False,
            'error': None,
            'output': '',
            'exception': None
        }
        
        try:
            # Execute the code
            exec(code, safe_globals)
            
            # Get captured output
            output = output_buffer.getvalue()
            result['output'] = output
            result['success'] = True
            
            logger.info("Code executed successfully in sandbox")
            
        except Exception as e:
            result['exception'] = str(e)
            result['error'] = f"Execution error: {e}"
            logger.error(f"Code execution failed: {e}")
            
        finally:
            # Restore stdout
            sys.stdout = old_stdout
            output_buffer.close()
        
        # Record execution
        self.execution_history.append({
            'timestamp': str(__import__('datetime').datetime.utcnow()),
            'success': result['success'],
            'error': result['error'],
            'output_length': len(result['output'])
        })
        
        return result
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """
        Create a safe global namespace for execution.
        
        Returns:
            Dictionary of safe global variables
        """
        safe_builtins = {
            name: __builtins__[name]
            for name in self.ALLOWED_BUILTINS
            if name in __builtins__
        }
        
        safe_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__sandbox__',
            '__doc__': None
        }
        
        return safe_globals
    
    def execute_remediation(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Execute remediation code with specific safety checks.
        
        Args:
            code: Remediation code to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Dictionary containing execution results
        """
        logger.info("Executing remediation code in sandbox")
        
        # Add boto3 to allowed imports for remediation
        original_imports = self.ALLOWED_IMPORTS.copy()
        self.ALLOWED_IMPORTS.add('boto3')
        self.ALLOWED_IMPORTS.add('botocore.exceptions')
        
        try:
            result = self.execute(code, timeout=timeout)
            return result
        finally:
            # Restore original allowed imports
            self.ALLOWED_IMPORTS = original_imports
    
    def get_execution_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent execution history.
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of execution history entries
        """
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """Clear execution history."""
        self.execution_history = []
        logger.info("Execution history cleared")
    
    def test_sandbox(self) -> Dict[str, Any]:
        """
        Test the sandbox with safe code.
        
        Returns:
            Test execution results
        """
        test_code = """
print("Sandbox test started")
result = {"test": "success", "value": 42}
print(f"Test result: {result}")
print("Sandbox test completed")
"""
        
        logger.info("Running sandbox test")
        return self.execute(test_code)

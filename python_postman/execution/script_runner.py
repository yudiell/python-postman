"""
Script execution for pre-request and test scripts.

This module contains the ScriptRunner class, which executes JavaScript-like
scripts from Postman collections, providing a sandboxed environment for
script execution with access to request/response data and variables.
"""

import ast
import re
import json
import time
from typing import Optional, Dict, Any, List
from .context import ExecutionContext
from .response import ExecutionResponse
from .results import ScriptResults, ScriptAssertion
from .exceptions import ScriptExecutionError
from ..models.request import Request
from ..models.collection import Collection
from ..models.event import EventType


class PostmanAPI:
    """
    Simulates the Postman API (pm object) for script execution.

    Provides access to variables, request/response data, and test functions
    in a way that mimics the Postman scripting environment.
    """

    def __init__(
        self, context: ExecutionContext, response: Optional[ExecutionResponse] = None
    ):
        """
        Initialize Postman API object.

        Args:
            context: Execution context for variable access
            response: Optional response object for test scripts
        """
        self.context = context
        self._response_obj = response
        self.test_results = ScriptResults()
        self._variables = PostmanVariables(context)
        self._response = PostmanResponse(response) if response else None
        self._request = PostmanRequest()

    @property
    def variables(self) -> "PostmanVariables":
        """Access to Postman variables."""
        return self._variables

    @property
    def response(self) -> Optional["PostmanResponse"]:
        """Access to response data (only available in test scripts)."""
        return self._response

    @property
    def request(self) -> "PostmanRequest":
        """Access to request data."""
        return self._request

    def test(self, name: str, test_function: callable) -> None:
        """
        Execute a test assertion.

        Args:
            name: Name of the test
            test_function: Function that performs the test
        """
        try:
            test_function()
            assertion = ScriptAssertion(name=name, passed=True)
            self.test_results.add_assertion(assertion)
        except Exception as e:
            assertion = ScriptAssertion(name=name, passed=False, error=str(e))
            self.test_results.add_assertion(assertion)

    def expect(self, actual: Any) -> "PostmanExpect":
        """
        Create an expectation for testing.

        Args:
            actual: The actual value to test

        Returns:
            PostmanExpect object for chaining assertions
        """
        return PostmanExpect(actual)


class PostmanVariables:
    """Handles variable access and manipulation in scripts."""

    def __init__(self, context: ExecutionContext):
        """
        Initialize variables handler.

        Args:
            context: Execution context for variable access
        """
        self.context = context

    def get(self, key: str) -> Any:
        """Get a variable value."""
        return self.context.get_variable(key)

    def set(self, key: str, value: Any) -> None:
        """Set a variable value."""
        self.context.set_variable(key, value, scope="collection")

    def has(self, key: str) -> bool:
        """Check if a variable exists."""
        return self.context.has_variable(key)


class PostmanResponse:
    """Provides access to response data in test scripts."""

    def __init__(self, response: Optional[ExecutionResponse]):
        """
        Initialize response handler.

        Args:
            response: The execution response object
        """
        self.response = response

    def json(self) -> Any:
        """Get response body as JSON."""
        if not self.response:
            raise ScriptExecutionError("No response available")
        return self.response.json

    def text(self) -> str:
        """Get response body as text."""
        if not self.response:
            raise ScriptExecutionError("No response available")
        return self.response.text

    @property
    def status(self) -> int:
        """Get response status code."""
        if not self.response:
            raise ScriptExecutionError("No response available")
        return self.response.status_code

    @property
    def headers(self) -> Dict[str, str]:
        """Get response headers."""
        if not self.response:
            raise ScriptExecutionError("No response available")
        return dict(self.response.headers)

    @property
    def responseTime(self) -> float:
        """Get response time in milliseconds."""
        if not self.response:
            raise ScriptExecutionError("No response available")
        return self.response.elapsed_ms


class PostmanRequest:
    """Provides access to request data in scripts."""

    def __init__(self):
        """Initialize request handler."""
        pass


class PostmanExpect:
    """Provides assertion methods for testing."""

    def __init__(self, actual: Any):
        """
        Initialize expectation.

        Args:
            actual: The actual value to test
        """
        self.actual = actual

    def to_equal(self, expected: Any) -> None:
        """Assert that actual equals expected."""
        if self.actual != expected:
            raise AssertionError(f"Expected {expected}, but got {self.actual}")

    def to_be_truthy(self) -> None:
        """Assert that actual is truthy."""
        if not self.actual:
            raise AssertionError(f"Expected truthy value, but got {self.actual}")

    def to_be_falsy(self) -> None:
        """Assert that actual is falsy."""
        if self.actual:
            raise AssertionError(f"Expected falsy value, but got {self.actual}")

    def to_have_status(self, status_code: int) -> None:
        """Assert that response has specific status code."""
        if hasattr(self.actual, "status") and self.actual.status != status_code:
            raise AssertionError(
                f"Expected status {status_code}, but got {self.actual.status}"
            )
        elif not hasattr(self.actual, "status"):
            raise AssertionError("Expected object with status property")


class _ScriptASTValidator(ast.NodeVisitor):
    """
    AST validator that rejects dangerous patterns before exec().

    Blocks sandbox escape vectors such as:
    - Dunder attribute access (e.g., __class__, __bases__, __subclasses__)
    - Direct dunder name usage in code
    """

    # Dunder attributes that enable sandbox escapes
    _BLOCKED_ATTRS = frozenset({
        "__class__", "__bases__", "__subclasses__", "__mro__",
        "__globals__", "__builtins__", "__import__", "__loader__",
        "__spec__", "__code__", "__func__", "__self__",
        "__dict__", "__init_subclass__", "__set_name__",
        "__reduce__", "__reduce_ex__", "__getattr__",
        "__setattr__", "__delattr__", "__getattribute__",
    })

    def __init__(self) -> None:
        self.errors: List[str] = []

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if node.attr in self._BLOCKED_ATTRS:
            self.errors.append(
                f"Access to '{node.attr}' is not allowed in Postman scripts"
            )
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if node.id in self._BLOCKED_ATTRS:
            self.errors.append(
                f"Use of '{node.id}' is not allowed in Postman scripts"
            )
        self.generic_visit(node)

    @classmethod
    def validate(cls, code: str) -> None:
        """
        Parse and validate Python code for disallowed patterns.

        Args:
            code: Python source code to validate

        Raises:
            ScriptExecutionError: If the code contains disallowed patterns
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise ScriptExecutionError(f"Script syntax error: {e}") from None
        validator = cls()
        validator.visit(tree)
        if validator.errors:
            raise ScriptExecutionError(
                f"Script blocked by security policy: {'; '.join(validator.errors)}"
            )


class ScriptRunner:
    """
    Executes JavaScript-like scripts from Postman collections.

    The ScriptRunner provides a sandboxed environment for executing
    pre-request and test scripts, with access to variables, request
    data, and response data.

    Security boundaries:
        Scripts are executed via exec() with the following mitigations:
        - **Restricted builtins**: Only a safe subset of Python builtins is available.
        - **Import blocklist**: Dangerous modules (os, subprocess, sys, etc.) are blocked.
        - **AST validation**: Before execution, scripts are parsed and inspected to reject
          dunder attribute access (e.g., ``__class__``, ``__bases__``, ``__subclasses__``),
          which prevents object-introspection-based sandbox escapes.
        - **Thread-based timeout**: Scripts that exceed the timeout are interrupted (though
          Python cannot forcibly kill threads, so CPU-bound infinite loops may linger as
          daemon threads until process exit).

        These mitigations significantly raise the bar for exploitation but do not provide
        the same guarantees as a process-level sandbox. Scripts from untrusted sources
        should be reviewed before execution.
    """

    def __init__(self, timeout: float = 30.0):
        """
        Initialize script runner with timeout.

        Args:
            timeout: Script execution timeout in seconds
        """
        self.timeout = timeout
        self._console_logs: List[str] = []

    def execute_pre_request_scripts(
        self,
        request: Request,
        collection: Optional[Collection],
        context: ExecutionContext,
    ) -> None:
        """
        Execute pre-request scripts and update context.

        Args:
            request: Request object with potential pre-request scripts
            collection: Collection object with potential collection-level scripts (optional)
            context: Execution context to update with script results
        """
        # Execute collection-level pre-request scripts first
        if collection:
            for event in collection.events:
                if event.is_prerequest() and event.has_script():
                    self._execute_script(event.get_script_content(), context, None)

        # Execute request-level pre-request scripts
        for event in request.events:
            if event.is_prerequest() and event.has_script():
                self._execute_script(event.get_script_content(), context, None)

    def execute_test_scripts(
        self, request: Request, response: ExecutionResponse, context: ExecutionContext
    ) -> ScriptResults:
        """
        Execute test scripts and return results.

        Args:
            request: Request object with potential test scripts
            response: Response object for script access
            context: Execution context for variable access and updates

        Returns:
            ScriptResults: Results of test script execution
        """
        aggregated_results = ScriptResults()

        # Execute request-level test scripts
        for event in request.events:
            if event.is_test() and event.has_script():
                test_results = self._execute_script(
                    event.get_script_content(), context, response
                )
                if test_results:
                    aggregated_results.passed += test_results.passed
                    aggregated_results.failed += test_results.failed
                    aggregated_results.assertions.extend(test_results.assertions)

        return aggregated_results

    def create_script_environment(
        self, context: ExecutionContext, response: Optional[ExecutionResponse] = None
    ) -> Dict[str, Any]:
        """
        Create JavaScript execution environment.

        Args:
            context: Execution context for variable access
            response: Optional response object for test scripts

        Returns:
            Dictionary representing the script execution environment
        """
        pm = PostmanAPI(context, response)

        # Create console object for logging
        console = {
            "log": self._console_log,
            "info": self._console_log,
            "warn": self._console_log,
            "error": self._console_log,
        }

        # Basic JavaScript-like globals
        environment = {
            "pm": pm,
            "console": console,
            "JSON": json,
            "setTimeout": self._set_timeout,
            "clearTimeout": self._clear_timeout,
            # Common assertion functions
            "expect": pm.expect,
            # Utility functions
            "parseInt": int,
            "parseFloat": float,
            "String": str,
            "Number": float,
            "Boolean": bool,
            "Array": list,
            "Object": dict,
        }

        return environment

    def _execute_script(
        self,
        script_content: str,
        context: ExecutionContext,
        response: Optional[ExecutionResponse],
    ) -> Optional[ScriptResults]:
        """
        Execute a single script in a sandboxed environment.

        Args:
            script_content: The script code to execute
            context: Execution context
            response: Optional response object for test scripts

        Returns:
            ScriptResults if this was a test script, None for pre-request scripts
        """
        if not script_content or not script_content.strip():
            return None

        try:
            # Create execution environment
            env = self.create_script_environment(context, response)

            # Convert JavaScript-like syntax to Python
            python_code = self._convert_js_to_python(script_content)

            # AST validation — reject dangerous patterns before execution
            _ScriptASTValidator.validate(python_code)

            # Restrict builtins for security — only allow safe operations
            _BLOCKED_MODULES = frozenset({
                "os", "subprocess", "sys", "shutil", "signal",
                "ctypes", "socket", "http", "ftplib", "smtplib",
                "webbrowser", "code", "codeop", "compile",
                "importlib", "runpy", "pickletools", "shelve",
            })

            def _safe_import(name, *args, **kwargs):
                if name.split(".")[0] in _BLOCKED_MODULES:
                    raise ImportError(
                        f"Import of '{name}' is not allowed in Postman scripts"
                    )
                return __builtins__["__import__"](name, *args, **kwargs) if isinstance(__builtins__, dict) else __import__(name, *args, **kwargs)

            safe_builtins = {
                "__import__": _safe_import,
                "abs": abs,
                "all": all,
                "any": any,
                "bool": bool,
                "dict": dict,
                "enumerate": enumerate,
                "float": float,
                "int": int,
                "isinstance": isinstance,
                "len": len,
                "list": list,
                "max": max,
                "min": min,
                "print": print,
                "range": range,
                "round": round,
                "set": set,
                "sorted": sorted,
                "str": str,
                "sum": sum,
                "tuple": tuple,
                "zip": zip,
                "True": True,
                "False": False,
                "None": None,
                "Exception": Exception,
                "AssertionError": AssertionError,
                "ValueError": ValueError,
                "TypeError": TypeError,
                "KeyError": KeyError,
                "IndexError": IndexError,
            }
            env["__builtins__"] = safe_builtins

            # Execute the converted code with a thread-based timeout
            import threading

            exec_exception = [None]

            def _run_script():
                try:
                    exec(python_code, env)
                except Exception as e:
                    exec_exception[0] = e

            thread = threading.Thread(target=_run_script, daemon=True)
            start_time = time.time()
            thread.start()
            thread.join(timeout=self.timeout)

            if thread.is_alive():
                raise ScriptExecutionError(
                    f"Script execution timed out after {self.timeout}s"
                )

            if exec_exception[0] is not None:
                raise exec_exception[0]

            execution_time = time.time() - start_time

            # Return test results if this was a test script
            if response and "pm" in env:
                return env["pm"].test_results

        except Exception as e:
            raise ScriptExecutionError(f"Script execution failed: {str(e)}")

        return None

    def _convert_js_to_python(self, js_code: str) -> str:
        """
        Convert basic JavaScript syntax to Python.

        This is a simplified converter that handles common Postman script patterns.

        Args:
            js_code: JavaScript code to convert

        Returns:
            Python code string
        """
        # Start with the original code
        python_code = js_code

        # Convert variable declarations
        python_code = re.sub(r"\bvar\s+(\w+)", r"\1", python_code)
        python_code = re.sub(r"\blet\s+(\w+)", r"\1", python_code)
        python_code = re.sub(r"\bconst\s+(\w+)", r"\1", python_code)

        # Convert function declarations
        python_code = re.sub(
            r"function\s+(\w+)\s*\((.*?)\)\s*{", r"def \1(\2):", python_code
        )

        # Convert arrow functions (basic cases)
        python_code = re.sub(r"\(\s*\)\s*=>\s*{", r"lambda: (", python_code)
        python_code = re.sub(r"(\w+)\s*=>\s*{", r"lambda \1: (", python_code)

        # Convert common JavaScript methods to Python equivalents
        python_code = re.sub(r"\.length\b", r".__len__()", python_code)
        python_code = re.sub(r"\.push\(", r".append(", python_code)

        # Convert boolean literals
        python_code = re.sub(r"\btrue\b", "True", python_code)
        python_code = re.sub(r"\bfalse\b", "False", python_code)
        python_code = re.sub(r"\bnull\b", "None", python_code)
        python_code = re.sub(r"\bundefined\b", "None", python_code)

        # Convert equality operators
        python_code = re.sub(r"===", "==", python_code)
        python_code = re.sub(r"!==", "!=", python_code)

        # Convert Postman expect chains to method calls
        python_code = re.sub(r"\.to\.equal\(", r".to_equal(", python_code)
        python_code = re.sub(r"\.to\.be\.truthy\(\)", r".to_be_truthy()", python_code)
        python_code = re.sub(r"\.to\.be\.falsy\(\)", r".to_be_falsy()", python_code)
        python_code = re.sub(r"\.to\.have\.status\(", r".to_have_status(", python_code)

        # Convert pm.test calls to proper Python syntax
        python_code = re.sub(
            r'pm\.test\s*\(\s*["\']([^"\']+)["\']\s*,\s*function\s*\(\s*\)\s*{([^}]+)}\s*\)',
            r'pm.test("\1", lambda: (\2))',
            python_code,
            flags=re.DOTALL,
        )

        # Handle basic if statements and blocks
        python_code = re.sub(r"if\s*\(([^)]+)\)\s*{", r"if \1:", python_code)
        python_code = re.sub(r"}\s*else\s*{", r"else:", python_code)
        python_code = re.sub(
            r"}\s*else\s+if\s*\(([^)]+)\)\s*{", r"elif \1:", python_code
        )

        # Remove standalone braces and semicolons
        python_code = re.sub(r"^\s*{\s*$", "", python_code, flags=re.MULTILINE)
        python_code = re.sub(r"^\s*}\s*$", "", python_code, flags=re.MULTILINE)
        python_code = re.sub(r";$", "", python_code, flags=re.MULTILINE)

        # Clean up extra whitespace
        python_code = re.sub(r"\n\s*\n", "\n", python_code)
        python_code = python_code.strip()

        return python_code

    def _console_log(self, *args) -> None:
        """Handle console.log calls from scripts."""
        message = " ".join(str(arg) for arg in args)
        self._console_logs.append(message)

    def _set_timeout(self, callback: callable, delay: int) -> int:
        """Basic setTimeout implementation (returns dummy timer ID)."""
        # In a real implementation, this would schedule the callback
        # For now, just return a dummy timer ID
        return 1

    def _clear_timeout(self, timer_id: int) -> None:
        """Basic clearTimeout implementation."""
        # In a real implementation, this would cancel the timer
        pass

    def get_console_logs(self) -> List[str]:
        """Get all console log messages from script execution."""
        return self._console_logs.copy()

    def clear_console_logs(self) -> None:
        """Clear all console log messages."""
        self._console_logs.clear()

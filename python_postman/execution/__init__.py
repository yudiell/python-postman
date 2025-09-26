"""
Execution module for HTTP request execution using httpx.

This module provides functionality to execute HTTP requests from parsed Postman collections,
including variable substitution, authentication handling, pre-request and test script execution.

The execution module is designed to be optional - the core parsing functionality remains
available without httpx dependencies.
"""

# Core execution classes
from .executor import RequestExecutor
from .context import ExecutionContext
from .response import ExecutionResponse
from .extensions import RequestExtensions

# Result classes
from .results import (
    ExecutionResult,
    TestResults,
    TestAssertion,
    CollectionExecutionResult,
    FolderExecutionResult,
)

# Utility classes
from .variable_resolver import VariableResolver
from .auth_handler import AuthHandler
from .script_runner import ScriptRunner

# Exception classes
from .exceptions import (
    ExecutionError,
    RequestExecutionError,
    VariableResolutionError,
    ScriptExecutionError,
    AuthenticationError,
    TimeoutError,
)

__all__ = [
    # Core execution classes
    "RequestExecutor",
    "ExecutionContext",
    "ExecutionResponse",
    "RequestExtensions",
    # Result classes
    "ExecutionResult",
    "TestResults",
    "TestAssertion",
    "CollectionExecutionResult",
    "FolderExecutionResult",
    # Utility classes
    "VariableResolver",
    "AuthHandler",
    "ScriptRunner",
    # Exception classes
    "ExecutionError",
    "RequestExecutionError",
    "VariableResolutionError",
    "ScriptExecutionError",
    "AuthenticationError",
    "TimeoutError",
]

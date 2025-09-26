"""
Exception classes for HTTP request execution errors.

This module defines the exception hierarchy for errors that can occur during
request execution, including HTTP errors, variable resolution errors, script
execution errors, and authentication errors.
"""

from typing import Optional, Dict, Any
from ..exceptions.base import PostmanCollectionError


class ExecutionError(PostmanCollectionError):
    """
    Base exception for all execution-related errors.

    This serves as the parent class for all specific execution error types.
    """

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """
        Initialize the execution error.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message, details)


class RequestExecutionError(ExecutionError):
    """
    Error during HTTP request execution.

    This exception is raised when an HTTP request fails due to network issues,
    server errors, or other HTTP-related problems.
    """

    def __init__(
        self,
        message: str,
        request_name: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the request execution error.

        Args:
            message: Human-readable error message
            request_name: Name of the request that failed
            status_code: HTTP status code if available
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if request_name:
            error_details["request_name"] = request_name
        if status_code:
            error_details["status_code"] = status_code

        super().__init__(message, error_details)
        self.request_name = request_name
        self.status_code = status_code


class VariableResolutionError(ExecutionError):
    """
    Error resolving variables during request preparation.

    This exception is raised when variable substitution fails due to missing
    variables, circular references, or invalid variable syntax.
    """

    def __init__(
        self,
        message: str,
        variable_name: Optional[str] = None,
        variable_path: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the variable resolution error.

        Args:
            message: Human-readable error message
            variable_name: Name of the variable that failed to resolve
            variable_path: Path or context where the variable was referenced
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if variable_name:
            error_details["variable_name"] = variable_name
        if variable_path:
            error_details["variable_path"] = variable_path

        super().__init__(message, error_details)
        self.variable_name = variable_name
        self.variable_path = variable_path


class ScriptExecutionError(ExecutionError):
    """
    Error executing pre-request or test scripts.

    This exception is raised when script execution fails due to syntax errors,
    runtime errors, or timeouts during script execution.
    """

    def __init__(
        self,
        message: str,
        script_type: Optional[str] = None,
        script_name: Optional[str] = None,
        line_number: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the script execution error.

        Args:
            message: Human-readable error message
            script_type: Type of script ('prerequest' or 'test')
            script_name: Name or identifier of the script
            line_number: Line number where the error occurred
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if script_type:
            error_details["script_type"] = script_type
        if script_name:
            error_details["script_name"] = script_name
        if line_number:
            error_details["line_number"] = line_number

        super().__init__(message, error_details)
        self.script_type = script_type
        self.script_name = script_name
        self.line_number = line_number


class AuthenticationError(ExecutionError):
    """
    Error processing authentication for requests.

    This exception is raised when authentication configuration is invalid,
    credentials are missing, or authentication processing fails.
    """

    def __init__(
        self,
        message: str,
        auth_type: Optional[str] = None,
        auth_parameter: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the authentication error.

        Args:
            message: Human-readable error message
            auth_type: Type of authentication that failed
            auth_parameter: Specific auth parameter that caused the error
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if auth_type:
            error_details["auth_type"] = auth_type
        if auth_parameter:
            error_details["auth_parameter"] = auth_parameter

        super().__init__(message, error_details)
        self.auth_type = auth_type
        self.auth_parameter = auth_parameter


class TimeoutError(ExecutionError):
    """
    Error due to request or script execution timeout.

    This exception is raised when HTTP requests or script execution
    exceeds the configured timeout limits.
    """

    def __init__(
        self,
        message: str,
        timeout_type: Optional[str] = None,
        timeout_duration: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the timeout error.

        Args:
            message: Human-readable error message
            timeout_type: Type of timeout ('request' or 'script')
            timeout_duration: Timeout duration in seconds
            details: Optional dictionary with additional error context
        """
        error_details = details or {}
        if timeout_type:
            error_details["timeout_type"] = timeout_type
        if timeout_duration:
            error_details["timeout_duration"] = timeout_duration

        super().__init__(message, error_details)
        self.timeout_type = timeout_type
        self.timeout_duration = timeout_duration

"""
Unit tests for execution exception classes.
"""

import pytest
from python_postman.execution.exceptions import (
    ExecutionError,
    RequestExecutionError,
    VariableResolutionError,
    ScriptExecutionError,
    AuthenticationError,
    TimeoutError,
)
from python_postman.exceptions.base import PostmanCollectionError


class TestExecutionError:
    """Test cases for the base ExecutionError class."""

    def test_basic_initialization(self):
        """Test basic exception initialization with message only."""
        message = "Test execution error"
        error = ExecutionError(message)

        assert str(error) == message
        assert error.message == message
        assert error.details == {}

    def test_initialization_with_details(self):
        """Test exception initialization with message and details."""
        message = "Test execution error with details"
        details = {"context": "test_context", "operation": "test_operation"}
        error = ExecutionError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == f"{message} (Details: {details})"

    def test_inheritance_from_base(self):
        """Test that ExecutionError inherits from PostmanCollectionError."""
        error = ExecutionError("test")
        assert isinstance(error, PostmanCollectionError)
        assert isinstance(error, Exception)

    def test_can_be_raised_and_caught(self):
        """Test that the exception can be raised and caught properly."""
        with pytest.raises(ExecutionError) as exc_info:
            raise ExecutionError("test execution error")

        assert str(exc_info.value) == "test execution error"

    def test_can_be_caught_as_base_exception(self):
        """Test that ExecutionError can be caught as PostmanCollectionError."""
        with pytest.raises(PostmanCollectionError):
            raise ExecutionError("test error")


class TestRequestExecutionError:
    """Test cases for RequestExecutionError class."""

    def test_basic_initialization(self):
        """Test basic initialization with message only."""
        message = "Request failed"
        error = RequestExecutionError(message)

        assert error.message == message
        assert error.request_name is None
        assert error.status_code is None
        assert error.details == {}

    def test_initialization_with_request_name(self):
        """Test initialization with request name."""
        message = "Request failed"
        request_name = "Get Users"
        error = RequestExecutionError(message, request_name=request_name)

        assert error.message == message
        assert error.request_name == request_name
        assert error.details["request_name"] == request_name

    def test_initialization_with_status_code(self):
        """Test initialization with status code."""
        message = "Request failed"
        status_code = 404
        error = RequestExecutionError(message, status_code=status_code)

        assert error.message == message
        assert error.status_code == status_code
        assert error.details["status_code"] == status_code

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        message = "Request failed"
        request_name = "Get Users"
        status_code = 500
        details = {"url": "https://api.example.com/users"}

        error = RequestExecutionError(
            message, request_name=request_name, status_code=status_code, details=details
        )

        assert error.message == message
        assert error.request_name == request_name
        assert error.status_code == status_code
        assert error.details["request_name"] == request_name
        assert error.details["status_code"] == status_code
        assert error.details["url"] == "https://api.example.com/users"

    def test_inheritance_from_execution_error(self):
        """Test that RequestExecutionError inherits from ExecutionError."""
        error = RequestExecutionError("test")
        assert isinstance(error, ExecutionError)
        assert isinstance(error, PostmanCollectionError)
        assert isinstance(error, Exception)


class TestVariableResolutionError:
    """Test cases for VariableResolutionError class."""

    def test_basic_initialization(self):
        """Test basic initialization with message only."""
        message = "Variable not found"
        error = VariableResolutionError(message)

        assert error.message == message
        assert error.variable_name is None
        assert error.variable_path is None
        assert error.details == {}

    def test_initialization_with_variable_name(self):
        """Test initialization with variable name."""
        message = "Variable not found"
        variable_name = "api_key"
        error = VariableResolutionError(message, variable_name=variable_name)

        assert error.message == message
        assert error.variable_name == variable_name
        assert error.details["variable_name"] == variable_name

    def test_initialization_with_variable_path(self):
        """Test initialization with variable path."""
        message = "Variable not found"
        variable_path = "request.headers.Authorization"
        error = VariableResolutionError(message, variable_path=variable_path)

        assert error.message == message
        assert error.variable_path == variable_path
        assert error.details["variable_path"] == variable_path

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        message = "Variable not found"
        variable_name = "api_key"
        variable_path = "request.headers.Authorization"
        details = {"scope": "collection", "available_vars": ["base_url", "timeout"]}

        error = VariableResolutionError(
            message,
            variable_name=variable_name,
            variable_path=variable_path,
            details=details,
        )

        assert error.message == message
        assert error.variable_name == variable_name
        assert error.variable_path == variable_path
        assert error.details["variable_name"] == variable_name
        assert error.details["variable_path"] == variable_path
        assert error.details["scope"] == "collection"

    def test_inheritance_from_execution_error(self):
        """Test that VariableResolutionError inherits from ExecutionError."""
        error = VariableResolutionError("test")
        assert isinstance(error, ExecutionError)
        assert isinstance(error, PostmanCollectionError)
        assert isinstance(error, Exception)


class TestScriptExecutionError:
    """Test cases for ScriptExecutionError class."""

    def test_basic_initialization(self):
        """Test basic initialization with message only."""
        message = "Script execution failed"
        error = ScriptExecutionError(message)

        assert error.message == message
        assert error.script_type is None
        assert error.script_name is None
        assert error.line_number is None
        assert error.details == {}

    def test_initialization_with_script_type(self):
        """Test initialization with script type."""
        message = "Script execution failed"
        script_type = "prerequest"
        error = ScriptExecutionError(message, script_type=script_type)

        assert error.message == message
        assert error.script_type == script_type
        assert error.details["script_type"] == script_type

    def test_initialization_with_script_name(self):
        """Test initialization with script name."""
        message = "Script execution failed"
        script_name = "setup_auth"
        error = ScriptExecutionError(message, script_name=script_name)

        assert error.message == message
        assert error.script_name == script_name
        assert error.details["script_name"] == script_name

    def test_initialization_with_line_number(self):
        """Test initialization with line number."""
        message = "Script execution failed"
        line_number = 42
        error = ScriptExecutionError(message, line_number=line_number)

        assert error.message == message
        assert error.line_number == line_number
        assert error.details["line_number"] == line_number

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        message = "Script execution failed"
        script_type = "test"
        script_name = "validate_response"
        line_number = 15
        details = {"error_type": "ReferenceError", "stack_trace": "..."}

        error = ScriptExecutionError(
            message,
            script_type=script_type,
            script_name=script_name,
            line_number=line_number,
            details=details,
        )

        assert error.message == message
        assert error.script_type == script_type
        assert error.script_name == script_name
        assert error.line_number == line_number
        assert error.details["script_type"] == script_type
        assert error.details["script_name"] == script_name
        assert error.details["line_number"] == line_number
        assert error.details["error_type"] == "ReferenceError"

    def test_inheritance_from_execution_error(self):
        """Test that ScriptExecutionError inherits from ExecutionError."""
        error = ScriptExecutionError("test")
        assert isinstance(error, ExecutionError)
        assert isinstance(error, PostmanCollectionError)
        assert isinstance(error, Exception)


class TestAuthenticationError:
    """Test cases for AuthenticationError class."""

    def test_basic_initialization(self):
        """Test basic initialization with message only."""
        message = "Authentication failed"
        error = AuthenticationError(message)

        assert error.message == message
        assert error.auth_type is None
        assert error.auth_parameter is None
        assert error.details == {}

    def test_initialization_with_auth_type(self):
        """Test initialization with auth type."""
        message = "Authentication failed"
        auth_type = "bearer"
        error = AuthenticationError(message, auth_type=auth_type)

        assert error.message == message
        assert error.auth_type == auth_type
        assert error.details["auth_type"] == auth_type

    def test_initialization_with_auth_parameter(self):
        """Test initialization with auth parameter."""
        message = "Authentication failed"
        auth_parameter = "token"
        error = AuthenticationError(message, auth_parameter=auth_parameter)

        assert error.message == message
        assert error.auth_parameter == auth_parameter
        assert error.details["auth_parameter"] == auth_parameter

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        message = "Authentication failed"
        auth_type = "basic"
        auth_parameter = "username"
        details = {"required_fields": ["username", "password"], "missing": ["password"]}

        error = AuthenticationError(
            message, auth_type=auth_type, auth_parameter=auth_parameter, details=details
        )

        assert error.message == message
        assert error.auth_type == auth_type
        assert error.auth_parameter == auth_parameter
        assert error.details["auth_type"] == auth_type
        assert error.details["auth_parameter"] == auth_parameter
        assert error.details["required_fields"] == ["username", "password"]

    def test_inheritance_from_execution_error(self):
        """Test that AuthenticationError inherits from ExecutionError."""
        error = AuthenticationError("test")
        assert isinstance(error, ExecutionError)
        assert isinstance(error, PostmanCollectionError)
        assert isinstance(error, Exception)


class TestTimeoutError:
    """Test cases for TimeoutError class."""

    def test_basic_initialization(self):
        """Test basic initialization with message only."""
        message = "Operation timed out"
        error = TimeoutError(message)

        assert error.message == message
        assert error.timeout_type is None
        assert error.timeout_duration is None
        assert error.details == {}

    def test_initialization_with_timeout_type(self):
        """Test initialization with timeout type."""
        message = "Operation timed out"
        timeout_type = "request"
        error = TimeoutError(message, timeout_type=timeout_type)

        assert error.message == message
        assert error.timeout_type == timeout_type
        assert error.details["timeout_type"] == timeout_type

    def test_initialization_with_timeout_duration(self):
        """Test initialization with timeout duration."""
        message = "Operation timed out"
        timeout_duration = 30.0
        error = TimeoutError(message, timeout_duration=timeout_duration)

        assert error.message == message
        assert error.timeout_duration == timeout_duration
        assert error.details["timeout_duration"] == timeout_duration

    def test_initialization_with_all_parameters(self):
        """Test initialization with all parameters."""
        message = "Operation timed out"
        timeout_type = "script"
        timeout_duration = 15.5
        details = {"operation": "pre_request_script", "script_name": "auth_setup"}

        error = TimeoutError(
            message,
            timeout_type=timeout_type,
            timeout_duration=timeout_duration,
            details=details,
        )

        assert error.message == message
        assert error.timeout_type == timeout_type
        assert error.timeout_duration == timeout_duration
        assert error.details["timeout_type"] == timeout_type
        assert error.details["timeout_duration"] == timeout_duration
        assert error.details["operation"] == "pre_request_script"

    def test_inheritance_from_execution_error(self):
        """Test that TimeoutError inherits from ExecutionError."""
        error = TimeoutError("test")
        assert isinstance(error, ExecutionError)
        assert isinstance(error, PostmanCollectionError)
        assert isinstance(error, Exception)


class TestExecutionExceptionHierarchy:
    """Test cases for the overall execution exception hierarchy."""

    def test_all_execution_exceptions_inherit_from_execution_error(self):
        """Test that all specific execution exceptions inherit from ExecutionError."""
        exceptions = [
            RequestExecutionError("test"),
            VariableResolutionError("test"),
            ScriptExecutionError("test"),
            AuthenticationError("test"),
            TimeoutError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, ExecutionError)
            assert isinstance(exc, PostmanCollectionError)
            assert isinstance(exc, Exception)

    def test_execution_exception_hierarchy_catching(self):
        """Test that execution exceptions can be caught at different levels of hierarchy."""
        # Test catching specific exception
        with pytest.raises(RequestExecutionError):
            raise RequestExecutionError("specific error")

        # Test catching at ExecutionError level
        with pytest.raises(ExecutionError):
            raise VariableResolutionError("caught as ExecutionError")

        # Test catching at PostmanCollectionError level
        with pytest.raises(PostmanCollectionError):
            raise ScriptExecutionError("caught as PostmanCollectionError")

        # Test catching at Exception level
        with pytest.raises(Exception):
            raise AuthenticationError("caught as Exception")

    def test_execution_exception_types_are_distinct(self):
        """Test that different execution exception types are distinct."""
        request_error = RequestExecutionError("request")
        variable_error = VariableResolutionError("variable")
        script_error = ScriptExecutionError("script")
        auth_error = AuthenticationError("auth")
        timeout_error = TimeoutError("timeout")

        exceptions = [
            request_error,
            variable_error,
            script_error,
            auth_error,
            timeout_error,
        ]

        # Test that all types are different
        for i, exc1 in enumerate(exceptions):
            for j, exc2 in enumerate(exceptions):
                if i != j:
                    assert type(exc1) != type(exc2)

        # But they all share the same base
        for exc in exceptions:
            assert isinstance(exc, ExecutionError)
            assert isinstance(exc, PostmanCollectionError)

    def test_exception_details_are_preserved(self):
        """Test that exception details are properly preserved and accessible."""
        # Test RequestExecutionError details
        request_error = RequestExecutionError(
            "Request failed",
            request_name="Test Request",
            status_code=404,
            details={"url": "https://example.com"},
        )
        assert request_error.request_name == "Test Request"
        assert request_error.status_code == 404
        assert request_error.details["url"] == "https://example.com"

        # Test VariableResolutionError details
        variable_error = VariableResolutionError(
            "Variable not found",
            variable_name="api_key",
            variable_path="headers.Authorization",
        )
        assert variable_error.variable_name == "api_key"
        assert variable_error.variable_path == "headers.Authorization"

        # Test ScriptExecutionError details
        script_error = ScriptExecutionError(
            "Script failed", script_type="test", script_name="validate", line_number=10
        )
        assert script_error.script_type == "test"
        assert script_error.script_name == "validate"
        assert script_error.line_number == 10

        # Test AuthenticationError details
        auth_error = AuthenticationError(
            "Auth failed", auth_type="bearer", auth_parameter="token"
        )
        assert auth_error.auth_type == "bearer"
        assert auth_error.auth_parameter == "token"

        # Test TimeoutError details
        timeout_error = TimeoutError(
            "Timeout occurred", timeout_type="request", timeout_duration=30.0
        )
        assert timeout_error.timeout_type == "request"
        assert timeout_error.timeout_duration == 30.0

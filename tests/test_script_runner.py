"""Tests for the ScriptRunner class."""

import pytest
from unittest.mock import Mock, MagicMock
from python_postman.execution.script_runner import (
    ScriptRunner,
    PostmanAPI,
    PostmanVariables,
    PostmanResponse,
    PostmanExpect,
)
from python_postman.execution.context import ExecutionContext
from python_postman.execution.response import ExecutionResponse
from python_postman.execution.results import TestResults, TestAssertion
from python_postman.execution.exceptions import ScriptExecutionError
from python_postman.models.request import Request
from python_postman.models.collection import Collection, CollectionInfo
from python_postman.models.event import Event
from python_postman.models.url import Url


class TestPostmanAPI:
    """Test the PostmanAPI class."""

    def test_init(self):
        """Test PostmanAPI initialization."""
        context = ExecutionContext()
        response = Mock(spec=ExecutionResponse)

        pm = PostmanAPI(context, response)

        assert pm.context is context
        assert pm.response is not None
        assert isinstance(pm.test_results, TestResults)
        assert isinstance(pm.variables, PostmanVariables)

    def test_init_without_response(self):
        """Test PostmanAPI initialization without response."""
        context = ExecutionContext()

        pm = PostmanAPI(context)

        assert pm.context is context
        assert pm.response is None

    def test_test_success(self):
        """Test successful test execution."""
        context = ExecutionContext()
        pm = PostmanAPI(context)

        def passing_test():
            assert True

        pm.test("Test passes", passing_test)

        assert pm.test_results.passed == 1
        assert pm.test_results.failed == 0
        assert len(pm.test_results.assertions) == 1
        assert pm.test_results.assertions[0].name == "Test passes"
        assert pm.test_results.assertions[0].passed is True

    def test_test_failure(self):
        """Test failed test execution."""
        context = ExecutionContext()
        pm = PostmanAPI(context)

        def failing_test():
            assert False, "This should fail"

        pm.test("Test fails", failing_test)

        assert pm.test_results.passed == 0
        assert pm.test_results.failed == 1
        assert len(pm.test_results.assertions) == 1
        assert pm.test_results.assertions[0].name == "Test fails"
        assert pm.test_results.assertions[0].passed is False
        assert "This should fail" in pm.test_results.assertions[0].error

    def test_expect(self):
        """Test expect method returns PostmanExpect."""
        context = ExecutionContext()
        pm = PostmanAPI(context)

        expectation = pm.expect(42)

        assert isinstance(expectation, PostmanExpect)
        assert expectation.actual == 42


class TestPostmanVariables:
    """Test the PostmanVariables class."""

    def test_get_variable(self):
        """Test getting a variable."""
        context = ExecutionContext(collection_variables={"test_var": "test_value"})
        variables = PostmanVariables(context)

        result = variables.get("test_var")

        assert result == "test_value"

    def test_set_variable(self):
        """Test setting a variable."""
        context = ExecutionContext()
        variables = PostmanVariables(context)

        variables.set("new_var", "new_value")

        assert context.get_variable("new_var") == "new_value"

    def test_has_variable_exists(self):
        """Test checking if variable exists."""
        context = ExecutionContext(collection_variables={"test_var": "test_value"})
        variables = PostmanVariables(context)

        result = variables.has("test_var")

        assert result is True

    def test_has_variable_not_exists(self):
        """Test checking if variable doesn't exist."""
        context = ExecutionContext()
        variables = PostmanVariables(context)

        result = variables.has("nonexistent")

        assert result is False


class TestPostmanResponse:
    """Test the PostmanResponse class."""

    def test_json(self):
        """Test getting JSON response."""
        mock_response = Mock(spec=ExecutionResponse)
        mock_response.json.return_value = {"key": "value"}

        response = PostmanResponse(mock_response)
        result = response.json()

        assert result == {"key": "value"}
        mock_response.json.assert_called_once()

    def test_text(self):
        """Test getting text response."""
        mock_response = Mock(spec=ExecutionResponse)
        mock_response.text = "response text"

        response = PostmanResponse(mock_response)
        result = response.text()

        assert result == "response text"

    def test_status(self):
        """Test getting status code."""
        mock_response = Mock(spec=ExecutionResponse)
        mock_response.status_code = 200

        response = PostmanResponse(mock_response)
        result = response.status

        assert result == 200

    def test_headers(self):
        """Test getting headers."""
        mock_response = Mock(spec=ExecutionResponse)
        mock_response.headers = {"Content-Type": "application/json"}

        response = PostmanResponse(mock_response)
        result = response.headers

        assert result == {"Content-Type": "application/json"}

    def test_response_time(self):
        """Test getting response time."""
        mock_response = Mock(spec=ExecutionResponse)
        mock_response.elapsed_ms = 123.45

        response = PostmanResponse(mock_response)
        result = response.responseTime

        assert result == 123.45

    def test_no_response_error(self):
        """Test error when no response available."""
        response = PostmanResponse(None)

        with pytest.raises(ScriptExecutionError, match="No response available"):
            response.json()


class TestPostmanExpect:
    """Test the PostmanExpect class."""

    def test_to_equal_success(self):
        """Test successful equality assertion."""
        expect = PostmanExpect(42)

        # Should not raise
        expect.to_equal(42)

    def test_to_equal_failure(self):
        """Test failed equality assertion."""
        expect = PostmanExpect(42)

        with pytest.raises(AssertionError, match="Expected 24, but got 42"):
            expect.to_equal(24)

    def test_to_be_truthy_success(self):
        """Test successful truthy assertion."""
        expect = PostmanExpect(True)

        # Should not raise
        expect.to_be_truthy()

    def test_to_be_truthy_failure(self):
        """Test failed truthy assertion."""
        expect = PostmanExpect(False)

        with pytest.raises(AssertionError, match="Expected truthy value"):
            expect.to_be_truthy()

    def test_to_be_falsy_success(self):
        """Test successful falsy assertion."""
        expect = PostmanExpect(False)

        # Should not raise
        expect.to_be_falsy()

    def test_to_be_falsy_failure(self):
        """Test failed falsy assertion."""
        expect = PostmanExpect(True)

        with pytest.raises(AssertionError, match="Expected falsy value"):
            expect.to_be_falsy()

    def test_to_have_status_success(self):
        """Test successful status assertion."""
        mock_obj = Mock()
        mock_obj.status = 200
        expect = PostmanExpect(mock_obj)

        # Should not raise
        expect.to_have_status(200)

    def test_to_have_status_failure(self):
        """Test failed status assertion."""
        mock_obj = Mock()
        mock_obj.status = 404
        expect = PostmanExpect(mock_obj)

        with pytest.raises(AssertionError, match="Expected status 200, but got 404"):
            expect.to_have_status(200)

    def test_to_have_status_no_status_property(self):
        """Test status assertion on object without status."""
        expect = PostmanExpect("not an object with status")

        with pytest.raises(
            AssertionError, match="Expected object with status property"
        ):
            expect.to_have_status(200)


class TestScriptRunner:
    """Test the ScriptRunner class."""

    def test_init(self):
        """Test ScriptRunner initialization."""
        runner = ScriptRunner(timeout=60.0)

        assert runner.timeout == 60.0
        assert runner._console_logs == []

    def test_init_default_timeout(self):
        """Test ScriptRunner initialization with default timeout."""
        runner = ScriptRunner()

        assert runner.timeout == 30.0

    def test_create_script_environment(self):
        """Test creating script environment."""
        runner = ScriptRunner()
        context = ExecutionContext()
        response = Mock(spec=ExecutionResponse)

        env = runner.create_script_environment(context, response)

        assert "pm" in env
        assert "console" in env
        assert "JSON" in env
        assert "expect" in env
        assert isinstance(env["pm"], PostmanAPI)

    def test_create_script_environment_no_response(self):
        """Test creating script environment without response."""
        runner = ScriptRunner()
        context = ExecutionContext()

        env = runner.create_script_environment(context)

        assert "pm" in env
        assert env["pm"].response is None

    def test_execute_pre_request_scripts_collection_level(self):
        """Test executing collection-level pre-request scripts."""
        runner = ScriptRunner()
        context = ExecutionContext()

        # Create collection with pre-request script
        collection_info = CollectionInfo(name="Test Collection", schema="test")
        collection_event = Event(
            listen="prerequest",
            script="pm.variables.set('test_var', 'collection_value')",
        )
        collection = Collection(info=collection_info, events=[collection_event])

        # Create request
        request = Request(
            name="Test Request", method="GET", url=Url(raw="http://example.com")
        )

        runner.execute_pre_request_scripts(request, collection, context)

        # Variable should be set by the script
        assert context.get_variable("test_var") == "collection_value"

    def test_execute_pre_request_scripts_request_level(self):
        """Test executing request-level pre-request scripts."""
        runner = ScriptRunner()
        context = ExecutionContext()

        # Create collection
        collection_info = CollectionInfo(name="Test Collection", schema="test")
        collection = Collection(info=collection_info)

        # Create request with pre-request script
        request_event = Event(
            listen="prerequest", script="pm.variables.set('test_var', 'request_value')"
        )
        request = Request(
            name="Test Request",
            method="GET",
            url=Url(raw="http://example.com"),
            events=[request_event],
        )

        runner.execute_pre_request_scripts(request, collection, context)

        # Variable should be set by the script
        assert context.get_variable("test_var") == "request_value"

    def test_execute_pre_request_scripts_both_levels(self):
        """Test executing both collection and request level pre-request scripts."""
        runner = ScriptRunner()
        context = ExecutionContext()

        # Create collection with pre-request script
        collection_info = CollectionInfo(name="Test Collection", schema="test")
        collection_event = Event(
            listen="prerequest",
            script="pm.variables.set('collection_var', 'collection_value')",
        )
        collection = Collection(info=collection_info, events=[collection_event])

        # Create request with pre-request script
        request_event = Event(
            listen="prerequest",
            script="pm.variables.set('request_var', 'request_value')",
        )
        request = Request(
            name="Test Request",
            method="GET",
            url=Url(raw="http://example.com"),
            events=[request_event],
        )

        runner.execute_pre_request_scripts(request, collection, context)

        # Both variables should be set
        assert context.get_variable("collection_var") == "collection_value"
        assert context.get_variable("request_var") == "request_value"

    def test_execute_test_scripts(self):
        """Test executing test scripts."""
        runner = ScriptRunner()
        context = ExecutionContext()
        response = Mock(spec=ExecutionResponse)
        response.status_code = 200

        # Create request with test script
        test_script = """
pm.test("Status code is 200", function() {
    pm.expect(pm.response.status).to.equal(200);
});
"""
        test_event = Event(listen="test", script=test_script)
        request = Request(
            name="Test Request",
            method="GET",
            url=Url(raw="http://example.com"),
            events=[test_event],
        )

        results = runner.execute_test_scripts(request, response, context)

        assert isinstance(results, TestResults)
        assert results.passed == 1
        assert results.failed == 0

    def test_execute_test_scripts_failure(self):
        """Test executing test scripts with failures."""
        runner = ScriptRunner()
        context = ExecutionContext()
        response = Mock(spec=ExecutionResponse)
        response.status_code = 404

        # Create request with test script that should fail
        test_script = """
pm.test("Status code is 200", function() {
    pm.expect(pm.response.status).to.equal(200);
});
"""
        test_event = Event(listen="test", script=test_script)
        request = Request(
            name="Test Request",
            method="GET",
            url=Url(raw="http://example.com"),
            events=[test_event],
        )

        results = runner.execute_test_scripts(request, response, context)

        assert isinstance(results, TestResults)
        assert results.passed == 0
        assert results.failed == 1

    def test_convert_js_to_python_basic(self):
        """Test basic JavaScript to Python conversion."""
        runner = ScriptRunner()

        js_code = """
var testVar = true;
let anotherVar = false;
const constVar = null;
"""

        python_code = runner._convert_js_to_python(js_code)

        assert "var " not in python_code
        assert "let " not in python_code
        assert "const " not in python_code
        assert "True" in python_code
        assert "False" in python_code
        assert "None" in python_code

    def test_convert_js_to_python_pm_test(self):
        """Test converting pm.test calls."""
        runner = ScriptRunner()

        js_code = (
            'pm.test("Test name", function() { pm.expect(true).to.be.truthy(); });'
        )

        python_code = runner._convert_js_to_python(js_code)

        assert 'pm.test("Test name", lambda:' in python_code

    def test_console_log(self):
        """Test console logging."""
        runner = ScriptRunner()

        runner._console_log("Hello", "World", 123)

        logs = runner.get_console_logs()
        assert len(logs) == 1
        assert logs[0] == "Hello World 123"

    def test_clear_console_logs(self):
        """Test clearing console logs."""
        runner = ScriptRunner()
        runner._console_log("Test message")

        runner.clear_console_logs()

        logs = runner.get_console_logs()
        assert len(logs) == 0

    def test_script_execution_timeout(self):
        """Test script execution timeout."""
        runner = ScriptRunner(timeout=0.001)  # Very short timeout
        context = ExecutionContext()

        # Script that would take longer than timeout
        script = """
import time
time.sleep(0.1)
"""

        with pytest.raises(ScriptExecutionError, match="Script execution timed out"):
            runner._execute_script(script, context, None)

    def test_script_execution_error(self):
        """Test script execution error handling."""
        runner = ScriptRunner()
        context = ExecutionContext()

        # Script with syntax error
        script = "invalid python syntax !!!"

        with pytest.raises(ScriptExecutionError, match="Script execution failed"):
            runner._execute_script(script, context, None)

    def test_empty_script_handling(self):
        """Test handling of empty scripts."""
        runner = ScriptRunner()
        context = ExecutionContext()

        result = runner._execute_script("", context, None)

        assert result is None

    def test_disabled_event_ignored(self):
        """Test that disabled events are ignored."""
        runner = ScriptRunner()
        context = ExecutionContext()

        # Create collection
        collection_info = CollectionInfo(name="Test Collection", schema="test")
        collection = Collection(info=collection_info)

        # Create request with disabled pre-request script
        disabled_event = Event(
            listen="prerequest",
            script="pm.variables.set('should_not_be_set', 'value')",
            disabled=True,
        )
        request = Request(
            name="Test Request",
            method="GET",
            url=Url(raw="http://example.com"),
            events=[disabled_event],
        )

        runner.execute_pre_request_scripts(request, collection, context)

        # Variable should not be set because event is disabled
        assert context.get_variable("should_not_be_set") is None


if __name__ == "__main__":
    pytest.main([__file__])

"""Tests for execution reporter module."""

import pytest
import json
from pathlib import Path
from python_postman.execution.results import (
    ExecutionResult,
    CollectionExecutionResult,
    ScriptResults,
    ScriptAssertion,
)
from python_postman.models.request import Request
from python_postman.models.url import Url
from python_postman.execution.response import ExecutionResponse
from tests.execution_tests.execution_reporter import ExecutionReporter


class MockHttpxResponse:
    """Mock httpx response for testing."""

    def __init__(self, status_code=200, text='{"test": "data"}', content=None):
        self.status_code = status_code
        self.text = text
        self.content = content or text.encode('utf-8')
        self.url = "https://api.example.com/test"
        self.request = type('obj', (object,), {'method': 'GET'})()

    def json(self):
        return json.loads(self.text)


def test_format_request_summary_success():
    """Test formatting successful request summary."""
    # Create a mock request
    url = Url(raw="https://api.example.com/test")
    request = Request(name="Test Request", method="GET", url=url)

    # Create a mock response
    mock_httpx = MockHttpxResponse()
    response = ExecutionResponse(mock_httpx, 0.0, 0.245)

    # Create execution result
    result = ExecutionResult(
        request=request,
        response=response,
        execution_time_ms=245.32
    )

    # Format summary
    summary = ExecutionReporter.format_request_summary(result)

    # Verify key elements are present
    assert "Test Request" in summary
    assert "SUCCESS" in summary
    assert "200" in summary
    assert "245.32ms" in summary
    assert "GET" in summary


def test_format_request_summary_with_error():
    """Test formatting request summary with error."""
    url = Url(raw="https://api.example.com/fail")
    request = Request(name="Failed Request", method="POST", url=url)

    result = ExecutionResult(
        request=request,
        error=Exception("Connection timeout"),
        execution_time_ms=5000.0
    )

    summary = ExecutionReporter.format_request_summary(result)

    assert "Failed Request" in summary
    assert "FAILED" in summary
    assert "Connection timeout" in summary
    assert "5000.00ms" in summary


def test_format_collection_summary():
    """Test formatting collection summary."""
    # Create collection result
    collection_result = CollectionExecutionResult(
        collection_name="Test Collection"
    )

    # Add successful result
    url1 = Url(raw="https://api.example.com/test1")
    request1 = Request(name="Request 1", method="GET", url=url1)
    mock_httpx1 = MockHttpxResponse(status_code=200)
    response1 = ExecutionResponse(mock_httpx1, 0.0, 0.1)
    result1 = ExecutionResult(request=request1, response=response1, execution_time_ms=100.0)
    collection_result.add_result(result1)

    # Add failed result
    url2 = Url(raw="https://api.example.com/test2")
    request2 = Request(name="Request 2", method="POST", url=url2)
    result2 = ExecutionResult(
        request=request2,
        error=Exception("Network error"),
        execution_time_ms=50.0
    )
    collection_result.add_result(result2)

    # Format summary
    summary = ExecutionReporter.format_collection_summary(collection_result)

    assert "Test Collection" in summary
    assert "Total Requests: 2" in summary
    assert "Successful: 1" in summary
    assert "Failed: 1" in summary
    assert "Success Rate: 50.0%" in summary
    assert "Request 1" in summary
    assert "Request 2" in summary


def test_format_comparison_table():
    """Test formatting comparison table."""
    results = {}

    # Add multiple results
    for i in range(3):
        url = Url(raw=f"https://api.example.com/test{i}")
        request = Request(name=f"Request {i}", method="GET", url=url)
        mock_httpx = MockHttpxResponse(status_code=200)
        response = ExecutionResponse(mock_httpx, 0.0, 0.1 + i * 0.05)
        result = ExecutionResult(
            request=request,
            response=response,
            execution_time_ms=100.0 + i * 50
        )
        results[f"dataset_{i}"] = result

    # Format table
    table = ExecutionReporter.format_comparison_table(results)

    assert "Execution Comparison" in table
    assert "dataset_0" in table
    assert "dataset_1" in table
    assert "dataset_2" in table
    assert "SUCCESS" in table
    assert "Total: 3" in table
    assert "Successful: 3" in table


def test_export_to_json(tmp_path):
    """Test exporting results to JSON."""
    # Create a result
    url = Url(raw="https://api.example.com/test")
    request = Request(name="Test Request", method="GET", url=url)
    mock_httpx = MockHttpxResponse()
    response = ExecutionResponse(mock_httpx, 0.0, 0.245)
    result = ExecutionResult(
        request=request,
        response=response,
        execution_time_ms=245.32
    )

    # Export to JSON
    output_path = tmp_path / "test_output.json"
    ExecutionReporter.export_to_json(result, output_path)

    # Verify file was created
    assert output_path.exists()

    # Verify content
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert "timestamp" in data
    assert "results" in data
    assert data["results"]["request_name"] == "Test Request"
    assert data["results"]["success"] is True
    assert data["results"]["status_code"] == 200


def test_export_collection_to_json(tmp_path):
    """Test exporting collection results to JSON."""
    collection_result = CollectionExecutionResult(
        collection_name="Test Collection"
    )

    url = Url(raw="https://api.example.com/test")
    request = Request(name="Request 1", method="GET", url=url)
    mock_httpx = MockHttpxResponse()
    response = ExecutionResponse(mock_httpx, 0.0, 0.1)
    result = ExecutionResult(request=request, response=response, execution_time_ms=100.0)
    collection_result.add_result(result)

    # Export to JSON
    output_path = tmp_path / "collection_output.json"
    ExecutionReporter.export_to_json(collection_result, output_path)

    # Verify file was created
    assert output_path.exists()

    # Verify content
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert data["results"]["collection_name"] == "Test Collection"
    assert data["results"]["total_requests"] == 1
    assert data["results"]["successful_requests"] == 1


def test_format_bytes():
    """Test byte formatting."""
    assert ExecutionReporter._format_bytes(500) == "500.0 B"
    assert ExecutionReporter._format_bytes(1024) == "1.0 KB"
    assert ExecutionReporter._format_bytes(1536) == "1.5 KB"
    assert ExecutionReporter._format_bytes(1048576) == "1.0 MB"
    assert ExecutionReporter._format_bytes(1073741824) == "1.0 GB"


def test_format_request_with_test_results():
    """Test formatting request with test results."""
    url = Url(raw="https://api.example.com/test")
    request = Request(name="Test Request", method="GET", url=url)
    mock_httpx = MockHttpxResponse()
    response = ExecutionResponse(mock_httpx, 0.0, 0.1)

    # Create test results
    test_results = ScriptResults()
    test_results.add_assertion(ScriptAssertion(name="Status is 200", passed=True))
    test_results.add_assertion(ScriptAssertion(name="Response has data", passed=True))
    test_results.add_assertion(ScriptAssertion(name="Invalid check", passed=False, error="Expected true"))

    result = ExecutionResult(
        request=request,
        response=response,
        test_results=test_results,
        execution_time_ms=100.0
    )

    summary = ExecutionReporter.format_request_summary(result)

    assert "Test Results:" in summary
    assert "Status is 200" in summary
    assert "Response has data" in summary
    assert "Invalid check" in summary
    assert "PASS" in summary
    assert "FAIL" in summary


def test_export_dict_results_to_json(tmp_path):
    """Test exporting dictionary of results to JSON."""
    results = {}

    for i in range(2):
        url = Url(raw=f"https://api.example.com/test{i}")
        request = Request(name=f"Request {i}", method="GET", url=url)
        mock_httpx = MockHttpxResponse()
        response = ExecutionResponse(mock_httpx, 0.0, 0.1)
        result = ExecutionResult(request=request, response=response, execution_time_ms=100.0)
        results[f"dataset_{i}"] = result

    # Export to JSON
    output_path = tmp_path / "dict_output.json"
    ExecutionReporter.export_to_json(results, output_path)

    # Verify file was created
    assert output_path.exists()

    # Verify content
    with open(output_path, 'r') as f:
        data = json.load(f)

    assert "dataset_0" in data["results"]
    assert "dataset_1" in data["results"]

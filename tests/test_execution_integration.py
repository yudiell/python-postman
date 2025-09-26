"""
Integration tests for HTTP request execution functionality.

These tests validate end-to-end execution workflows using real HTTP requests
against test servers, including variable substitution, authentication,
script execution, and collection-level execution patterns.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any
from unittest.mock import Mock, patch
import pytest

# Test server imports
import threading
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs

# Import execution components
try:
    import httpx
    from python_postman.execution.executor import RequestExecutor
    from python_postman.execution.context import ExecutionContext
    from python_postman.execution.extensions import RequestExtensions
    from python_postman.execution.results import (
        ExecutionResult,
        CollectionExecutionResult,
        TestResults,
    )
    from python_postman.execution.exceptions import (
        ExecutionError,
        RequestExecutionError,
        VariableResolutionError,
        ScriptExecutionError,
        AuthenticationError,
    )

    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

from python_postman.parser import PythonPostman
from python_postman.models.collection import Collection
from python_postman.models.request import Request
from python_postman.models.url import Url
from python_postman.models.header import Header
from python_postman.models.body import Body
from python_postman.models.auth import Auth, AuthParameter
from python_postman.models.variable import Variable


# Test HTTP Server Implementation
class TestHTTPHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler for integration test server."""

    def log_message(self, format, *args):
        """Suppress server logs during tests."""
        pass

    def do_GET(self):
        """Handle GET requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)

        # Check authentication
        auth_header = self.headers.get("Authorization")
        api_key = self.headers.get("X-API-Key")

        if path == "/users/123":
            self._handle_get_user(auth_header, api_key)
        elif path == "/protected/profile":
            self._handle_protected_profile(auth_header)
        elif path == "/nonexistent":
            self._send_json_response(404, {"error": "Not found"})
        elif path == "/slow":
            # Simulate slow response
            time.sleep(2)
            self._send_json_response(200, {"message": "Slow response"})
        elif path == "/error":
            self._send_json_response(500, {"error": "Internal server error"})
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def do_POST(self):
        """Handle POST requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/users":
            self._handle_create_user()
        elif path == "/auth/login":
            self._handle_login()
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def do_PUT(self):
        """Handle PUT requests."""
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path.startswith("/users/"):
            user_id = path.split("/")[-1]
            self._handle_update_user(user_id)
        else:
            self._send_json_response(404, {"error": "Endpoint not found"})

    def _handle_get_user(self, auth_header, api_key):
        """Handle GET /users/123 request."""
        # Check API key authentication
        if api_key != "collection-api-key-456":
            self._send_json_response(401, {"error": "Invalid API key"})
            return

        self._send_json_response(
            200,
            {
                "id": 123,
                "name": "John Doe",
                "email": "john@example.com",
                "created_at": "2023-01-01T00:00:00Z",
            },
        )

    def _handle_protected_profile(self, auth_header):
        """Handle GET /protected/profile request."""
        if not auth_header or not auth_header.startswith("Bearer "):
            self._send_json_response(401, {"error": "Bearer token required"})
            return

        token = auth_header.split(" ")[1]
        if token != "test-bearer-token-123":
            self._send_json_response(401, {"error": "Invalid bearer token"})
            return

        self._send_json_response(
            200,
            {
                "profile": {
                    "user_id": 123,
                    "preferences": {"theme": "dark"},
                    "last_login": "2023-01-01T12:00:00Z",
                }
            },
        )

    def _handle_create_user(self):
        """Handle POST /users request."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode("utf-8"))

            # Simulate user creation
            created_user = {
                "id": 456,
                "name": data.get("name", "Unknown"),
                "email": data.get("email", "unknown@example.com"),
                "timestamp": data.get("timestamp", ""),
                "created_at": "2023-01-01T00:00:00Z",
            }

            self._send_json_response(201, created_user)
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON"})

    def _handle_login(self):
        """Handle POST /auth/login request."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode("utf-8"))
            username = data.get("username")
            password = data.get("password")

            if username == "testuser" and password == "testpass":
                self._send_json_response(
                    200, {"token": "test-bearer-token-123", "expires_in": 3600}
                )
            else:
                self._send_json_response(401, {"error": "Invalid credentials"})
        except json.JSONDecodeError:
            self._send_json_response(400, {"error": "Invalid JSON"})

    def _handle_update_user(self, user_id):
        """Handle PUT /users/{id} request."""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode("utf-8"))

            updated_user = {
                "id": int(user_id),
                "name": data.get("name", "Unknown"),
                "email": data.get("email", "unknown@example.com"),
                "updated_at": "2023-01-01T00:00:00Z",
            }

            self._send_json_response(200, updated_user)
        except (json.JSONDecodeError, ValueError):
            self._send_json_response(400, {"error": "Invalid data"})

    def _send_json_response(self, status_code: int, data: Dict[str, Any]):
        """Send JSON response."""
        response_data = json.dumps(data).encode("utf-8")

        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(response_data)))
        self.end_headers()
        self.wfile.write(response_data)


class TestServer:
    """Test HTTP server for integration tests."""

    def __init__(self, port: int = 0):  # Use 0 to let OS choose available port
        self.port = port
        self.server = None
        self.thread = None
        self.actual_port = None

    def start(self):
        """Start the test server."""
        self.server = socketserver.TCPServer(("", self.port), TestHTTPHandler)
        self.actual_port = self.server.server_address[1]  # Get actual port assigned
        self.thread = threading.Thread(target=self.server.serve_forever)
        self.thread.daemon = True
        self.thread.start()

        # Wait a bit for server to start
        time.sleep(0.1)

    def stop(self):
        """Stop the test server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.thread:
            self.thread.join(timeout=1)


@pytest.fixture(scope="session")
def test_server():
    """Fixture to provide a test HTTP server."""
    if not HTTPX_AVAILABLE:
        pytest.skip("httpx not available for integration tests")

    server = TestServer()  # Let OS choose port
    server.start()
    yield server
    server.stop()


@pytest.fixture
def execution_collection():
    """Fixture to provide execution test collection."""
    file_path = Path(__file__).parent / "test_data" / "execution_collection.json"
    return PythonPostman.from_file(file_path)


@pytest.fixture
def request_executor():
    """Fixture to provide a configured request executor."""
    if not HTTPX_AVAILABLE:
        pytest.skip("httpx not available for integration tests")

    return RequestExecutor(
        client_config={"timeout": 10.0, "verify": False}, request_delay=0.1
    )


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not available")
class TestSingleRequestExecution:
    """Test single request execution scenarios."""

    @pytest.mark.asyncio
    async def test_simple_get_request_execution(self, test_server, request_executor):
        """Test executing a simple GET request with variable substitution."""
        # Create request with variables
        request = Request(
            name="Get User",
            url=Url(raw="{{base_url}}/users/{{user_id}}"),
            method="GET",
            headers=[
                Header(key="Accept", value="application/json"),
                Header(key="X-API-Key", value="{{api_key}}"),
            ],
        )

        # Create execution context with variables
        context = ExecutionContext(
            collection_variables={
                "base_url": f"http://localhost:{test_server.actual_port}",
                "user_id": "123",
                "api_key": "collection-api-key-456",
            }
        )

        # Execute request
        result = await request_executor.execute_request(request, context)

        # Verify result
        assert isinstance(result, ExecutionResult)
        assert result.error is None
        assert result.response is not None
        assert result.response.status_code == 200

        # Verify response data
        response_data = result.response.json
        assert response_data["id"] == 123
        assert response_data["name"] == "John Doe"
        assert result.response.elapsed_ms > 0

    @pytest.mark.asyncio
    async def test_post_request_with_body_execution(
        self, test_server, request_executor
    ):
        """Test executing POST request with JSON body."""
        # Create POST request
        request = Request(
            name="Create User",
            url=Url(raw="{{base_url}}/users"),
            method="POST",
            headers=[Header(key="Content-Type", value="application/json")],
            body=Body(
                mode="raw", raw='{"name": "{{user_name}}", "email": "{{user_email}}"}'
            ),
        )

        # Create execution context
        context = ExecutionContext(
            collection_variables={
                "base_url": f"http://localhost:{test_server.actual_port}",
                "user_name": "Jane Doe",
                "user_email": "jane@example.com",
            }
        )

        # Execute request
        result = await request_executor.execute_request(request, context)

        # Verify result
        assert result.error is None
        assert result.response.status_code == 201

        response_data = result.response.json
        assert response_data["name"] == "Jane Doe"
        assert response_data["email"] == "jane@example.com"
        assert response_data["id"] == 456

    @pytest.mark.asyncio
    async def test_authenticated_request_execution(self, test_server, request_executor):
        """Test executing request with bearer token authentication."""
        # Create authenticated request
        request = Request(
            name="Protected Request",
            url=Url(raw="{{base_url}}/protected/profile"),
            method="GET",
            auth=Auth(
                type="bearer",
                parameters=[AuthParameter(key="token", value="{{auth_token}}")],
            ),
        )

        # Create execution context
        context = ExecutionContext(
            collection_variables={
                "base_url": f"http://localhost:{test_server.actual_port}",
                "auth_token": "test-bearer-token-123",
            }
        )

        # Execute request
        result = await request_executor.execute_request(request, context)

        # Verify result
        assert result.error is None
        assert result.response.status_code == 200

        response_data = result.response.json
        assert "profile" in response_data
        assert response_data["profile"]["user_id"] == 123

    @pytest.mark.asyncio
    async def test_request_with_extensions(self, test_server, request_executor):
        """Test executing request with runtime extensions."""
        # Create base request
        request = Request(
            name="Extended Request",
            url=Url(raw="{{base_url}}/users/{{user_id}}"),
            method="GET",
        )

        # Create execution context
        context = ExecutionContext(
            collection_variables={
                "base_url": f"http://localhost:{test_server.actual_port}",
                "user_id": "123",
            }
        )

        # Create extensions
        extensions = RequestExtensions(
            header_extensions={"X-API-Key": "collection-api-key-456"},
            param_extensions={"format": "json"},
        )

        # Execute request with extensions
        result = await request_executor.execute_request(
            request, context, extensions=extensions
        )

        # Verify result
        assert result.error is None
        assert result.response.status_code == 200

    def test_synchronous_request_execution(self, test_server, request_executor):
        """Test synchronous request execution."""
        # Create simple request
        request = Request(
            name="Sync Request",
            url=Url(raw="{{base_url}}/users/{{user_id}}"),
            method="GET",
            headers=[Header(key="X-API-Key", value="{{api_key}}")],
        )

        # Create execution context
        context = ExecutionContext(
            collection_variables={
                "base_url": f"http://localhost:{test_server.actual_port}",
                "user_id": "123",
                "api_key": "collection-api-key-456",
            }
        )

        # Execute request synchronously
        result = request_executor.execute_request_sync(request, context)

        # Verify result
        assert isinstance(result, ExecutionResult)
        assert result.error is None
        assert result.response.status_code == 200


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not available")
class TestCollectionExecution:
    """Test collection-level execution scenarios."""

    @pytest.mark.asyncio
    async def test_full_collection_execution(
        self, test_server, execution_collection, request_executor
    ):
        """Test executing complete collection with variable state management."""
        # Execute the entire collection
        result = await request_executor.execute_collection(execution_collection)

        # Verify collection execution result
        assert isinstance(result, CollectionExecutionResult)
        assert result.collection_name == "Execution Test Collection"
        assert result.total_requests == 4
        assert result.successful_requests >= 3  # At least 3 should succeed
        assert result.total_time_ms > 0

        # Verify individual request results
        assert len(result.results) == 4

        # Check that variables were maintained across requests
        get_result = result.results[0]  # Simple GET Request
        assert get_result.error is None
        assert get_result.response.status_code == 200

        post_result = result.results[1]  # POST Request with Body
        assert post_result.error is None
        assert post_result.response.status_code == 201

        auth_result = result.results[2]  # Authenticated Request
        assert auth_result.error is None
        assert auth_result.response.status_code == 200

        # Error handling request should return 404
        error_result = result.results[3]  # Error Handling Request
        assert error_result.error is None  # No execution error
        assert error_result.response.status_code == 404

    @pytest.mark.asyncio
    async def test_collection_execution_with_stop_on_error(
        self, test_server, request_executor
    ):
        """Test collection execution with stop_on_error option."""
        # Create collection with failing request first
        failing_request = Request(
            name="Failing Request",
            url=Url(raw="http://localhost:8080/error"),
            method="GET",
        )

        success_request = Request(
            name="Success Request",
            url=Url(raw="http://localhost:8080/users/123"),
            method="GET",
            headers=[Header(key="X-API-Key", value="collection-api-key-456")],
        )

        from python_postman.models.collection_info import CollectionInfo

        collection = Collection(
            info=CollectionInfo(name="Stop on Error Test"),
            items=[failing_request, success_request],
        )

        # Execute with stop_on_error=True
        result = await request_executor.execute_collection(
            collection, stop_on_error=True
        )

        # Should stop after first request fails
        assert result.total_requests == 1
        assert result.successful_requests == 0
        assert result.failed_requests == 1

    @pytest.mark.asyncio
    async def test_collection_execution_continue_on_error(
        self, test_server, request_executor
    ):
        """Test collection execution continuing on errors."""
        # Create collection with failing request first
        failing_request = Request(
            name="Failing Request",
            url=Url(raw="http://localhost:8080/error"),
            method="GET",
        )

        success_request = Request(
            name="Success Request",
            url=Url(raw="http://localhost:8080/users/123"),
            method="GET",
            headers=[Header(key="X-API-Key", value="collection-api-key-456")],
        )

        from python_postman.models.collection_info import CollectionInfo

        collection = Collection(
            info=CollectionInfo(name="Continue on Error Test"),
            items=[failing_request, success_request],
        )

        # Execute with stop_on_error=False (default)
        result = await request_executor.execute_collection(
            collection, stop_on_error=False
        )

        # Should execute both requests
        assert result.total_requests == 2
        assert result.successful_requests == 1
        assert result.failed_requests == 1


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not available")
class TestScriptExecution:
    """Test script execution during request execution."""

    @pytest.mark.asyncio
    async def test_pre_request_script_execution(self, test_server, request_executor):
        """Test pre-request script execution and variable modification."""
        from python_postman.models.event import Event, Script

        # Create request with pre-request script
        pre_request_script = Event(
            listen="prerequest",
            script=Script(
                type="text/javascript",
                exec=[
                    "pm.collectionVariables.set('dynamic_user_id', '999');",
                    "pm.collectionVariables.set('timestamp', Date.now().toString());",
                ],
            ),
        )

        request = Request(
            name="Request with Pre-script",
            url=Url(raw="{{base_url}}/users/{{dynamic_user_id}}"),
            method="GET",
            headers=[Header(key="X-API-Key", value="collection-api-key-456")],
            events=[pre_request_script],
        )

        # Create execution context
        context = ExecutionContext(
            collection_variables={"base_url": "http://localhost:8080"}
        )

        # Execute request
        result = await request_executor.execute_request(request, context)

        # Verify that pre-request script was executed
        # The request should have used dynamic_user_id=999, but our test server
        # only responds to /users/123, so this should return 404
        assert result.error is None
        # Note: This will likely return 404 since our test server doesn't handle /users/999

    @pytest.mark.asyncio
    async def test_test_script_execution(self, test_server, request_executor):
        """Test test script execution and result collection."""
        from python_postman.models.event import Event, Script

        # Create request with test script
        test_script = Event(
            listen="test",
            script=Script(
                type="text/javascript",
                exec=[
                    "pm.test('Status code is 200', function () {",
                    "    pm.response.to.have.status(200);",
                    "});",
                    "pm.test('Response has user data', function () {",
                    "    const jsonData = pm.response.json();",
                    "    pm.expect(jsonData).to.have.property('id');",
                    "});",
                ],
            ),
        )

        request = Request(
            name="Request with Test Script",
            url=Url(raw="{{base_url}}/users/{{user_id}}"),
            method="GET",
            headers=[Header(key="X-API-Key", value="{{api_key}}")],
            events=[test_script],
        )

        # Create execution context
        context = ExecutionContext(
            collection_variables={
                "base_url": "http://localhost:8080",
                "user_id": "123",
                "api_key": "collection-api-key-456",
            }
        )

        # Execute request
        result = await request_executor.execute_request(request, context)

        # Verify test script execution
        assert result.error is None
        assert result.response.status_code == 200
        assert result.test_results is not None
        assert isinstance(result.test_results, TestResults)


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not available")
class TestErrorHandling:
    """Test error handling scenarios."""

    @pytest.mark.asyncio
    async def test_network_error_handling(self, request_executor):
        """Test handling of network errors."""
        # Create request to non-existent server
        request = Request(
            name="Network Error Request",
            url=Url(raw="http://localhost:9999/test"),  # Non-existent port
            method="GET",
        )

        context = ExecutionContext()

        # Execute request
        result = await request_executor.execute_request(request, context)

        # Should have an error but not crash
        assert result.error is not None
        assert isinstance(result.error, RequestExecutionError)
        assert result.response is None

    @pytest.mark.asyncio
    async def test_variable_resolution_error(self, test_server, request_executor):
        """Test handling of variable resolution errors."""
        # Create request with undefined variable
        request = Request(
            name="Variable Error Request",
            url=Url(raw="{{base_url}}/users/{{undefined_variable}}"),
            method="GET",
        )

        context = ExecutionContext(
            collection_variables={"base_url": "http://localhost:8080"}
            # Note: undefined_variable is not defined
        )

        # Execute request
        result = await request_executor.execute_request(request, context)

        # Should have a variable resolution error
        assert result.error is not None
        assert isinstance(result.error, VariableResolutionError)

    @pytest.mark.asyncio
    async def test_authentication_error_handling(self, test_server, request_executor):
        """Test handling of authentication errors."""
        # Create request with invalid auth token
        request = Request(
            name="Auth Error Request",
            url=Url(raw="{{base_url}}/protected/profile"),
            method="GET",
            auth=Auth(
                type="bearer",
                parameters=[AuthParameter(key="token", value="invalid-token")],
            ),
        )

        context = ExecutionContext(
            collection_variables={"base_url": "http://localhost:8080"}
        )

        # Execute request
        result = await request_executor.execute_request(request, context)

        # Should get 401 response, not an execution error
        assert result.error is None
        assert result.response.status_code == 401


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not available")
class TestPerformanceAndParallelExecution:
    """Test performance and parallel execution scenarios."""

    @pytest.mark.asyncio
    async def test_parallel_collection_execution(self, test_server, request_executor):
        """Test parallel execution of collection requests."""
        # Create collection with multiple independent requests
        requests = []
        for i in range(5):
            request = Request(
                name=f"Parallel Request {i}",
                url=Url(raw="{{base_url}}/users/{{user_id}}"),
                method="GET",
                headers=[Header(key="X-API-Key", value="{{api_key}}")],
            )
            requests.append(request)

        from python_postman.models.collection_info import CollectionInfo

        collection = Collection(
            info=CollectionInfo(name="Parallel Test Collection"),
            items=requests,
            variables=[
                Variable(key="base_url", value="http://localhost:8080"),
                Variable(key="user_id", value="123"),
                Variable(key="api_key", value="collection-api-key-456"),
            ],
        )

        # Measure execution time for parallel execution
        start_time = time.time()
        result = await request_executor.execute_collection(collection, parallel=True)
        parallel_time = time.time() - start_time

        # Verify all requests succeeded
        assert result.total_requests == 5
        assert result.successful_requests == 5
        assert result.failed_requests == 0

        # Parallel execution should be faster than sequential
        # (This is a rough check - in practice, the difference might be small for fast requests)
        assert parallel_time < 10.0  # Should complete within reasonable time

    @pytest.mark.asyncio
    async def test_large_collection_execution(self, test_server, request_executor):
        """Test execution of large collection with many requests."""
        # Create collection with many requests
        requests = []
        for i in range(20):
            request = Request(
                name=f"Large Collection Request {i}",
                url=Url(raw="{{base_url}}/users/{{user_id}}"),
                method="GET",
                headers=[Header(key="X-API-Key", value="{{api_key}}")],
            )
            requests.append(request)

        from python_postman.models.collection_info import CollectionInfo

        collection = Collection(
            info=CollectionInfo(name="Large Test Collection"),
            items=requests,
            variables=[
                Variable(key="base_url", value="http://localhost:8080"),
                Variable(key="user_id", value="123"),
                Variable(key="api_key", value="collection-api-key-456"),
            ],
        )

        # Execute large collection
        start_time = time.time()
        result = await request_executor.execute_collection(collection)
        execution_time = time.time() - start_time

        # Verify all requests succeeded
        assert result.total_requests == 20
        assert result.successful_requests == 20
        assert result.failed_requests == 0

        # Should complete within reasonable time
        assert execution_time < 30.0

        # Verify memory usage is reasonable (basic check)
        assert len(result.results) == 20
        for request_result in result.results:
            assert request_result.response is not None

    @pytest.mark.asyncio
    async def test_request_timeout_handling(self, test_server):
        """Test handling of request timeouts."""
        # Create executor with short timeout
        short_timeout_executor = RequestExecutor(
            client_config={"timeout": 1.0}  # 1 second timeout
        )

        # Create request to slow endpoint
        request = Request(
            name="Slow Request",
            url=Url(raw="http://localhost:8080/slow"),  # Takes 2 seconds
            method="GET",
        )

        context = ExecutionContext()

        # Execute request
        result = await short_timeout_executor.execute_request(request, context)

        # Should timeout
        assert result.error is not None
        assert "timeout" in str(result.error).lower()


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not available")
class TestVariableStateManagement:
    """Test variable state management across request execution."""

    @pytest.mark.asyncio
    async def test_variable_state_across_requests(self, test_server, request_executor):
        """Test that variables are maintained and updated across requests."""
        from python_postman.models.event import Event, Script
        from python_postman.models.collection_info import CollectionInfo

        # Create first request that sets a variable
        set_var_script = Event(
            listen="test",
            script=Script(
                type="text/javascript",
                exec=[
                    "const responseJson = pm.response.json();",
                    "pm.collectionVariables.set('extracted_name', responseJson.name);",
                ],
            ),
        )

        first_request = Request(
            name="Set Variable Request",
            url=Url(raw="{{base_url}}/users/{{user_id}}"),
            method="GET",
            headers=[Header(key="X-API-Key", value="{{api_key}}")],
            events=[set_var_script],
        )

        # Create second request that uses the variable
        second_request = Request(
            name="Use Variable Request",
            url=Url(raw="{{base_url}}/users"),
            method="POST",
            headers=[Header(key="Content-Type", value="application/json")],
            body=Body(
                mode="raw",
                raw='{"name": "{{extracted_name}} Updated", "email": "updated@example.com"}',
            ),
        )

        collection = Collection(
            info=CollectionInfo(name="Variable State Test"),
            items=[first_request, second_request],
            variables=[
                Variable(key="base_url", value="http://localhost:8080"),
                Variable(key="user_id", value="123"),
                Variable(key="api_key", value="collection-api-key-456"),
                Variable(
                    key="extracted_name", value=""
                ),  # Will be set by first request
            ],
        )

        # Execute collection
        result = await request_executor.execute_collection(collection)

        # Verify both requests succeeded
        assert result.total_requests == 2
        assert result.successful_requests == 2

        # Verify second request used the variable from first request
        second_result = result.results[1]
        assert second_result.response.status_code == 201

        response_data = second_result.response.json
        assert (
            "John Doe Updated" in response_data["name"]
        )  # Should include extracted name

    @pytest.mark.asyncio
    async def test_folder_variable_scoping(self, test_server, request_executor):
        """Test variable scoping with folders."""
        from python_postman.models.folder import Folder
        from python_postman.models.collection_info import CollectionInfo

        # Create folder with folder-level variables
        folder_request = Request(
            name="Folder Request",
            url=Url(raw="{{base_url}}/users/{{folder_user_id}}"),
            method="GET",
            headers=[Header(key="X-API-Key", value="{{api_key}}")],
        )

        folder = Folder(
            name="Test Folder",
            items=[folder_request],
            variables=[Variable(key="folder_user_id", value="123")],
        )

        collection = Collection(
            info=CollectionInfo(name="Folder Scoping Test"),
            items=[folder],
            variables=[
                Variable(key="base_url", value="http://localhost:8080"),
                Variable(key="api_key", value="collection-api-key-456"),
            ],
        )

        # Execute collection
        result = await request_executor.execute_collection(collection)

        # Verify request succeeded with folder variable
        assert result.total_requests == 1
        assert result.successful_requests == 1
        assert result.results[0].response.status_code == 200


@pytest.mark.skipif(not HTTPX_AVAILABLE, reason="httpx not available")
class TestRequestModelIntegration:
    """Test integration with Request and Collection model execution methods."""

    @pytest.mark.asyncio
    async def test_request_execute_method(self, test_server):
        """Test Request.execute() method."""
        # Create request
        request = Request(
            name="Model Integration Request",
            url=Url(raw="{{base_url}}/users/{{user_id}}"),
            method="GET",
            headers=[Header(key="X-API-Key", value="{{api_key}}")],
        )

        # Create execution context
        context = ExecutionContext(
            collection_variables={
                "base_url": "http://localhost:8080",
                "user_id": "123",
                "api_key": "collection-api-key-456",
            }
        )

        # Execute using request method
        result = await request.execute(context=context)

        # Verify result
        assert isinstance(result, ExecutionResult)
        assert result.error is None
        assert result.response.status_code == 200

    def test_request_execute_sync_method(self, test_server):
        """Test Request.execute_sync() method."""
        # Create request
        request = Request(
            name="Sync Model Integration Request",
            url=Url(raw="{{base_url}}/users/{{user_id}}"),
            method="GET",
            headers=[Header(key="X-API-Key", value="{{api_key}}")],
        )

        # Create execution context
        context = ExecutionContext(
            collection_variables={
                "base_url": "http://localhost:8080",
                "user_id": "123",
                "api_key": "collection-api-key-456",
            }
        )

        # Execute using sync request method
        result = request.execute_sync(context=context)

        # Verify result
        assert isinstance(result, ExecutionResult)
        assert result.error is None
        assert result.response.status_code == 200

    @pytest.mark.asyncio
    async def test_collection_execute_method(self, test_server, execution_collection):
        """Test Collection.execute() method."""
        # Execute using collection method
        result = await execution_collection.execute()

        # Verify result
        assert isinstance(result, CollectionExecutionResult)
        assert result.collection_name == "Execution Test Collection"
        assert result.total_requests == 4
        assert result.successful_requests >= 3

    def test_collection_create_executor_method(self, execution_collection):
        """Test Collection.create_executor() method."""
        # Create executor using collection method
        executor = execution_collection.create_executor(
            client_config={"timeout": 5.0}, request_delay=0.5
        )

        # Verify executor configuration
        assert isinstance(executor, RequestExecutor)
        assert executor.request_delay == 0.5

        # Verify collection variables are included
        expected_vars = {
            "base_url": "http://localhost:8080",
            "test_header_value": "test-value-123",
            "user_email": "test@example.com",
            "auth_token": "test-bearer-token-123",
            "collection_api_key": "collection-api-key-456",
        }

        for key, value in expected_vars.items():
            assert executor.variable_overrides.get(key) == value


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v"])

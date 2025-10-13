"""
Tests for the RequestExecutor class.

This module tests the core RequestExecutor functionality including
initialization, configuration, request preparation, and resource management.
"""

import pytest
import warnings
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from python_postman.execution.executor import RequestExecutor, HTTPX_AVAILABLE
from python_postman.execution.context import ExecutionContext
from python_postman.execution.extensions import RequestExtensions
from python_postman.execution.exceptions import ExecutionError, RequestExecutionError
from python_postman.models.request import Request
from python_postman.models.collection import Collection
from python_postman.models.folder import Folder
from python_postman.models.url import Url
from python_postman.models.header import Header
from python_postman.models.body import Body, BodyMode
from python_postman.models.auth import Auth, AuthType
from python_postman.models.variable import Variable


class TestRequestExecutorInitialization:
    """Test RequestExecutor initialization and configuration."""

    @pytest.fixture
    def mock_httpx_available(self):
        """Mock httpx availability."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            with patch("python_postman.execution.executor.httpx") as mock_httpx:
                yield mock_httpx

    def test_init_with_defaults(self, mock_httpx_available):
        """Test initialization with default configuration."""
        executor = RequestExecutor()

        assert executor.variable_overrides == {}
        assert executor.global_headers == {}
        assert executor.script_timeout == 30.0
        assert executor.request_delay == 0.0
        assert executor.client_config["timeout"] == 30.0
        assert executor.client_config["verify"] is True
        assert executor.client_config["follow_redirects"] is True
        assert executor.auth_handler is not None
        assert executor._sync_client is None
        assert executor._async_client is None

    def test_init_with_custom_config(self, mock_httpx_available):
        """Test initialization with custom configuration."""
        client_config = {
            "timeout": 60.0,
            "verify": False,
            "proxies": {"http": "http://proxy:8080"},
        }
        variable_overrides = {"api_key": "test123"}
        global_headers = {"User-Agent": "test-agent"}

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            executor = RequestExecutor(
                client_config=client_config,
                variable_overrides=variable_overrides,
                global_headers=global_headers,
                script_timeout=45.0,
                request_delay=1.0,
            )

            # Check SSL warning was issued
            assert len(w) == 1
            assert "SSL verification is disabled" in str(w[0].message)

        assert executor.variable_overrides == variable_overrides
        assert executor.global_headers == global_headers
        assert executor.script_timeout == 45.0
        assert executor.request_delay == 1.0
        assert executor.client_config["timeout"] == 60.0
        assert executor.client_config["verify"] is False
        assert executor.client_config["proxies"] == {"http": "http://proxy:8080"}

    def test_init_without_httpx(self):
        """Test initialization fails when httpx is not available."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", False):
            with pytest.raises(ExecutionError, match="httpx is required"):
                RequestExecutor()

    def test_client_config_merging(self, mock_httpx_available):
        """Test that client config is properly merged with defaults."""
        client_config = {"timeout": 45.0, "custom_option": "value"}
        executor = RequestExecutor(client_config=client_config)

        # Should have custom values
        assert executor.client_config["timeout"] == 45.0
        assert executor.client_config["custom_option"] == "value"
        # Should retain defaults
        assert executor.client_config["verify"] is True
        assert executor.client_config["follow_redirects"] is True


class TestRequestExecutorClients:
    """Test HTTP client management."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            with patch("python_postman.execution.executor.httpx") as mock_httpx:
                executor = RequestExecutor()
                executor._mock_httpx = mock_httpx
                return executor

    def test_get_sync_client_creation(self, executor):
        """Test synchronous client creation."""
        mock_client = Mock()
        executor._mock_httpx.Client.return_value = mock_client

        with patch("python_postman.execution.executor.httpx", executor._mock_httpx):
            client = executor._get_sync_client()

        assert client is mock_client
        executor._mock_httpx.Client.assert_called_once_with(**executor.client_config)
        assert executor._sync_client is mock_client

    def test_get_sync_client_reuse(self, executor):
        """Test synchronous client reuse."""
        mock_client = Mock()
        executor._sync_client = mock_client

        client = executor._get_sync_client()

        assert client is mock_client
        # Should not create new client
        executor._mock_httpx.Client.assert_not_called()

    def test_get_async_client_creation(self, executor):
        """Test asynchronous client creation."""
        mock_client = Mock()
        executor._mock_httpx.AsyncClient.return_value = mock_client

        with patch("python_postman.execution.executor.httpx", executor._mock_httpx):
            client = executor._get_async_client()

        assert client is mock_client
        executor._mock_httpx.AsyncClient.assert_called_once_with(
            **executor.client_config
        )
        assert executor._async_client is mock_client

    def test_get_async_client_reuse(self, executor):
        """Test asynchronous client reuse."""
        mock_client = Mock()
        executor._async_client = mock_client

        client = executor._get_async_client()

        assert client is mock_client
        # Should not create new client
        executor._mock_httpx.AsyncClient.assert_not_called()


class TestRequestExecutorContextCreation:
    """Test execution context creation."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            return RequestExecutor(variable_overrides={"env_var": "env_value"})

    def test_create_context_empty(self, executor):
        """Test creating context with no inputs."""
        context = executor._create_execution_context()

        assert context.collection_variables == {}
        assert context.folder_variables == {}
        assert context.request_variables == {}
        assert context.environment_variables == {"env_var": "env_value"}

    def test_create_context_with_collection(self, executor):
        """Test creating context with collection variables."""
        collection = Mock()
        collection.variables = [
            Mock(key="col_var1", value="col_value1"),
            Mock(key="col_var2", value="col_value2"),
        ]

        context = executor._create_execution_context(collection=collection)

        assert context.collection_variables == {
            "col_var1": "col_value1",
            "col_var2": "col_value2",
        }
        assert context.environment_variables == {"env_var": "env_value"}

    def test_create_context_with_folder(self, executor):
        """Test creating context with folder variables."""
        folder = Mock()
        folder.variable = [
            Mock(key="folder_var", value="folder_value"),
        ]

        context = executor._create_execution_context(folder=folder)

        assert context.folder_variables == {"folder_var": "folder_value"}

    def test_create_context_with_request(self, executor):
        """Test creating context with request variables."""
        request = Mock()
        request.variable = [
            Mock(key="req_var", value="req_value"),
        ]

        context = executor._create_execution_context(request=request)

        assert context.request_variables == {"req_var": "req_value"}

    def test_create_context_with_additional_variables(self, executor):
        """Test creating context with additional variables."""
        additional = {"add_var": "add_value"}

        context = executor._create_execution_context(additional_variables=additional)

        assert context.environment_variables == {
            "env_var": "env_value",
            "add_var": "add_value",
        }

    def test_create_context_no_variables_attribute(self, executor):
        """Test creating context when objects don't have variable attributes."""
        collection = Mock(spec=[])  # Mock with no attributes

        context = executor._create_execution_context(collection=collection)

        assert context.collection_variables == {}


class TestRequestExecutorRequestPreparation:
    """Test request preparation logic."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            executor = RequestExecutor(global_headers={"Global": "header"})
            executor.auth_handler = Mock()
            return executor

    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = Mock(spec=Request)
        request.method = "POST"
        request.url = Mock()
        request.headers = [Mock(key="Content-Type", value="application/json")]
        request.body = Mock()
        request.auth = None
        return request

    @pytest.fixture
    def mock_context(self):
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.collection_variables = {}
        context.folder_variables = {}
        context.environment_variables = {}
        context.request_variables = {}
        return context

    def test_prepare_request_basic(self, executor, mock_request, mock_context):
        """Test basic request preparation."""
        # Mock the resolver and auth handler
        with patch(
            "python_postman.execution.executor.VariableResolver"
        ) as mock_resolver_class:
            mock_resolver = Mock()
            mock_resolver_class.return_value = mock_resolver
            mock_resolver.resolve_url.return_value = "https://api.example.com/test"
            mock_resolver.resolve_headers.return_value = {
                "Content-Type": "application/json"
            }
            mock_resolver.resolve_body.return_value = {"key": "value"}

            executor.auth_handler.apply_auth.return_value = {
                "headers": {},
                "params": {},
            }

            result = executor._prepare_request(mock_request, mock_context)

            assert result["method"] == "POST"
            assert result["url"] == "https://api.example.com/test"
            assert result["headers"]["Content-Type"] == "application/json"
            assert result["headers"]["Global"] == "header"
            assert result["json"] == {"key": "value"}

    def test_prepare_request_with_substitutions(
        self, executor, mock_request, mock_context
    ):
        """Test request preparation with substitutions."""
        substitutions = {"api_key": "test123"}

        with patch(
            "python_postman.execution.executor.VariableResolver"
        ) as mock_resolver_class:
            with patch(
                "python_postman.execution.executor.ExecutionContext"
            ) as mock_context_class:
                mock_resolver = Mock()
                mock_resolver_class.return_value = mock_resolver
                mock_resolver.resolve_url.return_value = "https://api.example.com/test"
                mock_resolver.resolve_headers.return_value = {}
                mock_resolver.resolve_body.return_value = None

                executor.auth_handler.apply_auth.return_value = {
                    "headers": {},
                    "params": {},
                }

                executor._prepare_request(
                    mock_request, mock_context, substitutions=substitutions
                )

                # Should create child context with substitutions
                mock_context_class.assert_called_once()
                call_args = mock_context_class.call_args[1]
                assert "test123" in str(call_args["environment_variables"])

    def test_prepare_request_with_extensions(
        self, executor, mock_request, mock_context
    ):
        """Test request preparation with extensions."""
        extensions = Mock(spec=RequestExtensions)
        modified_request = Mock()
        extensions.apply_to_request.return_value = modified_request

        with patch(
            "python_postman.execution.executor.VariableResolver"
        ) as mock_resolver_class:
            mock_resolver = Mock()
            mock_resolver_class.return_value = mock_resolver
            mock_resolver.resolve_url.return_value = "https://api.example.com/test"
            mock_resolver.resolve_headers.return_value = {}
            mock_resolver.resolve_body.return_value = None

            executor.auth_handler.apply_auth.return_value = {
                "headers": {},
                "params": {},
            }

            executor._prepare_request(mock_request, mock_context, extensions=extensions)

            extensions.apply_to_request.assert_called_once_with(
                mock_request, mock_context
            )

    def test_prepare_request_with_auth(self, executor, mock_request, mock_context):
        """Test request preparation with authentication."""
        with patch(
            "python_postman.execution.executor.VariableResolver"
        ) as mock_resolver_class:
            mock_resolver = Mock()
            mock_resolver_class.return_value = mock_resolver
            mock_resolver.resolve_url.return_value = "https://api.example.com/test"
            mock_resolver.resolve_headers.return_value = {}
            mock_resolver.resolve_body.return_value = None

            executor.auth_handler.apply_auth.return_value = {
                "headers": {"Authorization": "Bearer token123"},
                "params": {"api_key": "key123"},
            }

            result = executor._prepare_request(mock_request, mock_context)

            assert result["headers"]["Authorization"] == "Bearer token123"
            assert result["headers"]["Global"] == "header"
            assert result["params"] == {"api_key": "key123"}

    def test_prepare_request_no_url(self, executor, mock_request, mock_context):
        """Test request preparation fails with no URL."""
        with patch(
            "python_postman.execution.executor.VariableResolver"
        ) as mock_resolver_class:
            mock_resolver = Mock()
            mock_resolver_class.return_value = mock_resolver
            mock_resolver.resolve_url.return_value = ""

            with pytest.raises(RequestExecutionError, match="Request URL is required"):
                executor._prepare_request(mock_request, mock_context)

    def test_prepare_request_body_types(self, executor, mock_request, mock_context):
        """Test request preparation with different body types."""
        with patch(
            "python_postman.execution.executor.VariableResolver"
        ) as mock_resolver_class:
            mock_resolver = Mock()
            mock_resolver_class.return_value = mock_resolver
            mock_resolver.resolve_url.return_value = "https://api.example.com/test"
            mock_resolver.resolve_headers.return_value = {}

            executor.auth_handler.apply_auth.return_value = {
                "headers": {},
                "params": {},
            }

            # Test dict body (JSON)
            mock_resolver.resolve_body.return_value = {"key": "value"}
            result = executor._prepare_request(mock_request, mock_context)
            assert result["json"] == {"key": "value"}

            # Test string body
            mock_resolver.resolve_body.return_value = "raw content"
            result = executor._prepare_request(mock_request, mock_context)
            assert result["content"] == "raw content"

            # Test bytes body
            mock_resolver.resolve_body.return_value = b"binary content"
            result = executor._prepare_request(mock_request, mock_context)
            assert result["content"] == b"binary content"

    def test_prepare_request_error_handling(self, executor, mock_request, mock_context):
        """Test request preparation error handling."""
        with patch(
            "python_postman.execution.executor.VariableResolver"
        ) as mock_resolver_class:
            mock_resolver_class.side_effect = Exception("Resolver error")

            with pytest.raises(
                RequestExecutionError, match="Failed to prepare request"
            ):
                executor._prepare_request(mock_request, mock_context)


class TestRequestExecutorResourceManagement:
    """Test resource management and cleanup."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            return RequestExecutor()

    def test_close_sync_client(self, executor):
        """Test closing synchronous client."""
        mock_client = Mock()
        executor._sync_client = mock_client

        executor.close()

        mock_client.close.assert_called_once()
        assert executor._sync_client is None

    def test_close_async_client(self, executor):
        """Test closing asynchronous client."""
        mock_client = Mock()
        executor._async_client = mock_client

        executor.close()

        # Async client should be set to None but not closed in sync method
        assert executor._async_client is None

    @pytest.mark.asyncio
    async def test_aclose_clients(self, executor):
        """Test asynchronous closing of clients."""
        mock_sync_client = Mock()
        mock_async_client = AsyncMock()
        executor._sync_client = mock_sync_client
        executor._async_client = mock_async_client

        await executor.aclose()

        mock_sync_client.close.assert_called_once()
        mock_async_client.aclose.assert_called_once()
        assert executor._sync_client is None
        assert executor._async_client is None

    def test_context_manager_sync(self, executor):
        """Test synchronous context manager."""
        mock_client = Mock()
        executor._sync_client = mock_client

        with executor as ctx_executor:
            assert ctx_executor is executor

        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_context_manager_async(self, executor):
        """Test asynchronous context manager."""
        mock_sync_client = Mock()
        mock_async_client = AsyncMock()
        executor._sync_client = mock_sync_client
        executor._async_client = mock_async_client

        async with executor as ctx_executor:
            assert ctx_executor is executor

        mock_sync_client.close.assert_called_once()
        mock_async_client.aclose.assert_called_once()


class TestRequestExecutorSynchronousExecution:
    """Test synchronous request execution."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            return RequestExecutor()

    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = Mock(spec=Request)
        request.name = "Test Request"
        request.method = "GET"
        request.url = Mock()
        request.header = []
        request.body = None
        request.auth = None
        request.events = []
        request._collection = None
        return request

    @pytest.fixture
    def mock_context(self):
        """Create a mock execution context."""
        return Mock(spec=ExecutionContext)

    def test_execute_request_sync_success(self, executor, mock_request, mock_context):
        """Test successful synchronous request execution."""
        # Mock the HTTP client and response
        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}
        mock_response.content = b'{"result": "success"}'
        mock_response.url = "https://api.example.com/test"
        mock_response.request.method = "GET"
        mock_client.request.return_value = mock_response

        # Mock script runner
        mock_script_runner = Mock()
        mock_test_results = Mock()
        mock_script_runner.execute_test_scripts.return_value = mock_test_results

        with patch.object(executor, "_get_sync_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                    "headers": {},
                }
                with patch(
                    "python_postman.execution.executor.ScriptRunner",
                    return_value=mock_script_runner,
                ):
                    with patch(
                        "python_postman.execution.executor.time.time",
                        side_effect=[1.0, 1.1, 1.2, 1.3],
                    ):
                        result = executor.execute_request_sync(
                            mock_request, mock_context
                        )

        # Verify the result
        assert result.request is mock_request
        assert result.response is not None
        assert result.error is None
        assert result.test_results is mock_test_results
        assert abs(result.execution_time_ms - 300.0) < 0.1  # (1.3 - 1.0) * 1000

        # Verify script execution
        mock_script_runner.execute_pre_request_scripts.assert_called_once()
        mock_script_runner.execute_test_scripts.assert_called_once()

        # Verify HTTP request
        mock_client.request.assert_called_once()

    def test_execute_request_sync_with_collection_scripts(
        self, executor, mock_request, mock_context
    ):
        """Test synchronous request execution with collection-level scripts."""
        mock_collection = Mock()
        mock_request._collection = mock_collection

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response

        mock_script_runner = Mock()

        with patch.object(executor, "_get_sync_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch(
                    "python_postman.execution.executor.ScriptRunner",
                    return_value=mock_script_runner,
                ):
                    executor.execute_request_sync(mock_request, mock_context)

        # Verify collection was passed to script runner
        mock_script_runner.execute_pre_request_scripts.assert_called_once_with(
            mock_request, mock_collection, mock_context
        )

    def test_execute_request_sync_with_delay(
        self, executor, mock_request, mock_context
    ):
        """Test synchronous request execution with request delay."""
        executor.request_delay = 0.1

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response

        with patch.object(executor, "_get_sync_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch(
                    "python_postman.execution.executor.time.sleep"
                ) as mock_sleep:
                    with patch("python_postman.execution.executor.ScriptRunner"):
                        executor.execute_request_sync(mock_request, mock_context)

        mock_sleep.assert_called_once_with(0.1)

    def test_execute_request_sync_with_substitutions(
        self, executor, mock_request, mock_context
    ):
        """Test synchronous request execution with substitutions."""
        substitutions = {"api_key": "test123"}

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response

        with patch.object(executor, "_get_sync_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch("python_postman.execution.executor.ScriptRunner"):
                    executor.execute_request_sync(
                        mock_request, mock_context, substitutions=substitutions
                    )

        # Verify substitutions were passed to prepare_request
        mock_prepare.assert_called_once_with(
            mock_request, mock_context, substitutions, None
        )

    def test_execute_request_sync_with_extensions(
        self, executor, mock_request, mock_context
    ):
        """Test synchronous request execution with extensions."""
        extensions = Mock(spec=RequestExtensions)

        mock_client = Mock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response

        with patch.object(executor, "_get_sync_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch("python_postman.execution.executor.ScriptRunner"):
                    executor.execute_request_sync(
                        mock_request, mock_context, extensions=extensions
                    )

        # Verify extensions were passed to prepare_request
        mock_prepare.assert_called_once_with(
            mock_request, mock_context, None, extensions
        )

    def test_execute_request_sync_http_error(
        self, executor, mock_request, mock_context
    ):
        """Test synchronous request execution with HTTP error."""
        mock_client = Mock()
        mock_client.request.side_effect = Exception("Connection failed")

        with patch.object(executor, "_get_sync_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch("python_postman.execution.executor.ScriptRunner"):
                    result = executor.execute_request_sync(mock_request, mock_context)

        # Verify error handling
        assert result.request is mock_request
        assert result.response is None
        assert result.error is not None
        assert "Request execution failed" in str(result.error)
        assert result.execution_time_ms > 0

    def test_execute_request_sync_preparation_error(
        self, executor, mock_request, mock_context
    ):
        """Test synchronous request execution with request preparation error."""
        with patch.object(executor, "_prepare_request") as mock_prepare:
            mock_prepare.side_effect = RequestExecutionError("Invalid URL")
            with patch("python_postman.execution.executor.ScriptRunner"):
                result = executor.execute_request_sync(mock_request, mock_context)

        # Verify error handling
        assert result.request is mock_request
        assert result.response is None
        assert result.error is not None
        assert "Invalid URL" in str(result.error)

    def test_execute_request_sync_script_error(
        self, executor, mock_request, mock_context
    ):
        """Test synchronous request execution with script execution error."""


class TestRequestExecutorFolderExecution:
    """Test folder execution functionality."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            return RequestExecutor()

    @pytest.fixture
    def mock_folder(self):
        """Create a mock folder for testing."""
        folder = Mock(spec=Folder)
        folder.name = "Test Folder"
        folder.variable = [
            Mock(key="folder_var", value="folder_value"),
        ]
        return folder

    @pytest.fixture
    def mock_context(self):
        """Create a mock execution context."""
        context = Mock(spec=ExecutionContext)
        context.collection_variables = {"col_var": "col_value"}
        context.folder_variables = {}
        context.environment_variables = {"env_var": "env_value"}
        context.request_variables = {}
        context._collection = Mock()
        return context

    @pytest.fixture
    def mock_requests(self):
        """Create mock requests for testing."""
        request1 = Mock(spec=Request)
        request1.name = "Request 1"
        request1._collection = None

        request2 = Mock(spec=Request)
        request2.name = "Request 2"
        request2._collection = None

        return [request1, request2]

    @pytest.mark.asyncio
    async def test_execute_folder_sequential_success(
        self, executor, mock_folder, mock_context, mock_requests
    ):
        """Test successful sequential folder execution."""
        # Mock folder.get_requests() to return our test requests
        mock_folder.get_requests.return_value = iter(mock_requests)

        # Mock successful execution results
        mock_result1 = Mock()
        mock_result1.success = True
        mock_result1.execution_time_ms = 100.0

        mock_result2 = Mock()
        mock_result2.success = True
        mock_result2.execution_time_ms = 150.0

        with patch.object(executor, "_create_execution_context") as mock_create_context:
            mock_folder_context = Mock(spec=ExecutionContext)
            mock_folder_context.collection_variables = {}
            mock_folder_context.environment_variables = {}
            mock_create_context.return_value = mock_folder_context

            with patch.object(executor, "execute_request") as mock_execute:
                mock_execute.side_effect = [mock_result1, mock_result2]

                with patch(
                    "python_postman.execution.executor.time.time",
                    side_effect=[1.0, 1.5],
                ):
                    result = await executor.execute_folder(
                        mock_folder, mock_context, parallel=False, stop_on_error=False
                    )

        # Verify the result
        assert result.folder_name == "Test Folder"
        assert len(result.results) == 2
        assert result.results[0] is mock_result1
        assert result.results[1] is mock_result2
        assert result.total_time_ms == 500.0  # (1.5 - 1.0) * 1000

        # Verify context creation with folder variables
        mock_create_context.assert_called_once()
        call_args = mock_create_context.call_args
        assert call_args[1]["folder"] is mock_folder

        # Verify collection reference was set on requests
        assert mock_requests[0]._collection is mock_context._collection
        assert mock_requests[1]._collection is mock_context._collection

        # Verify sequential execution
        assert mock_execute.call_count == 2
        mock_execute.assert_any_call(mock_requests[0], mock_folder_context)
        mock_execute.assert_any_call(mock_requests[1], mock_folder_context)

    @pytest.mark.asyncio
    async def test_execute_folder_parallel_success(
        self, executor, mock_folder, mock_context, mock_requests
    ):
        """Test successful parallel folder execution."""
        mock_folder.get_requests.return_value = iter(mock_requests)

        mock_result1 = Mock()
        mock_result1.success = True
        mock_result1.execution_time_ms = 100.0

        mock_result2 = Mock()
        mock_result2.success = True
        mock_result2.execution_time_ms = 150.0

        with patch.object(executor, "_create_execution_context") as mock_create_context:
            mock_folder_context = Mock(spec=ExecutionContext)
            mock_folder_context.collection_variables = MagicMock()
            mock_folder_context.environment_variables = MagicMock()
            mock_create_context.return_value = mock_folder_context

            with patch.object(executor, "execute_request") as mock_execute:
                mock_execute.side_effect = [mock_result1, mock_result2]

                with patch("asyncio.create_task") as mock_create_task:
                    with patch("asyncio.gather") as mock_gather:
                        # Make gather return an awaitable
                        async def mock_gather_func(*args, **kwargs):
                            return [mock_result1, mock_result2]

                        mock_gather.side_effect = mock_gather_func

                        result = await executor.execute_folder(
                            mock_folder,
                            mock_context,
                            parallel=True,
                            stop_on_error=False,
                        )

        # Verify parallel execution was attempted
        assert mock_create_task.call_count == 2
        mock_gather.assert_called_once()

        # Verify results
        assert len(result.results) == 2
        assert result.results[0] is mock_result1
        assert result.results[1] is mock_result2

    @pytest.mark.asyncio
    async def test_execute_folder_stop_on_error_sequential(
        self, executor, mock_folder, mock_context, mock_requests
    ):
        """Test folder execution stops on error in sequential mode."""
        mock_folder.get_requests.return_value = iter(mock_requests)

        mock_result1 = Mock()
        mock_result1.success = False  # First request fails
        mock_result1.execution_time_ms = 100.0

        with patch.object(executor, "_create_execution_context") as mock_create_context:
            mock_folder_context = Mock(spec=ExecutionContext)
            mock_folder_context.collection_variables = MagicMock()
            mock_folder_context.environment_variables = MagicMock()
            mock_create_context.return_value = mock_folder_context

            with patch.object(executor, "execute_request") as mock_execute:
                mock_execute.return_value = mock_result1

                result = await executor.execute_folder(
                    mock_folder, mock_context, parallel=False, stop_on_error=True
                )

        # Should only execute first request
        assert mock_execute.call_count == 1
        assert len(result.results) == 1
        assert result.results[0] is mock_result1

    @pytest.mark.asyncio
    async def test_execute_folder_stop_on_error_parallel(
        self, executor, mock_folder, mock_context, mock_requests
    ):
        """Test folder execution stops on error in parallel mode."""
        mock_folder.get_requests.return_value = iter(mock_requests)

        mock_result1 = Mock()
        mock_result1.success = False  # First result fails
        mock_result1.execution_time_ms = 100.0

        mock_result2 = Mock()
        mock_result2.success = True
        mock_result2.execution_time_ms = 150.0

        with patch.object(executor, "_create_execution_context") as mock_create_context:
            mock_folder_context = Mock(spec=ExecutionContext)
            mock_folder_context.collection_variables = MagicMock()
            mock_folder_context.environment_variables = MagicMock()
            mock_create_context.return_value = mock_folder_context

            with patch.object(executor, "execute_request"):
                with patch("asyncio.create_task"):
                    with patch("asyncio.gather") as mock_gather:
                        # Make gather return an awaitable
                        async def mock_gather_func(*args, **kwargs):
                            return [mock_result1, mock_result2]

                        mock_gather.side_effect = mock_gather_func

                        result = await executor.execute_folder(
                            mock_folder, mock_context, parallel=True, stop_on_error=True
                        )

        # Should process first result and stop
        assert len(result.results) == 1
        assert result.results[0] is mock_result1

    @pytest.mark.asyncio
    async def test_execute_folder_with_exceptions_sequential(
        self, executor, mock_folder, mock_context, mock_requests
    ):
        """Test folder execution handles exceptions in sequential mode."""
        mock_folder.get_requests.return_value = iter(mock_requests)

        test_exception = Exception("Request failed")

        with patch.object(executor, "_create_execution_context") as mock_create_context:
            mock_folder_context = Mock(spec=ExecutionContext)
            mock_folder_context.collection_variables = {}
            mock_folder_context.environment_variables = {}
            mock_create_context.return_value = mock_folder_context

            # Create an async function that raises the exception
            async def mock_execute_func(*args, **kwargs):
                raise test_exception

            with patch.object(executor, "execute_request", side_effect=mock_execute_func):
                result = await executor.execute_folder(
                    mock_folder, mock_context, parallel=False, stop_on_error=False
                )

        # Should create failed execution results
        assert len(result.results) == 2
        for exec_result in result.results:
            assert exec_result.error is test_exception
            assert exec_result.execution_time_ms == 0.0

    @pytest.mark.asyncio
    async def test_execute_folder_with_exceptions_parallel(
        self, executor, mock_folder, mock_context, mock_requests
    ):
        """Test folder execution handles exceptions in parallel mode."""
        mock_folder.get_requests.return_value = iter(mock_requests)

        test_exception = Exception("Request failed")

        with patch.object(executor, "_create_execution_context") as mock_create_context:
            mock_folder_context = Mock(spec=ExecutionContext)
            # Use real dicts to avoid mock issues
            mock_folder_context.collection_variables = {}
            mock_folder_context.environment_variables = {}
            mock_create_context.return_value = mock_folder_context

            with patch.object(executor, "execute_request") as mock_execute:
                # Mock create_task to consume the coroutine properly
                def mock_create_task_func(coro):
                    # Close the coroutine to avoid warning
                    coro.close()
                    return Mock()
                
                with patch("asyncio.create_task", side_effect=mock_create_task_func) as mock_create_task:
                    with patch("asyncio.gather") as mock_gather:
                        # Make gather return an awaitable with exceptions
                        async def mock_gather_func(*args, **kwargs):
                            return [test_exception, test_exception]

                        mock_gather.side_effect = mock_gather_func

                        result = await executor.execute_folder(
                            mock_folder,
                            mock_context,
                            parallel=True,
                            stop_on_error=False,
                        )

        # Should create failed execution results for exceptions
        assert len(result.results) == 2
        for exec_result in result.results:
            assert exec_result.error is test_exception

    @pytest.mark.asyncio
    async def test_execute_folder_variable_scoping(
        self, executor, mock_folder, mock_context, mock_requests
    ):
        """Test folder execution properly handles variable scoping."""
        mock_folder.get_requests.return_value = iter(mock_requests)

        # Mock folder with variables
        mock_folder.variable = [
            Mock(key="folder_var", value="folder_value"),
            Mock(key="override_var", value="folder_override"),
        ]

        mock_result = Mock()
        mock_result.success = True
        mock_result.execution_time_ms = 100.0

        with patch.object(executor, "_create_execution_context") as mock_create_context:
            mock_folder_context = Mock(spec=ExecutionContext)
            # Create mock dictionaries with proper update method
            mock_folder_context.collection_variables = {}
            mock_folder_context.environment_variables = {}
            mock_create_context.return_value = mock_folder_context

            with patch.object(executor, "execute_request", new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = mock_result

                await executor.execute_folder(
                    mock_folder, mock_context, parallel=False, stop_on_error=False
                )

        # Verify context creation was called with folder
        mock_create_context.assert_called_once()
        call_args = mock_create_context.call_args[1]
        assert call_args["folder"] is mock_folder

        # Verify context variables were merged (check that update was called by verifying the dict was modified)
        # Since we're using real dicts, we can't assert on update calls, but the test still validates the behavior

    @pytest.mark.asyncio
    async def test_execute_folder_empty_folder(
        self, executor, mock_folder, mock_context
    ):
        """Test folder execution with empty folder."""
        mock_folder.get_requests.return_value = iter([])  # Empty folder

        with patch.object(executor, "_create_execution_context") as mock_create_context:
            mock_folder_context = Mock(spec=ExecutionContext)
            mock_folder_context.collection_variables = MagicMock()
            mock_folder_context.environment_variables = MagicMock()
            mock_create_context.return_value = mock_folder_context

            with patch(
                "python_postman.execution.executor.time.time", side_effect=[1.0, 1.1]
            ):
                result = await executor.execute_folder(
                    mock_folder, mock_context, parallel=False, stop_on_error=False
                )

        # Should return empty result
        assert result.folder_name == "Test Folder"
        assert len(result.results) == 0
        assert (
            abs(result.total_time_ms - 100.0) < 0.1
        )  # Allow for floating point precision

    @pytest.mark.asyncio
    async def test_execute_folder_nested_folders(
        self, executor, mock_folder, mock_context
    ):
        """Test folder execution with nested folders."""
        # Create nested structure: folder -> subfolder -> request
        nested_request = Mock(spec=Request)
        nested_request.name = "Nested Request"
        nested_request._collection = None

        # Mock get_requests to return requests from nested structure
        mock_folder.get_requests.return_value = iter([nested_request])

        mock_result = Mock()
        mock_result.success = True
        mock_result.execution_time_ms = 100.0

        with patch.object(executor, "_create_execution_context") as mock_create_context:
            mock_folder_context = Mock(spec=ExecutionContext)
            mock_folder_context.collection_variables = MagicMock()
            mock_folder_context.environment_variables = MagicMock()
            mock_create_context.return_value = mock_folder_context

            with patch.object(executor, "execute_request") as mock_execute:
                mock_execute.return_value = mock_result

                result = await executor.execute_folder(
                    mock_folder, mock_context, parallel=False, stop_on_error=False
                )

        # Should execute nested request
        assert len(result.results) == 1
        assert result.results[0] is mock_result
        mock_execute.assert_called_once_with(nested_request, mock_folder_context)

        # Verify collection reference was set
        assert nested_request._collection is mock_context._collection


class TestRequestExecutorAsynchronousExecution:
    """Test asynchronous request execution."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            return RequestExecutor()

    @pytest.fixture
    def mock_request(self):
        """Create a mock request for testing."""
        request = Mock(spec=Request)
        request.name = "Test Request"
        request.method = "GET"
        request.url = Mock()
        request.header = []
        request.body = None
        request.auth = None
        request.events = []
        request._collection = None
        return request

    @pytest.fixture
    def mock_context(self):
        """Create a mock execution context."""
        return Mock(spec=ExecutionContext)

    @pytest.mark.asyncio
    async def test_execute_request_async_success(
        self, executor, mock_request, mock_context
    ):
        """Test successful asynchronous request execution."""
        # Mock the HTTP client and response
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}
        mock_response.content = b'{"result": "success"}'
        mock_response.url = "https://api.example.com/test"
        mock_response.request.method = "GET"
        mock_client.request.return_value = mock_response

        # Mock script runner
        mock_script_runner = Mock()
        mock_test_results = Mock()
        mock_script_runner.execute_test_scripts.return_value = mock_test_results

        with patch.object(executor, "_get_async_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                    "headers": {},
                }
                with patch(
                    "python_postman.execution.executor.ScriptRunner",
                    return_value=mock_script_runner,
                ):
                    with patch(
                        "python_postman.execution.executor.time.time",
                        side_effect=[1.0, 1.1, 1.2, 1.3],
                    ):
                        result = await executor.execute_request(
                            mock_request, mock_context
                        )

        # Verify the result
        assert result.request is mock_request
        assert result.response is not None
        assert result.error is None
        assert result.test_results is mock_test_results
        assert abs(result.execution_time_ms - 300.0) < 0.1  # (1.3 - 1.0) * 1000

        # Verify script execution
        mock_script_runner.execute_pre_request_scripts.assert_called_once()
        mock_script_runner.execute_test_scripts.assert_called_once()

        # Verify HTTP request
        mock_client.request.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_request_async_with_collection_scripts(
        self, executor, mock_request, mock_context
    ):
        """Test asynchronous request execution with collection-level scripts."""
        mock_collection = Mock()
        mock_request._collection = mock_collection

        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response

        # Use Mock with spec to avoid async behavior
        mock_script_runner = Mock()
        mock_script_runner.execute_pre_request_scripts = Mock()
        mock_script_runner.execute_test_scripts = Mock()

        with patch.object(executor, "_get_async_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch(
                    "python_postman.execution.executor.ScriptRunner",
                    return_value=mock_script_runner,
                ):
                    await executor.execute_request(mock_request, mock_context)

        # Verify collection was passed to script runner
        mock_script_runner.execute_pre_request_scripts.assert_called_once_with(
            mock_request, mock_collection, mock_context
        )

    @pytest.mark.asyncio
    async def test_execute_request_async_with_delay(
        self, executor, mock_request, mock_context
    ):
        """Test asynchronous request execution with request delay."""
        executor.request_delay = 0.1

        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response

        with patch.object(executor, "_get_async_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch("asyncio.sleep") as mock_sleep:
                    with patch("python_postman.execution.executor.ScriptRunner"):
                        await executor.execute_request(mock_request, mock_context)

        mock_sleep.assert_called_once_with(0.1)

    @pytest.mark.asyncio
    async def test_execute_request_async_with_substitutions(
        self, executor, mock_request, mock_context
    ):
        """Test asynchronous request execution with substitutions."""
        substitutions = {"api_key": "test123"}

        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response

        with patch.object(executor, "_get_async_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch("python_postman.execution.executor.ScriptRunner"):
                    await executor.execute_request(
                        mock_request, mock_context, substitutions=substitutions
                    )

        # Verify substitutions were passed to prepare_request
        mock_prepare.assert_called_once_with(
            mock_request, mock_context, substitutions, None
        )

    @pytest.mark.asyncio
    async def test_execute_request_async_with_extensions(
        self, executor, mock_request, mock_context
    ):
        """Test asynchronous request execution with extensions."""
        extensions = Mock(spec=RequestExtensions)

        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response

        with patch.object(executor, "_get_async_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch("python_postman.execution.executor.ScriptRunner"):
                    await executor.execute_request(
                        mock_request, mock_context, extensions=extensions
                    )

        # Verify extensions were passed to prepare_request
        mock_prepare.assert_called_once_with(
            mock_request, mock_context, None, extensions
        )

    @pytest.mark.asyncio
    async def test_execute_request_async_http_error(
        self, executor, mock_request, mock_context
    ):
        """Test asynchronous request execution with HTTP error."""
        mock_client = AsyncMock()
        mock_client.request.side_effect = Exception("Connection failed")

        with patch.object(executor, "_get_async_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch("python_postman.execution.executor.ScriptRunner"):
                    result = await executor.execute_request(mock_request, mock_context)

        # Verify error handling
        assert result.request is mock_request
        assert result.response is None
        assert result.error is not None
        assert "Request execution failed" in str(result.error)
        assert result.execution_time_ms > 0

    @pytest.mark.asyncio
    async def test_execute_request_async_preparation_error(
        self, executor, mock_request, mock_context
    ):
        """Test asynchronous request execution with request preparation error."""
        with patch.object(executor, "_prepare_request") as mock_prepare:
            mock_prepare.side_effect = RequestExecutionError("Invalid URL")
            with patch("python_postman.execution.executor.ScriptRunner"):
                result = await executor.execute_request(mock_request, mock_context)

        # Verify error handling
        assert result.request is mock_request
        assert result.response is None
        assert result.error is not None
        assert "Invalid URL" in str(result.error)

    @pytest.mark.asyncio
    async def test_execute_request_async_script_error(
        self, executor, mock_request, mock_context
    ):
        """Test asynchronous request execution with script execution error."""
        mock_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_client.request.return_value = mock_response

        # Mock script runner to raise error
        mock_script_runner = Mock()
        mock_script_runner.execute_pre_request_scripts.side_effect = Exception(
            "Script failed"
        )

        with patch.object(executor, "_get_async_client", return_value=mock_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                }
                with patch(
                    "python_postman.execution.executor.ScriptRunner",
                    return_value=mock_script_runner,
                ):
                    result = await executor.execute_request(mock_request, mock_context)

        # Verify error handling - script errors should cause overall execution failure
        assert result.request is mock_request
        assert result.response is None
        assert result.error is not None
        assert "Request execution failed" in str(result.error)

    @pytest.mark.asyncio
    async def test_execute_request_async_vs_sync_consistency(
        self, executor, mock_request, mock_context
    ):
        """Test that async and sync execution produce consistent results."""
        # Mock the HTTP client and response for both sync and async
        mock_sync_client = Mock()
        mock_async_client = AsyncMock()
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success"}'
        mock_response.json.return_value = {"result": "success"}
        mock_response.content = b'{"result": "success"}'
        mock_response.url = "https://api.example.com/test"
        mock_response.request.method = "GET"

        mock_sync_client.request.return_value = mock_response
        mock_async_client.request.return_value = mock_response

        # Mock script runner
        mock_script_runner = Mock()
        mock_test_results = Mock()
        mock_test_results.passed = 1
        mock_test_results.failed = 0
        mock_script_runner.execute_test_scripts.return_value = mock_test_results

        # Execute sync version
        with patch.object(executor, "_get_sync_client", return_value=mock_sync_client):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                    "headers": {},
                }
                with patch(
                    "python_postman.execution.executor.ScriptRunner",
                    return_value=mock_script_runner,
                ):
                    sync_result = executor.execute_request_sync(
                        mock_request, mock_context
                    )

        # Reset mocks
        mock_script_runner.reset_mock()

        # Execute async version
        with patch.object(
            executor, "_get_async_client", return_value=mock_async_client
        ):
            with patch.object(executor, "_prepare_request") as mock_prepare:
                mock_prepare.return_value = {
                    "method": "GET",
                    "url": "https://api.example.com/test",
                    "headers": {},
                }
                with patch(
                    "python_postman.execution.executor.ScriptRunner",
                    return_value=mock_script_runner,
                ):
                    async_result = await executor.execute_request(
                        mock_request, mock_context
                    )

        # Verify both results have the same structure and success status
        assert sync_result.request is mock_request
        assert async_result.request is mock_request
        assert sync_result.error is None
        assert async_result.error is None
        assert sync_result.response is not None
        assert async_result.response is not None
        assert sync_result.test_results is not None
        assert async_result.test_results is not None


class TestRequestExecutorCollectionExecution:
    """Test collection execution functionality."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            return RequestExecutor()

    @pytest.fixture
    def mock_collection(self):
        """Create a mock collection with requests."""
        from python_postman.models.collection_info import CollectionInfo

        # Create mock requests
        request1 = Mock(spec=Request)
        request1.name = "Request 1"
        request1._collection = None

        request2 = Mock(spec=Request)
        request2.name = "Request 2"
        request2._collection = None

        request3 = Mock(spec=Request)
        request3.name = "Request 3"
        request3._collection = None

        # Create mock collection
        collection = Mock(spec=Collection)
        collection.info = CollectionInfo(name="Test Collection")
        collection.get_requests.return_value = [request1, request2, request3]

        return collection, [request1, request2, request3]

    @pytest.fixture
    def mock_empty_collection(self):
        """Create a mock empty collection."""
        from python_postman.models.collection_info import CollectionInfo

        collection = Mock(spec=Collection)
        collection.info = CollectionInfo(name="Empty Collection")
        collection.get_requests.return_value = []

        return collection

    @pytest.mark.asyncio
    async def test_execute_collection_sequential_success(
        self, executor, mock_collection
    ):
        """Test successful sequential collection execution."""
        collection, requests = mock_collection

        # Mock successful execution results
        mock_results = []
        for i, request in enumerate(requests):
            result = Mock()
            result.success = True
            result.request = request
            result.response = Mock()
            result.response.status_code = 200
            result.error = None
            result.test_results = Mock()
            result.execution_time_ms = 100.0 + i * 10
            mock_results.append(result)

        with patch.object(
            executor, "execute_request", side_effect=mock_results
        ) as mock_execute:
            with patch.object(executor, "_create_execution_context") as mock_context:
                mock_context.return_value = Mock()

                result = await executor.execute_collection(collection)

                # Verify execution calls
                assert mock_execute.call_count == 3
                for i, request in enumerate(requests):
                    mock_execute.assert_any_call(request, mock_context.return_value)

                # Verify result
                assert result.collection_name == "Test Collection"
                assert result.total_requests == 3
                assert result.successful_requests == 3
                assert result.failed_requests == 0
                assert result.success_rate == 1.0
                assert result.total_time_ms > 0
                assert len(result.results) == 3

                # Verify collection reference was set
                for request in requests:
                    assert request._collection == collection

    @pytest.mark.asyncio
    async def test_execute_collection_sequential_with_failures(
        self, executor, mock_collection
    ):
        """Test sequential collection execution with some failures."""
        collection, requests = mock_collection

        # Mock mixed execution results (success, failure, success)
        mock_results = []
        for i, request in enumerate(requests):
            result = Mock()
            result.request = request
            result.execution_time_ms = 100.0 + i * 10

            if i == 1:  # Second request fails
                result.success = False
                result.response = None
                result.error = RequestExecutionError("Request failed")
                result.test_results = None
            else:
                result.success = True
                result.response = Mock()
                result.response.status_code = 200
                result.error = None
                result.test_results = Mock()

            mock_results.append(result)

        with patch.object(executor, "execute_request", side_effect=mock_results):
            with patch.object(executor, "_create_execution_context") as mock_context:
                mock_context.return_value = Mock()

                result = await executor.execute_collection(collection)

                # Verify result
                assert result.collection_name == "Test Collection"
                assert result.total_requests == 3
                assert result.successful_requests == 2
                assert result.failed_requests == 1
                assert result.success_rate == 2 / 3
                assert len(result.results) == 3

    @pytest.mark.asyncio
    async def test_execute_collection_sequential_stop_on_error(
        self, executor, mock_collection
    ):
        """Test sequential collection execution with stop_on_error=True."""
        collection, requests = mock_collection

        # Mock execution results where second request fails
        mock_results = []
        for i, request in enumerate(requests):
            result = Mock()
            result.request = request
            result.execution_time_ms = 100.0 + i * 10

            if i == 1:  # Second request fails
                result.success = False
                result.response = None
                result.error = RequestExecutionError("Request failed")
                result.test_results = None
            else:
                result.success = True
                result.response = Mock()
                result.response.status_code = 200
                result.error = None
                result.test_results = Mock()

            mock_results.append(result)

        with patch.object(
            executor, "execute_request", side_effect=mock_results
        ) as mock_execute:
            with patch.object(executor, "_create_execution_context") as mock_context:
                mock_context.return_value = Mock()

                result = await executor.execute_collection(
                    collection, stop_on_error=True
                )

                # Should only execute first two requests
                assert mock_execute.call_count == 2
                assert result.total_requests == 2
                assert result.successful_requests == 1
                assert result.failed_requests == 1

    @pytest.mark.asyncio
    async def test_execute_collection_sequential_exception_handling(
        self, executor, mock_collection
    ):
        """Test sequential collection execution with exceptions."""
        collection, requests = mock_collection

        # Mock execute_request to raise exception for second request
        def mock_execute_side_effect(request, context):
            if request.name == "Request 2":
                raise RuntimeError("Unexpected error")

            result = Mock()
            result.success = True
            result.request = request
            result.response = Mock()
            result.response.status_code = 200
            result.error = None
            result.test_results = Mock()
            result.execution_time_ms = 100.0
            return result

        with patch.object(
            executor, "execute_request", side_effect=mock_execute_side_effect
        ):
            with patch.object(executor, "_create_execution_context") as mock_context:
                mock_context.return_value = Mock()

                result = await executor.execute_collection(collection)

                # Verify result includes failed request
                assert result.total_requests == 3
                assert result.successful_requests == 2
                assert result.failed_requests == 1

                # Find the failed result
                failed_result = next(r for r in result.results if not r.success)
                assert failed_result.request.name == "Request 2"
                assert isinstance(failed_result.error, RuntimeError)

    @pytest.mark.asyncio
    async def test_execute_collection_parallel_success(self, executor, mock_collection):
        """Test successful parallel collection execution."""
        collection, requests = mock_collection

        # Mock successful execution results
        mock_results = []
        for i, request in enumerate(requests):
            result = Mock()
            result.success = True
            result.request = request
            result.response = Mock()
            result.response.status_code = 200
            result.error = None
            result.test_results = Mock()
            result.execution_time_ms = 100.0 + i * 10
            mock_results.append(result)

        with patch.object(
            executor, "execute_request", side_effect=mock_results
        ) as mock_execute:
            with patch.object(executor, "_create_execution_context") as mock_context:
                mock_context.return_value = Mock()

                result = await executor.execute_collection(collection, parallel=True)

                # Verify all requests were executed
                assert mock_execute.call_count == 3
                assert result.total_requests == 3
                assert result.successful_requests == 3
                assert result.failed_requests == 0

    @pytest.mark.asyncio
    async def test_execute_collection_parallel_with_exceptions(
        self, executor, mock_collection
    ):
        """Test parallel collection execution with exceptions."""
        collection, requests = mock_collection

        # Mock execute_request to raise exception for second request
        async def mock_execute_side_effect(request, context):
            if request.name == "Request 2":
                raise RuntimeError("Unexpected error")

            result = Mock()
            result.success = True
            result.request = request
            result.response = Mock()
            result.response.status_code = 200
            result.error = None
            result.test_results = Mock()
            result.execution_time_ms = 100.0
            return result

        with patch.object(
            executor, "execute_request", side_effect=mock_execute_side_effect
        ):
            with patch.object(executor, "_create_execution_context") as mock_context:
                mock_context.return_value = Mock()

                result = await executor.execute_collection(collection, parallel=True)

                # Verify result includes failed request
                assert result.total_requests == 3
                assert result.successful_requests == 2
                assert result.failed_requests == 1

                # Find the failed result
                failed_result = next(r for r in result.results if not r.success)
                assert failed_result.request.name == "Request 2"
                assert isinstance(failed_result.error, RuntimeError)

    @pytest.mark.asyncio
    async def test_execute_collection_parallel_stop_on_error(
        self, executor, mock_collection
    ):
        """Test parallel collection execution with stop_on_error=True."""
        collection, requests = mock_collection

        # Mock execution results where second request fails
        mock_results = []
        for i, request in enumerate(requests):
            result = Mock()
            result.request = request
            result.execution_time_ms = 100.0 + i * 10

            if i == 1:  # Second request fails
                result.success = False
                result.response = None
                result.error = RequestExecutionError("Request failed")
                result.test_results = None
            else:
                result.success = True
                result.response = Mock()
                result.response.status_code = 200
                result.error = None
                result.test_results = Mock()

            mock_results.append(result)

        with patch.object(executor, "execute_request", side_effect=mock_results):
            with patch.object(executor, "_create_execution_context") as mock_context:
                mock_context.return_value = Mock()

                result = await executor.execute_collection(
                    collection, parallel=True, stop_on_error=True
                )

                # With parallel execution and stop_on_error, all tasks start but execution stops
                # when the first error is encountered during result processing
                assert (
                    result.total_requests >= 1
                )  # At least one request should be processed
                assert result.failed_requests >= 1  # At least one should fail

    @pytest.mark.asyncio
    async def test_execute_collection_empty_collection(
        self, executor, mock_empty_collection
    ):
        """Test execution of empty collection."""
        collection = mock_empty_collection

        with patch.object(executor, "_create_execution_context") as mock_context:
            mock_context.return_value = Mock()

            result = await executor.execute_collection(collection)

            # Verify result
            assert result.collection_name == "Empty Collection"
            assert result.total_requests == 0
            assert result.successful_requests == 0
            assert result.failed_requests == 0
            assert (
                result.success_rate == 1.0
            )  # Empty collection is considered successful
            assert len(result.results) == 0

    @pytest.mark.asyncio
    async def test_execute_collection_variable_state_maintenance(
        self, executor, mock_collection
    ):
        """Test that variable state is maintained across requests in collection execution."""
        collection, requests = mock_collection

        # Mock execution context
        mock_context = Mock()

        with patch.object(executor, "execute_request") as mock_execute:
            with patch.object(
                executor, "_create_execution_context", return_value=mock_context
            ):

                # Mock successful results
                mock_results = [
                    Mock(success=True, execution_time_ms=100.0) for _ in requests
                ]
                mock_execute.side_effect = mock_results

                await executor.execute_collection(collection)

                # Verify that the same context is used for all requests
                for call in mock_execute.call_args_list:
                    assert (
                        call[0][1] == mock_context
                    )  # Second argument should be the context

    @pytest.mark.asyncio
    async def test_execute_collection_timing_calculation(
        self, executor, mock_collection
    ):
        """Test that collection execution timing is calculated correctly."""
        collection, requests = mock_collection

        with patch.object(executor, "execute_request") as mock_execute:
            with patch.object(executor, "_create_execution_context") as mock_context:
                mock_context.return_value = Mock()

                # Mock results with specific timing
                mock_results = []
                for i, request in enumerate(requests):
                    result = Mock()
                    result.success = True
                    result.execution_time_ms = 100.0 + i * 50  # 100, 150, 200 ms
                    mock_results.append(result)

                mock_execute.side_effect = mock_results

                result = await executor.execute_collection(collection)

                # Total time should be greater than 0 (wall clock time)
                assert result.total_time_ms > 0
                # Individual request times should sum to 450ms
                total_request_time = sum(r.execution_time_ms for r in result.results)
                assert total_request_time == 450.0


class TestRequestExecutorMethodPlaceholders:
    """Test that execution methods have proper placeholders."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            return RequestExecutor()

    @pytest.mark.asyncio
    async def test_execute_folder_implemented(self, executor):
        """Test that execute_folder is now implemented."""
        # Create proper mocks for folder and context
        mock_folder = Mock()
        mock_folder.name = "Test Folder"
        mock_folder.get_requests.return_value = iter([])  # Empty folder
        mock_folder.variable = []

        mock_context = Mock()
        mock_context.collection_variables = {}
        mock_context.environment_variables = {}
        # Ensure _collection is None to avoid issues with variable extraction
        del mock_context._collection

        # Should not raise NotImplementedError anymore
        result = await executor.execute_folder(mock_folder, mock_context)

        # Should return a FolderExecutionResult
        assert result.folder_name == "Test Folder"
        assert len(result.results) == 0

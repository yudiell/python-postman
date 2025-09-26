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
        collection.variable = [
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
        collection = Mock()
        del collection.variable  # Remove variable attribute

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
        request.header = [Mock(key="Content-Type", value="application/json")]
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


class TestRequestExecutorMethodPlaceholders:
    """Test that execution methods have proper placeholders."""

    @pytest.fixture
    def executor(self):
        """Create a RequestExecutor for testing."""
        with patch("python_postman.execution.executor.HTTPX_AVAILABLE", True):
            return RequestExecutor()

    def test_execute_request_placeholder(self, executor):
        """Test that execute_request has proper placeholder."""
        with pytest.raises(NotImplementedError, match="task 10"):
            executor.execute_request_sync(Mock(), Mock())

    @pytest.mark.asyncio
    async def test_execute_request_async_placeholder(self, executor):
        """Test that execute_request async has proper placeholder."""
        with pytest.raises(NotImplementedError, match="task 10"):
            await executor.execute_request(Mock(), Mock())

    @pytest.mark.asyncio
    async def test_execute_collection_placeholder(self, executor):
        """Test that execute_collection has proper placeholder."""
        with pytest.raises(NotImplementedError, match="task 12"):
            await executor.execute_collection(Mock())

    @pytest.mark.asyncio
    async def test_execute_folder_placeholder(self, executor):
        """Test that execute_folder has proper placeholder."""
        with pytest.raises(NotImplementedError, match="task 13"):
            await executor.execute_folder(Mock(), Mock())

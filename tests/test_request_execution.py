"""
Tests for Request execution methods.

This module tests the execute() and execute_sync() methods added to the Request class,
ensuring they properly create default executors and contexts when not provided.
"""

import pytest
import sys
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from python_postman.models.request import Request
from python_postman.models.url import Url
from python_postman.models.header import Header


class TestRequestExecution:
    """Test Request execution methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com/users"),
            headers=[Header("Content-Type", "application/json")],
        )

    @pytest.mark.asyncio
    async def test_execute_with_defaults(self):
        """Test async execute method with default executor and context."""
        # Mock the execution module imports
        mock_executor = Mock()
        mock_context = Mock()
        mock_result = Mock()

        mock_executor.execute_request = AsyncMock(return_value=mock_result)

        # Mock the execution module that gets imported inside the method
        mock_execution_module = MagicMock()
        mock_execution_module.RequestExecutor.return_value = mock_executor
        mock_execution_module.ExecutionContext.return_value = mock_context

        with patch.dict(
            "sys.modules", {"python_postman.execution": mock_execution_module}
        ):
            result = await self.request.execute()

            # Verify default executor and context were created
            mock_execution_module.RequestExecutor.assert_called_once_with()
            mock_execution_module.ExecutionContext.assert_called_once_with()

            # Verify execute_request was called with correct parameters
            mock_executor.execute_request.assert_called_once_with(
                request=self.request,
                context=mock_context,
                substitutions=None,
                extensions=None,
            )

            assert result == mock_result

    @pytest.mark.asyncio
    async def test_execute_with_custom_parameters(self):
        """Test async execute method with custom executor, context, and parameters."""
        # Create mock objects
        custom_executor = Mock()
        custom_context = Mock()
        custom_substitutions = {"api_key": "test-key"}
        custom_extensions = Mock()
        mock_result = Mock()

        custom_executor.execute_request = AsyncMock(return_value=mock_result)

        result = await self.request.execute(
            executor=custom_executor,
            context=custom_context,
            substitutions=custom_substitutions,
            extensions=custom_extensions,
        )

        # Verify execute_request was called with custom parameters
        custom_executor.execute_request.assert_called_once_with(
            request=self.request,
            context=custom_context,
            substitutions=custom_substitutions,
            extensions=custom_extensions,
        )

        assert result == mock_result

    @pytest.mark.asyncio
    async def test_execute_import_error(self):
        """Test async execute method when httpx is not available."""
        # Mock the import to raise ImportError
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'httpx'")
        ):
            with pytest.raises(
                ImportError, match="Execution functionality requires httpx"
            ):
                await self.request.execute()

    def test_execute_sync_with_defaults(self):
        """Test sync execute method with default executor and context."""
        # Mock the execution module imports
        mock_executor = Mock()
        mock_context = Mock()
        mock_result = Mock()

        mock_executor.execute_request_sync.return_value = mock_result

        # Mock the execution module that gets imported inside the method
        mock_execution_module = MagicMock()
        mock_execution_module.RequestExecutor.return_value = mock_executor
        mock_execution_module.ExecutionContext.return_value = mock_context

        with patch.dict(
            "sys.modules", {"python_postman.execution": mock_execution_module}
        ):
            result = self.request.execute_sync()

            # Verify default executor and context were created
            mock_execution_module.RequestExecutor.assert_called_once_with()
            mock_execution_module.ExecutionContext.assert_called_once_with()

            # Verify execute_request_sync was called with correct parameters
            mock_executor.execute_request_sync.assert_called_once_with(
                request=self.request,
                context=mock_context,
                substitutions=None,
                extensions=None,
            )

            assert result == mock_result

    def test_execute_sync_with_custom_parameters(self):
        """Test sync execute method with custom executor, context, and parameters."""
        # Create mock objects
        custom_executor = Mock()
        custom_context = Mock()
        custom_substitutions = {"api_key": "test-key"}
        custom_extensions = Mock()
        mock_result = Mock()

        custom_executor.execute_request_sync.return_value = mock_result

        result = self.request.execute_sync(
            executor=custom_executor,
            context=custom_context,
            substitutions=custom_substitutions,
            extensions=custom_extensions,
        )

        # Verify execute_request_sync was called with custom parameters
        custom_executor.execute_request_sync.assert_called_once_with(
            request=self.request,
            context=custom_context,
            substitutions=custom_substitutions,
            extensions=custom_extensions,
        )

        assert result == mock_result

    def test_execute_sync_import_error(self):
        """Test sync execute method when httpx is not available."""
        # Mock the import to raise ImportError
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'httpx'")
        ):
            with pytest.raises(
                ImportError, match="Execution functionality requires httpx"
            ):
                self.request.execute_sync()

    def test_backward_compatibility(self):
        """Test that existing Request functionality is not affected."""
        # Test that all existing methods still work
        assert self.request.name == "Test Request"
        assert self.request.method == "GET"
        assert self.request.url.raw == "https://api.example.com/users"
        assert len(self.request.headers) == 1
        assert self.request.headers[0].key == "Content-Type"

        # Test get_requests method
        requests = list(self.request.get_requests())
        assert len(requests) == 1
        assert requests[0] is self.request

        # Test to_dict method
        request_dict = self.request.to_dict()
        assert request_dict["name"] == "Test Request"
        assert request_dict["request"]["method"] == "GET"

    def test_from_dict_still_works(self):
        """Test that Request.from_dict still works after adding execution methods."""
        request_data = {
            "name": "Test Request",
            "request": {
                "method": "POST",
                "url": "https://api.example.com/users",
                "header": [{"key": "Content-Type", "value": "application/json"}],
            },
        }

        request = Request.from_dict(request_data)
        assert request.name == "Test Request"
        assert request.method == "POST"
        assert request.url.raw == "https://api.example.com/users"
        assert len(request.headers) == 1
        assert request.headers[0].key == "Content-Type"

    @pytest.mark.asyncio
    async def test_execute_with_partial_parameters(self):
        """Test execute method with some custom parameters and some defaults."""
        custom_executor = Mock()
        custom_substitutions = {"var": "value"}
        mock_context = Mock()
        mock_result = Mock()

        custom_executor.execute_request = AsyncMock(return_value=mock_result)

        # Mock the execution module for ExecutionContext only
        mock_execution_module = MagicMock()
        mock_execution_module.ExecutionContext.return_value = mock_context

        with patch.dict(
            "sys.modules", {"python_postman.execution": mock_execution_module}
        ):
            result = await self.request.execute(
                executor=custom_executor,
                substitutions=custom_substitutions,
            )

            # Verify default context was created
            mock_execution_module.ExecutionContext.assert_called_once_with()

            # Verify execute_request was called with mixed parameters
            custom_executor.execute_request.assert_called_once_with(
                request=self.request,
                context=mock_context,
                substitutions=custom_substitutions,
                extensions=None,
            )

            assert result == mock_result

    def test_execute_sync_with_partial_parameters(self):
        """Test execute_sync method with some custom parameters and some defaults."""
        custom_context = Mock()
        custom_extensions = Mock()
        mock_executor = Mock()
        mock_result = Mock()

        mock_executor.execute_request_sync.return_value = mock_result

        # Mock the execution module for RequestExecutor only
        mock_execution_module = MagicMock()
        mock_execution_module.RequestExecutor.return_value = mock_executor

        with patch.dict(
            "sys.modules", {"python_postman.execution": mock_execution_module}
        ):
            result = self.request.execute_sync(
                context=custom_context,
                extensions=custom_extensions,
            )

            # Verify default executor was created
            mock_execution_module.RequestExecutor.assert_called_once_with()

            # Verify execute_request_sync was called with mixed parameters
            mock_executor.execute_request_sync.assert_called_once_with(
                request=self.request,
                context=custom_context,
                substitutions=None,
                extensions=custom_extensions,
            )

            assert result == mock_result

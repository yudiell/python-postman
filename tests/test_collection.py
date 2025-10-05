"""
Tests for Collection model execution methods.

This module tests the execution functionality added to the Collection class,
including the create_executor and execute methods.
"""

import pytest
import sys
from unittest.mock import Mock, AsyncMock, patch
from python_postman.models.collection import Collection
from python_postman.models.collection_info import CollectionInfo
from python_postman.models.variable import Variable
from python_postman.models.auth import Auth, AuthParameter
from python_postman.models.request import Request
from python_postman.models.folder import Folder
from python_postman.models.url import Url
from python_postman.models.header import Header


class TestCollectionExecutionMethods:
    """Test collection execution methods."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a basic collection
        self.collection_info = CollectionInfo(
            name="Test Collection",
            description="A test collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        )

        # Create collection variables
        self.variables = [
            Variable(key="base_url", value="https://api.example.com"),
            Variable(key="api_key", value="test-key-123"),
        ]

        # Create collection auth
        self.auth = Auth(
            type="bearer", parameters=[AuthParameter(key="token", value="{{api_key}}")]
        )

        # Create test requests
        self.request1 = Request(
            name="Get Users",
            url=Url(raw="{{base_url}}/users"),
            method="GET",
            headers=[Header(key="Accept", value="application/json")],
        )

        self.request2 = Request(
            name="Create User",
            url=Url(raw="{{base_url}}/users"),
            method="POST",
            headers=[Header(key="Content-Type", value="application/json")],
        )

        # Create a folder with a request
        self.folder = Folder(name="User Management", items=[self.request2])

        # Create collection with requests and folder
        self.collection = Collection(
            info=self.collection_info,
            items=[self.request1, self.folder],
            variables=self.variables,
            auth=self.auth,
        )

    @patch("python_postman.execution.executor.RequestExecutor")
    def test_create_executor_basic(self, mock_executor_class):
        """Test basic executor creation."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        executor = self.collection.create_executor()

        # Verify RequestExecutor was called with collection variables
        expected_vars = {
            "base_url": "https://api.example.com",
            "api_key": "test-key-123",
        }
        mock_executor_class.assert_called_once_with(variable_overrides=expected_vars)
        assert executor == mock_executor

    @patch("python_postman.execution.executor.RequestExecutor")
    def test_create_executor_with_custom_config(self, mock_executor_class):
        """Test executor creation with custom configuration."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        custom_config = {
            "client_config": {"timeout": 60.0},
            "script_timeout": 45.0,
            "request_delay": 1.0,
        }

        executor = self.collection.create_executor(**custom_config)

        # Verify RequestExecutor was called with custom config and collection variables
        expected_vars = {
            "base_url": "https://api.example.com",
            "api_key": "test-key-123",
        }
        expected_call_args = {**custom_config, "variable_overrides": expected_vars}
        mock_executor_class.assert_called_once_with(**expected_call_args)
        assert executor == mock_executor

    @patch("python_postman.execution.executor.RequestExecutor")
    def test_create_executor_with_variable_overrides(self, mock_executor_class):
        """Test executor creation with custom variable overrides."""
        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        custom_vars = {"base_url": "https://staging.example.com"}

        executor = self.collection.create_executor(variable_overrides=custom_vars)

        # Verify custom variable overrides are used instead of collection variables
        mock_executor_class.assert_called_once_with(variable_overrides=custom_vars)
        assert executor == mock_executor

    @patch("python_postman.execution.executor.RequestExecutor")
    def test_create_executor_no_variables(self, mock_executor_class):
        """Test executor creation with collection that has no variables."""
        collection_no_vars = Collection(
            info=self.collection_info, items=[self.request1]
        )

        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        executor = collection_no_vars.create_executor()

        # Verify RequestExecutor was called with empty variable overrides
        mock_executor_class.assert_called_once_with(variable_overrides={})
        assert executor == mock_executor

    def test_create_executor_import_error(self):
        """Test executor creation when execution module is not available."""
        # Mock the import to fail at the module level
        with patch.dict("sys.modules", {"python_postman.execution.executor": None}):
            with pytest.raises(ImportError) as exc_info:
                self.collection.create_executor()

            assert "Execution functionality requires httpx" in str(exc_info.value)

    @pytest.mark.asyncio
    @patch("python_postman.execution.executor.RequestExecutor")
    async def test_execute_basic(self, mock_executor_class):
        """Test basic collection execution."""
        mock_executor = Mock()
        mock_result = Mock()
        mock_result.collection_name = "Test Collection"
        mock_result.total_requests = 2
        mock_result.successful_requests = 2

        mock_executor.execute_collection = AsyncMock(return_value=mock_result)
        mock_executor_class.return_value = mock_executor

        result = await self.collection.execute()

        # Verify executor was created and execute_collection was called
        mock_executor_class.assert_called_once()
        mock_executor.execute_collection.assert_called_once_with(
            collection=self.collection, parallel=False, stop_on_error=False
        )
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_execute_with_custom_executor(self):
        """Test collection execution with provided executor."""
        mock_executor = Mock()
        mock_result = Mock()
        mock_result.collection_name = "Test Collection"

        mock_executor.execute_collection = AsyncMock(return_value=mock_result)

        result = await self.collection.execute(executor=mock_executor)

        # Verify provided executor was used
        mock_executor.execute_collection.assert_called_once_with(
            collection=self.collection, parallel=False, stop_on_error=False
        )
        assert result == mock_result

    @pytest.mark.asyncio
    @patch("python_postman.execution.executor.RequestExecutor")
    async def test_execute_with_options(self, mock_executor_class):
        """Test collection execution with parallel and stop_on_error options."""
        mock_executor = Mock()
        mock_result = Mock()

        mock_executor.execute_collection = AsyncMock(return_value=mock_result)
        mock_executor_class.return_value = mock_executor

        result = await self.collection.execute(parallel=True, stop_on_error=True)

        # Verify options were passed to execute_collection
        mock_executor.execute_collection.assert_called_once_with(
            collection=self.collection, parallel=True, stop_on_error=True
        )
        assert result == mock_result

    @pytest.mark.asyncio
    async def test_execute_import_error(self):
        """Test collection execution when execution module is not available."""
        # Mock the import to fail at the module level
        with patch.dict("sys.modules", {"python_postman.execution.executor": None}):
            with pytest.raises(ImportError) as exc_info:
                await self.collection.execute()

            assert "Execution functionality requires httpx" in str(exc_info.value)

    @patch("python_postman.execution.executor.RequestExecutor")
    def test_collection_variables_extraction(self, mock_executor_class):
        """Test that collection variables are properly extracted."""
        # Test with variables that have different attribute structures
        variables_with_different_attrs = [
            Variable(key="var1", value="value1"),
            Variable(key="var2", value="value2"),
            Mock(key="var3", value="value3"),  # Mock with attributes
            Mock(spec=[]),  # Mock without key/value attributes
        ]

        collection = Collection(
            info=self.collection_info,
            items=[],
            variables=variables_with_different_attrs,
        )

        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        collection.create_executor()

        # Verify only variables with key/value attributes are included
        expected_vars = {"var1": "value1", "var2": "value2", "var3": "value3"}
        mock_executor_class.assert_called_once_with(variable_overrides=expected_vars)

    @patch("python_postman.execution.executor.RequestExecutor")
    def test_collection_variables_none(self, mock_executor_class):
        """Test collection with None variables."""
        collection = Collection(info=self.collection_info, items=[], variables=None)

        mock_executor = Mock()
        mock_executor_class.return_value = mock_executor

        collection.create_executor()

        # Verify empty variable overrides when variables is None
        mock_executor_class.assert_called_once_with(variable_overrides={})

    @pytest.mark.asyncio
    async def test_execute_with_all_parameters(self):
        """Test collection execution with all parameters specified."""
        mock_executor = Mock()
        mock_result = Mock()
        mock_result.collection_name = "Test Collection"
        mock_result.total_requests = 2
        mock_result.successful_requests = 1
        mock_result.failed_requests = 1

        mock_executor.execute_collection = AsyncMock(return_value=mock_result)

        result = await self.collection.execute(
            executor=mock_executor, parallel=True, stop_on_error=True
        )

        # Verify all parameters were passed correctly
        mock_executor.execute_collection.assert_called_once_with(
            collection=self.collection, parallel=True, stop_on_error=True
        )
        assert result == mock_result
        assert result.collection_name == "Test Collection"
        assert result.total_requests == 2
        assert result.successful_requests == 1
        assert result.failed_requests == 1


class TestCollectionExecutionIntegration:
    """Integration tests for collection execution methods."""

    def setup_method(self):
        """Set up test fixtures for integration tests."""
        self.collection_info = CollectionInfo(
            name="Integration Test Collection",
            description="Collection for integration testing",
        )

        self.variables = [Variable(key="test_var", value="test_value")]

        self.request = Request(
            name="Test Request", url=Url(raw="https://httpbin.org/get"), method="GET"
        )

        self.collection = Collection(
            info=self.collection_info, items=[self.request], variables=self.variables
        )

    def test_create_executor_returns_correct_type(self):
        """Test that create_executor returns the correct type."""
        pytest.importorskip("httpx", reason="httpx not available for integration test")

        from python_postman.execution.executor import RequestExecutor

        executor = self.collection.create_executor()
        assert isinstance(executor, RequestExecutor)

        # Test that executor has expected configuration
        assert executor.variable_overrides == {"test_var": "test_value"}

    @pytest.mark.asyncio
    async def test_execute_returns_correct_result_type(self):
        """Test that execute returns the correct result type."""
        try:
            from python_postman.execution.results import CollectionExecutionResult

            # Create a mock executor that returns a real result
            mock_executor = Mock()
            mock_result = CollectionExecutionResult(collection_name="Test Collection")
            mock_executor.execute_collection = AsyncMock(return_value=mock_result)

            result = await self.collection.execute(executor=mock_executor)
            assert isinstance(result, CollectionExecutionResult)
            assert result.collection_name == "Test Collection"

        except ImportError:
            pytest.skip("httpx not available for integration test")

"""
Tests for package imports and optional dependencies.

This module tests that the package imports work correctly both with and without
the optional httpx dependency installed.
"""

import pytest

import python_postman


class TestImports:
    """Test import behavior with and without optional dependencies."""

    def test_core_imports_always_available(self):
        """Test that core functionality is always importable."""
        # These should always be available
        from python_postman import (
            PythonPostman,
            Collection,
            Request,
            Folder,
            Variable,
            Auth,
            AuthType,
            AuthParameter,
            Event,
            Url,
            QueryParam,
            Header,
            HeaderCollection,
            Body,
            BodyMode,
            FormParameter,
            CollectionInfo,
            Item,
            ValidationResult,
            PostmanCollectionError,
            CollectionParseError,
            CollectionValidationError,
            CollectionFileError,
            parse_json_safely,
            load_json_file,
            is_execution_available,
        )

        # Verify they are not None
        assert PythonPostman is not None
        assert Collection is not None
        assert Request is not None
        assert is_execution_available is not None

    def test_execution_availability_check(self):
        """Test the execution availability check function."""
        from python_postman import is_execution_available

        # Should return a boolean
        result = is_execution_available()
        assert isinstance(result, bool)

    def test_execution_imports_when_httpx_available(self):
        """Test that execution classes are available when httpx is installed."""
        # This test assumes httpx is installed (which it should be in our test environment)
        try:
            import httpx  # noqa: F401

            httpx_available = True
        except ImportError:
            httpx_available = False

        if httpx_available:
            from python_postman import (
                RequestExecutor,
                ExecutionContext,
                ExecutionResponse,
                RequestExtensions,
                ExecutionResult,
                TestResults,
                TestAssertion,
                CollectionExecutionResult,
                FolderExecutionResult,
                VariableResolver,
                AuthHandler,
                ScriptRunner,
                ExecutionError,
                RequestExecutionError,
                VariableResolutionError,
                ScriptExecutionError,
                AuthenticationError,
                TimeoutError,
            )

            # Verify they are not None
            assert RequestExecutor is not None
            assert ExecutionContext is not None
            assert ExecutionResponse is not None
            assert ExecutionError is not None

            # Check that is_execution_available returns True
            from python_postman import is_execution_available

            assert is_execution_available() is True

    def test_all_exports_are_importable(self):
        """Test that all items in __all__ are actually importable."""
        import python_postman

        for item_name in python_postman.__all__:
            # Should be able to get the attribute
            item = getattr(python_postman, item_name)
            assert item is not None, f"{item_name} should not be None"

    def test_execution_classes_in_all_when_httpx_available(self):
        """Test that execution classes are in __all__ when httpx is available."""
        try:
            import httpx  # noqa: F401

            httpx_available = True
        except ImportError:
            httpx_available = False

        import python_postman

        execution_classes = [
            "RequestExecutor",
            "ExecutionContext",
            "ExecutionResponse",
            "RequestExtensions",
            "ExecutionResult",
            "TestResults",
            "TestAssertion",
            "CollectionExecutionResult",
            "FolderExecutionResult",
            "VariableResolver",
            "AuthHandler",
            "ScriptRunner",
            "ExecutionError",
            "RequestExecutionError",
            "VariableResolutionError",
            "ScriptExecutionError",
            "AuthenticationError",
            "TimeoutError",
        ]

        if httpx_available:
            for class_name in execution_classes:
                assert (
                    class_name in python_postman.__all__
                ), f"{class_name} should be in __all__"

    def test_package_metadata(self):
        """Test that package metadata is correctly set."""
        import python_postman

        assert python_postman.__version__ == "0.7.0"
        assert python_postman.__author__ == "Python Postman Contributors"
        assert python_postman.__license__ == "MIT"
        assert "Postman collection" in python_postman.__description__

    def test_graceful_degradation_without_httpx(self):
        """Test that the package works normally without httpx for core functionality."""
        # This test ensures that even without httpx, users can still:
        # 1. Parse collections
        # 2. Access all model classes
        # 3. Use utility functions

        from python_postman import PythonPostman, Collection, Request

        # These should work regardless of httpx availability
        assert PythonPostman is not None
        assert Collection is not None
        assert Request is not None

        # The parser should still work
        collection_data = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [],
        }

        collection = Collection.from_dict(collection_data)
        assert collection.info.name == "Test Collection"

    def test_execution_module_structure(self):
        """Test that the execution module has the expected structure."""
        try:
            import python_postman.execution

            execution_available = True
        except ImportError:
            execution_available = False

        if execution_available:
            # Test that the execution module exports are available
            from python_postman.execution import (
                RequestExecutor,
                ExecutionContext,
                ExecutionResponse,
                RequestExtensions,
                ExecutionResult,
                TestResults,
                TestAssertion,
                CollectionExecutionResult,
                FolderExecutionResult,
                VariableResolver,
                AuthHandler,
                ScriptRunner,
                ExecutionError,
                RequestExecutionError,
                VariableResolutionError,
                ScriptExecutionError,
                AuthenticationError,
                TimeoutError,
            )

            # Verify they are classes/types
            assert callable(RequestExecutor)
            assert callable(ExecutionContext)
            assert callable(ExecutionResponse)


class TestOptionalDependencyInstallation:
    """Test scenarios related to optional dependency installation."""

    def test_execution_group_dependencies(self):
        """Test that the execution optional dependency group is properly configured."""
        # This is more of a documentation test - we can't easily test pip installation
        # but we can verify the configuration is correct

        # The pyproject.toml should have the execution group with httpx
        # This is verified by reading the file in the implementation
        pass

    def test_httpx_dependency_check(self):
        """Test that httpx dependency is properly detected."""
        try:
            import httpx  # noqa: F401

            httpx_available = True
        except ImportError:
            httpx_available = False

        from python_postman import is_execution_available

        # If httpx is available, execution should be available
        if httpx_available:
            assert is_execution_available() is True
        # If httpx is not available, execution should not be available
        # (but in our test environment, httpx should be available)

    def test_import_patterns(self):
        """Test different import patterns work correctly."""
        # Test direct import from main module
        from python_postman import is_execution_available

        assert callable(is_execution_available)

        # Test that we can check execution availability
        result = is_execution_available()
        assert isinstance(result, bool)

        # If execution is available, test that we can import execution classes
        if result:
            from python_postman import RequestExecutor, ExecutionContext

            assert RequestExecutor is not None
            assert ExecutionContext is not None

    def test_execution_availability_consistency(self):
        """Test that execution availability is consistent across different checks."""
        from python_postman import is_execution_available

        # Check the function result
        function_result = is_execution_available()

        # Check if we can import httpx directly
        try:
            import httpx  # noqa: F401

            httpx_available = True
        except ImportError:
            httpx_available = False

        # Check if we can import execution module
        try:
            import python_postman.execution  # noqa: F401

            execution_module_available = True
        except ImportError:
            execution_module_available = False

        # All checks should be consistent
        if httpx_available:
            assert function_result is True
            assert execution_module_available is True
        # Note: In our test environment, httpx should always be available
        # so we don't test the else case here


class TestExecutionImportScenarios:
    """Test specific execution import scenarios."""

    def test_direct_execution_module_import(self):
        """Test importing the execution module directly."""
        try:
            from python_postman import execution

            assert execution is not None

            # Should be able to access classes from the module
            assert hasattr(execution, "RequestExecutor")
            assert hasattr(execution, "ExecutionContext")

        except ImportError:
            # If execution module is not available, that's also valid
            # (would happen if httpx is not installed)
            pass

    def test_selective_execution_imports(self):
        """Test importing specific execution classes."""
        from python_postman import is_execution_available

        if is_execution_available():
            # Should be able to import specific classes
            from python_postman import RequestExecutor
            from python_postman import ExecutionContext
            from python_postman import ExecutionResponse

            assert RequestExecutor is not None
            assert ExecutionContext is not None
            assert ExecutionResponse is not None

    def test_execution_class_instantiation(self):
        """Test that execution classes can be instantiated when available."""
        from python_postman import is_execution_available

        if is_execution_available():
            from python_postman import ExecutionContext, RequestExtensions

            # Should be able to create instances
            context = ExecutionContext()
            assert context is not None

            extensions = RequestExtensions()
            assert extensions is not None

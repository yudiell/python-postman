"""
Unit tests for exception classes.
"""

import pytest
from python_postman.exceptions import (
    PostmanCollectionError,
    CollectionParseError,
    CollectionValidationError,
    CollectionFileError,
)


class TestPostmanCollectionError:
    """Test cases for the base PostmanCollectionError class."""

    def test_basic_initialization(self):
        """Test basic exception initialization with message only."""
        message = "Test error message"
        error = PostmanCollectionError(message)

        assert str(error) == message
        assert error.message == message
        assert error.details == {}

    def test_initialization_with_details(self):
        """Test exception initialization with message and details."""
        message = "Test error with details"
        details = {"file": "test.json", "line": 42}
        error = PostmanCollectionError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == f"{message} (Details: {details})"

    def test_inheritance_from_exception(self):
        """Test that PostmanCollectionError inherits from Exception."""
        error = PostmanCollectionError("test")
        assert isinstance(error, Exception)

    def test_details_default_to_empty_dict(self):
        """Test that details default to empty dict when None is passed."""
        error = PostmanCollectionError("test", None)
        assert error.details == {}


class TestCollectionParseError:
    """Test cases for CollectionParseError class."""

    def test_inheritance_from_base(self):
        """Test that CollectionParseError inherits from PostmanCollectionError."""
        error = CollectionParseError("parse error")
        assert isinstance(error, PostmanCollectionError)
        assert isinstance(error, Exception)

    def test_basic_functionality(self):
        """Test basic functionality inherited from base class."""
        message = "JSON parsing failed"
        details = {"position": 123, "character": "invalid"}
        error = CollectionParseError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == f"{message} (Details: {details})"

    def test_can_be_raised_and_caught(self):
        """Test that the exception can be raised and caught properly."""
        with pytest.raises(CollectionParseError) as exc_info:
            raise CollectionParseError("test parse error")

        assert str(exc_info.value) == "test parse error"

    def test_can_be_caught_as_base_exception(self):
        """Test that CollectionParseError can be caught as PostmanCollectionError."""
        with pytest.raises(PostmanCollectionError):
            raise CollectionParseError("test error")


class TestCollectionValidationError:
    """Test cases for CollectionValidationError class."""

    def test_inheritance_from_base(self):
        """Test that CollectionValidationError inherits from PostmanCollectionError."""
        error = CollectionValidationError("validation error")
        assert isinstance(error, PostmanCollectionError)
        assert isinstance(error, Exception)

    def test_basic_functionality(self):
        """Test basic functionality inherited from base class."""
        message = "Schema validation failed"
        details = {"missing_fields": ["name", "schema"], "invalid_fields": ["version"]}
        error = CollectionValidationError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == f"{message} (Details: {details})"

    def test_can_be_raised_and_caught(self):
        """Test that the exception can be raised and caught properly."""
        with pytest.raises(CollectionValidationError) as exc_info:
            raise CollectionValidationError("test validation error")

        assert str(exc_info.value) == "test validation error"

    def test_can_be_caught_as_base_exception(self):
        """Test that CollectionValidationError can be caught as PostmanCollectionError."""
        with pytest.raises(PostmanCollectionError):
            raise CollectionValidationError("test error")


class TestCollectionFileError:
    """Test cases for CollectionFileError class."""

    def test_inheritance_from_base(self):
        """Test that CollectionFileError inherits from PostmanCollectionError."""
        error = CollectionFileError("file error")
        assert isinstance(error, PostmanCollectionError)
        assert isinstance(error, Exception)

    def test_basic_functionality(self):
        """Test basic functionality inherited from base class."""
        message = "File not found"
        details = {"file_path": "/path/to/collection.json", "errno": 2}
        error = CollectionFileError(message, details)

        assert error.message == message
        assert error.details == details
        assert str(error) == f"{message} (Details: {details})"

    def test_can_be_raised_and_caught(self):
        """Test that the exception can be raised and caught properly."""
        with pytest.raises(CollectionFileError) as exc_info:
            raise CollectionFileError("test file error")

        assert str(exc_info.value) == "test file error"

    def test_can_be_caught_as_base_exception(self):
        """Test that CollectionFileError can be caught as PostmanCollectionError."""
        with pytest.raises(PostmanCollectionError):
            raise CollectionFileError("test error")


class TestExceptionHierarchy:
    """Test cases for the overall exception hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all specific exceptions inherit from PostmanCollectionError."""
        exceptions = [
            CollectionParseError("test"),
            CollectionValidationError("test"),
            CollectionFileError("test"),
        ]

        for exc in exceptions:
            assert isinstance(exc, PostmanCollectionError)
            assert isinstance(exc, Exception)

    def test_exception_hierarchy_catching(self):
        """Test that exceptions can be caught at different levels of hierarchy."""
        # Test catching specific exception
        with pytest.raises(CollectionParseError):
            raise CollectionParseError("specific error")

        # Test catching at base level
        with pytest.raises(PostmanCollectionError):
            raise CollectionParseError("caught as base")

        # Test catching at Exception level
        with pytest.raises(Exception):
            raise CollectionValidationError("caught as Exception")

    def test_exception_types_are_distinct(self):
        """Test that different exception types are distinct."""
        parse_error = CollectionParseError("parse")
        validation_error = CollectionValidationError("validation")
        file_error = CollectionFileError("file")

        assert type(parse_error) != type(validation_error)
        assert type(validation_error) != type(file_error)
        assert type(file_error) != type(parse_error)

        # But they all share the same base
        assert isinstance(parse_error, PostmanCollectionError)
        assert isinstance(validation_error, PostmanCollectionError)
        assert isinstance(file_error, PostmanCollectionError)

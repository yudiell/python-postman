"""
Tests for schema version detection and validation.
"""

import pytest
from python_postman.models.schema import SchemaVersion, SchemaValidator
from python_postman.models.collection import Collection
from python_postman.models.collection_info import CollectionInfo
from python_postman.exceptions import SchemaVersionError


class TestSchemaVersion:
    """Test SchemaVersion enum."""

    def test_schema_version_values(self):
        """Test that SchemaVersion enum has correct values."""
        assert SchemaVersion.V2_0_0.value == "v2.0.0"
        assert SchemaVersion.V2_1_0.value == "v2.1.0"
        assert SchemaVersion.UNKNOWN.value == "unknown"

    def test_schema_version_string_representation(self):
        """Test string representation of SchemaVersion."""
        assert str(SchemaVersion.V2_0_0) == "v2.0.0"
        assert str(SchemaVersion.V2_1_0) == "v2.1.0"
        assert str(SchemaVersion.UNKNOWN) == "unknown"


class TestSchemaValidator:
    """Test SchemaValidator class."""

    def test_detect_version_v2_0_0(self):
        """Test detection of v2.0.0 schema."""
        schema_url = "https://schema.getpostman.com/json/collection/v2.0.0/collection.json"
        version = SchemaValidator.detect_version(schema_url)
        assert version == SchemaVersion.V2_0_0

    def test_detect_version_v2_1_0(self):
        """Test detection of v2.1.0 schema."""
        schema_url = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        version = SchemaValidator.detect_version(schema_url)
        assert version == SchemaVersion.V2_1_0

    def test_detect_version_unknown(self):
        """Test detection of unknown schema."""
        schema_url = "https://schema.getpostman.com/json/collection/v3.0.0/collection.json"
        version = SchemaValidator.detect_version(schema_url)
        assert version == SchemaVersion.UNKNOWN

    def test_detect_version_none(self):
        """Test detection with None schema URL."""
        version = SchemaValidator.detect_version(None)
        assert version == SchemaVersion.UNKNOWN

    def test_detect_version_empty_string(self):
        """Test detection with empty string."""
        version = SchemaValidator.detect_version("")
        assert version == SchemaVersion.UNKNOWN

    def test_detect_version_case_insensitive_v2_1_0(self):
        """Test case-insensitive detection for v2.1.0."""
        schema_url = "https://SCHEMA.GETPOSTMAN.COM/json/collection/V2.1.0/collection.json"
        version = SchemaValidator.detect_version(schema_url)
        assert version == SchemaVersion.V2_1_0

    def test_detect_version_case_insensitive_v2_0_0(self):
        """Test case-insensitive detection for v2.0.0."""
        schema_url = "https://SCHEMA.GETPOSTMAN.COM/json/collection/V2.0.0/collection.json"
        version = SchemaValidator.detect_version(schema_url)
        assert version == SchemaVersion.V2_0_0

    def test_detect_version_with_underscores(self):
        """Test detection with underscores instead of dots."""
        # Test v2_1_0 pattern
        schema_url = "https://schema.getpostman.com/json/collection/v2_1_0/collection.json"
        version = SchemaValidator.detect_version(schema_url)
        assert version == SchemaVersion.V2_1_0

        # Test v2_0_0 pattern
        schema_url = "https://schema.getpostman.com/json/collection/v2_0_0/collection.json"
        version = SchemaValidator.detect_version(schema_url)
        assert version == SchemaVersion.V2_0_0

    def test_validate_version_v2_0_0_success(self):
        """Test successful validation of v2.0.0 schema."""
        schema_url = "https://schema.getpostman.com/json/collection/v2.0.0/collection.json"
        is_valid, error = SchemaValidator.validate_version(schema_url)
        assert is_valid is True
        assert error is None

    def test_validate_version_v2_1_0_success(self):
        """Test successful validation of v2.1.0 schema."""
        schema_url = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        is_valid, error = SchemaValidator.validate_version(schema_url)
        assert is_valid is True
        assert error is None

    def test_validate_version_unsupported(self):
        """Test validation of unsupported schema version."""
        schema_url = "https://schema.getpostman.com/json/collection/v3.0.0/collection.json"
        is_valid, error = SchemaValidator.validate_version(schema_url)
        assert is_valid is False
        assert error is not None
        assert "Unsupported schema version" in error
        assert "v2.0.0, v2.1.0" in error

    def test_validate_version_none(self):
        """Test validation with None schema URL."""
        is_valid, error = SchemaValidator.validate_version(None)
        assert is_valid is False
        assert error is not None
        assert "No schema version specified" in error
        assert "v2.0.0, v2.1.0" in error

    def test_validate_version_empty_string(self):
        """Test validation with empty string."""
        is_valid, error = SchemaValidator.validate_version("")
        assert is_valid is False
        assert error is not None
        assert "No schema version specified" in error

    def test_validate_version_invalid_url(self):
        """Test validation with invalid URL."""
        schema_url = "not-a-valid-schema-url"
        is_valid, error = SchemaValidator.validate_version(schema_url)
        assert is_valid is False
        assert error is not None
        assert "Unsupported schema version" in error
        assert schema_url in error

    def test_get_supported_versions(self):
        """Test getting list of supported versions."""
        versions = SchemaValidator.get_supported_versions()
        assert len(versions) == 2
        assert SchemaVersion.V2_0_0 in versions
        assert SchemaVersion.V2_1_0 in versions
        assert SchemaVersion.UNKNOWN not in versions

    def test_is_supported_v2_0_0(self):
        """Test is_supported for v2.0.0."""
        schema_url = "https://schema.getpostman.com/json/collection/v2.0.0/collection.json"
        assert SchemaValidator.is_supported(schema_url) is True

    def test_is_supported_v2_1_0(self):
        """Test is_supported for v2.1.0."""
        schema_url = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        assert SchemaValidator.is_supported(schema_url) is True

    def test_is_supported_unsupported(self):
        """Test is_supported for unsupported version."""
        schema_url = "https://schema.getpostman.com/json/collection/v3.0.0/collection.json"
        assert SchemaValidator.is_supported(schema_url) is False

    def test_is_supported_none(self):
        """Test is_supported with None."""
        assert SchemaValidator.is_supported(None) is False


class TestCollectionSchemaIntegration:
    """Test schema version integration with Collection class."""

    def test_collection_schema_version_v2_1_0(self):
        """Test that Collection detects v2.1.0 schema version."""
        info = CollectionInfo(
            name="Test Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        collection = Collection(info=info)
        assert collection.schema_version == SchemaVersion.V2_1_0

    def test_collection_schema_version_v2_0_0(self):
        """Test that Collection detects v2.0.0 schema version."""
        info = CollectionInfo(
            name="Test Collection",
            schema="https://schema.getpostman.com/json/collection/v2.0.0/collection.json"
        )
        collection = Collection(info=info)
        assert collection.schema_version == SchemaVersion.V2_0_0

    def test_collection_schema_version_unknown(self):
        """Test that Collection detects unknown schema version."""
        info = CollectionInfo(
            name="Test Collection",
            schema="https://schema.getpostman.com/json/collection/v3.0.0/collection.json"
        )
        collection = Collection(info=info)
        assert collection.schema_version == SchemaVersion.UNKNOWN

    def test_collection_schema_version_none(self):
        """Test that Collection handles None schema."""
        info = CollectionInfo(name="Test Collection", schema=None)
        collection = Collection(info=info)
        assert collection.schema_version == SchemaVersion.UNKNOWN

    def test_collection_validate_supported_schema(self):
        """Test that Collection.validate() accepts supported schema."""
        info = CollectionInfo(
            name="Test Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        collection = Collection(info=info)
        result = collection.validate()
        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_collection_validate_unsupported_schema(self):
        """Test that Collection.validate() rejects unsupported schema."""
        info = CollectionInfo(
            name="Test Collection",
            schema="https://schema.getpostman.com/json/collection/v3.0.0/collection.json"
        )
        collection = Collection(info=info)
        result = collection.validate()
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("Unsupported schema version" in error for error in result.errors)

    def test_collection_validate_no_schema(self):
        """Test that Collection.validate() handles missing schema."""
        info = CollectionInfo(name="Test Collection", schema=None)
        collection = Collection(info=info)
        result = collection.validate()
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("No schema version specified" in error for error in result.errors)

    def test_collection_from_dict_with_schema(self):
        """Test Collection.from_dict() with schema version."""
        data = {
            "info": {
                "name": "Test Collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            },
            "item": []
        }
        collection = Collection.from_dict(data)
        assert collection.schema_version == SchemaVersion.V2_1_0
        assert collection.info.schema == "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"

    def test_collection_to_dict_preserves_schema(self):
        """Test that Collection.to_dict() preserves schema."""
        info = CollectionInfo(
            name="Test Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        collection = Collection(info=info)
        data = collection.to_dict()
        assert data["info"]["schema"] == "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"


class TestSchemaVersionError:
    """Test SchemaVersionError exception."""

    def test_schema_version_error_basic(self):
        """Test basic SchemaVersionError creation."""
        error = SchemaVersionError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.schema_url is None
        assert error.supported_versions is None

    def test_schema_version_error_with_schema_url(self):
        """Test SchemaVersionError with schema URL."""
        schema_url = "https://schema.getpostman.com/json/collection/v3.0.0/collection.json"
        error = SchemaVersionError("Unsupported version", schema_url=schema_url)
        assert error.schema_url == schema_url
        assert "schema_url" in error.details

    def test_schema_version_error_with_supported_versions(self):
        """Test SchemaVersionError with supported versions."""
        supported = ["v2.0.0", "v2.1.0"]
        error = SchemaVersionError("Unsupported version", supported_versions=supported)
        assert error.supported_versions == supported
        assert "supported_versions" in error.details

    def test_schema_version_error_with_all_details(self):
        """Test SchemaVersionError with all details."""
        schema_url = "https://schema.getpostman.com/json/collection/v3.0.0/collection.json"
        supported = ["v2.0.0", "v2.1.0"]
        error = SchemaVersionError(
            "Unsupported version",
            schema_url=schema_url,
            supported_versions=supported
        )
        assert error.schema_url == schema_url
        assert error.supported_versions == supported
        assert "schema_url" in error.details
        assert "supported_versions" in error.details
        assert "schema_url" in str(error)
        assert "supported_versions" in str(error)

"""
Tests for PythonPostman parser and factory methods.
"""

import json
import pytest
import tempfile
import os
from pathlib import Path

from python_postman.parser import PythonPostman
from python_postman.models.collection import Collection
from python_postman.exceptions import (
    CollectionParseError,
    CollectionFileError,
    CollectionValidationError,
)


class TestPythonPostmanFactoryMethods:
    """Test cases for PythonPostman factory methods."""

    def test_from_dict_valid_collection(self):
        """Test creating collection from valid dictionary."""
        collection_data = {
            "info": {
                "name": "Test Collection",
                "description": "A test collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": [
                {
                    "name": "Test Request",
                    "request": {
                        "method": "GET",
                        "url": {
                            "raw": "https://api.example.com/test",
                            "protocol": "https",
                            "host": ["api", "example", "com"],
                            "path": ["test"],
                        },
                    },
                }
            ],
        }

        collection = PythonPostman.from_dict(collection_data)

        assert isinstance(collection, Collection)
        assert collection.info.name == "Test Collection"
        assert len(collection.items) == 1
        assert collection.items[0].name == "Test Request"

    def test_from_dict_minimal_collection(self):
        """Test creating collection from minimal valid dictionary."""
        collection_data = {"info": {"name": "Minimal Collection"}}

        collection = PythonPostman.from_dict(collection_data)

        assert isinstance(collection, Collection)
        assert collection.info.name == "Minimal Collection"
        assert len(collection.items) == 0

    def test_from_dict_with_variables_and_auth(self):
        """Test creating collection with variables and authentication."""
        collection_data = {
            "info": {
                "name": "Collection with Auth",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "variable": [
                {"key": "baseUrl", "value": "https://api.example.com", "type": "string"}
            ],
            "auth": {
                "type": "bearer",
                "bearer": [
                    {"key": "token", "value": "{{authToken}}", "type": "string"}
                ],
            },
        }

        collection = PythonPostman.from_dict(collection_data)

        assert collection.info.name == "Collection with Auth"
        assert len(collection.variables) == 1
        assert collection.variables[0].key == "baseUrl"
        assert collection.auth is not None
        assert collection.auth.type == "bearer"

    def test_from_dict_with_folders(self):
        """Test creating collection with nested folders."""
        collection_data = {
            "info": {"name": "Collection with Folders"},
            "item": [
                {
                    "name": "API Folder",
                    "item": [
                        {
                            "name": "Get Users",
                            "request": {
                                "method": "GET",
                                "url": "https://api.example.com/users",
                            },
                        }
                    ],
                }
            ],
        }

        collection = PythonPostman.from_dict(collection_data)

        assert len(collection.items) == 1
        assert collection.items[0].name == "API Folder"
        # The folder should contain one request
        requests = list(collection.get_all_requests())
        assert len(requests) == 1
        assert requests[0].name == "Get Users"

    def test_from_dict_invalid_structure(self):
        """Test handling of invalid collection structure."""
        invalid_data = {"info": "not an object"}  # Should be an object

        with pytest.raises(CollectionValidationError) as exc_info:
            PythonPostman.from_dict(invalid_data)

        error = exc_info.value
        assert "Failed to create collection from data" in str(error)

    def test_from_dict_missing_required_fields(self):
        """Test handling of missing required fields."""
        invalid_data = {
            # Missing 'info' field
            "item": []
        }

        with pytest.raises(CollectionValidationError):
            PythonPostman.from_dict(invalid_data)

    def test_from_dict_validation_failure(self):
        """Test handling when collection validation fails."""
        # Create data that will create a collection but fail validation
        invalid_data = {"info": {"name": ""}}  # Empty name should fail validation

        with pytest.raises(CollectionValidationError) as exc_info:
            PythonPostman.from_dict(invalid_data)

        error = exc_info.value
        assert "Collection validation failed" in str(error)
        assert "validation_errors" in error.details

    def test_from_json_valid_string(self):
        """Test creating collection from valid JSON string."""
        collection_json = """
        {
            "info": {
                "name": "JSON Test Collection",
                "description": "Created from JSON string"
            },
            "item": []
        }
        """

        collection = PythonPostman.from_json(collection_json)

        assert isinstance(collection, Collection)
        assert collection.info.name == "JSON Test Collection"
        assert collection.info.description == "Created from JSON string"

    def test_from_json_invalid_json(self):
        """Test handling of invalid JSON string."""
        invalid_json = '{"info": {"name": "test", invalid: }}'

        with pytest.raises(CollectionParseError):
            PythonPostman.from_json(invalid_json)

    def test_from_json_empty_string(self):
        """Test handling of empty JSON string."""
        with pytest.raises(CollectionParseError):
            PythonPostman.from_json("")

    def test_from_json_non_object(self):
        """Test handling when JSON is not an object."""
        json_array = '["not", "an", "object"]'

        with pytest.raises(CollectionParseError):
            PythonPostman.from_json(json_array)

    def test_from_file_valid_collection(self):
        """Test loading collection from valid file."""
        collection_data = {
            "info": {"name": "File Test Collection", "description": "Loaded from file"},
            "item": [
                {
                    "name": "File Request",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/data",
                    },
                }
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(collection_data, f)
            temp_path = f.name

        try:
            collection = PythonPostman.from_file(temp_path)

            assert isinstance(collection, Collection)
            assert collection.info.name == "File Test Collection"
            assert len(collection.items) == 1
        finally:
            os.unlink(temp_path)

    def test_from_file_with_path_object(self):
        """Test loading collection using Path object."""
        collection_data = {"info": {"name": "Path Test Collection"}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(collection_data, f)
            temp_path = Path(f.name)

        try:
            collection = PythonPostman.from_file(temp_path)
            assert collection.info.name == "Path Test Collection"
        finally:
            temp_path.unlink()

    def test_from_file_nonexistent(self):
        """Test handling of nonexistent file."""
        with pytest.raises(CollectionFileError):
            PythonPostman.from_file("/path/that/does/not/exist.json")

    def test_from_file_invalid_json(self):
        """Test handling of file with invalid JSON."""
        invalid_json = '{"info": {"name": "test", invalid: }}'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(invalid_json)
            temp_path = f.name

        try:
            with pytest.raises(CollectionParseError):
                PythonPostman.from_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_create_collection(self):
        """Test creating a new empty collection."""
        collection = PythonPostman.create_collection(
            name="New Collection", description="A brand new collection"
        )

        assert isinstance(collection, Collection)
        assert collection.info.name == "New Collection"
        assert collection.info.description == "A brand new collection"
        assert len(collection.items) == 0
        assert len(collection.variables) == 0

    def test_create_collection_minimal(self):
        """Test creating collection with minimal parameters."""
        collection = PythonPostman.create_collection("Minimal Collection")

        assert collection.info.name == "Minimal Collection"
        assert collection.info.description == ""
        assert "v2.1.0" in collection.info.schema

    def test_create_collection_custom_schema(self):
        """Test creating collection with custom schema."""
        custom_schema = (
            "https://schema.getpostman.com/json/collection/v2.0.0/collection.json"
        )
        collection = PythonPostman.create_collection(
            "Custom Schema Collection", schema=custom_schema
        )

        assert collection.info.schema == custom_schema

    def test_validate_collection_dict_valid(self):
        """Test validation of valid collection dictionary."""
        valid_data = {"info": {"name": "Valid Collection"}}

        is_valid = PythonPostman.validate_collection_dict(valid_data)
        assert is_valid is True

    def test_validate_collection_dict_invalid(self):
        """Test validation of invalid collection dictionary."""
        invalid_data = {"info": "not an object"}

        is_valid = PythonPostman.validate_collection_dict(invalid_data)
        assert is_valid is False

    def test_validate_collection_dict_missing_info(self):
        """Test validation when info is missing."""
        invalid_data = {"item": []}

        is_valid = PythonPostman.validate_collection_dict(invalid_data)
        assert is_valid is False

    def test_complex_collection_end_to_end(self):
        """Test end-to-end parsing of complex collection."""
        complex_collection = {
            "info": {
                "name": "Complex API Collection",
                "description": "A comprehensive API test collection",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "variable": [
                {
                    "key": "baseUrl",
                    "value": "https://api.example.com",
                    "type": "string",
                },
                {"key": "apiKey", "value": "secret-key", "type": "string"},
            ],
            "auth": {
                "type": "apikey",
                "apikey": [
                    {"key": "key", "value": "X-API-Key", "type": "string"},
                    {"key": "value", "value": "{{apiKey}}", "type": "string"},
                ],
            },
            "event": [
                {
                    "listen": "prerequest",
                    "script": {
                        "type": "text/javascript",
                        "exec": ["console.log('Pre-request script');"],
                    },
                }
            ],
            "item": [
                {
                    "name": "Users API",
                    "item": [
                        {
                            "name": "Get All Users",
                            "request": {
                                "method": "GET",
                                "url": {
                                    "raw": "{{baseUrl}}/users",
                                    "host": ["{{baseUrl}}"],
                                    "path": ["users"],
                                },
                            },
                        },
                        {
                            "name": "Create User",
                            "request": {
                                "method": "POST",
                                "url": "{{baseUrl}}/users",
                                "body": {
                                    "mode": "raw",
                                    "raw": '{"name": "John Doe", "email": "john@example.com"}',
                                    "options": {"raw": {"language": "json"}},
                                },
                            },
                        },
                    ],
                },
                {
                    "name": "Direct Request",
                    "request": {"method": "GET", "url": "{{baseUrl}}/status"},
                },
            ],
        }

        # Test from_dict
        collection = PythonPostman.from_dict(complex_collection)

        assert collection.info.name == "Complex API Collection"
        assert len(collection.variables) == 2
        assert collection.auth.type == "apikey"
        assert len(collection.events) == 1
        assert len(collection.items) == 2

        # Test that we can get all requests
        all_requests = list(collection.get_all_requests())
        assert len(all_requests) == 3  # 2 in folder + 1 direct

        # Test from_json
        json_string = json.dumps(complex_collection)
        collection_from_json = PythonPostman.from_json(json_string)

        assert collection_from_json.info.name == collection.info.name
        assert len(list(collection_from_json.get_all_requests())) == 3

        # Test from_file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(complex_collection, f)
            temp_path = f.name

        try:
            collection_from_file = PythonPostman.from_file(temp_path)
            assert collection_from_file.info.name == collection.info.name
            assert len(list(collection_from_file.get_all_requests())) == 3
        finally:
            os.unlink(temp_path)

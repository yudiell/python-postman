"""
Integration tests for the Postman Collection Parser.

These tests validate the end-to-end parsing workflow using real Postman collection
JSON files and test various scenarios including complex nested structures,
different authentication types, and error handling.
"""

import pytest
import json
from pathlib import Path
from typing import List

from python_postman.parser import PythonPostman
from python_postman.models.collection import Collection
from python_postman.models.request import Request
from python_postman.models.folder import Folder
from python_postman.exceptions import (
    CollectionParseError,
    CollectionValidationError,
    CollectionFileError,
)


class TestIntegrationBasicParsing:
    """Test basic parsing functionality with real collection files."""

    def test_parse_simple_collection_from_file(self):
        """Test parsing a simple collection from file."""
        file_path = Path(__file__).parent / "test_data" / "simple_collection.json"

        collection = PythonPostman.from_file(file_path)

        assert isinstance(collection, Collection)
        assert collection.info.name == "Simple Test Collection"
        assert (
            collection.info.description == "A basic collection for integration testing"
        )
        assert len(collection.items) == 2

        # Verify requests
        requests = list(collection.get_all_requests())
        assert len(requests) == 2

        get_request = requests[0]
        assert get_request.name == "Get Users"
        assert get_request.method == "GET"
        assert "{{base_url}}/users" in get_request.url.raw

        post_request = requests[1]
        assert post_request.name == "Create User"
        assert post_request.method == "POST"
        assert post_request.body is not None
        assert "John Doe" in post_request.body.raw

        # Verify variables
        assert len(collection.variables) == 1
        base_url_var = collection.variables[0]
        assert base_url_var.key == "base_url"
        assert base_url_var.value == "https://api.example.com"

    def test_parse_simple_collection_from_json_string(self):
        """Test parsing a collection from JSON string."""
        file_path = Path(__file__).parent / "test_data" / "simple_collection.json"

        with open(file_path, "r") as f:
            json_content = f.read()

        collection = PythonPostman.from_json(json_content)

        assert isinstance(collection, Collection)
        assert collection.info.name == "Simple Test Collection"
        assert len(collection.items) == 2

    def test_parse_simple_collection_from_dict(self):
        """Test parsing a collection from dictionary."""
        file_path = Path(__file__).parent / "test_data" / "simple_collection.json"

        with open(file_path, "r") as f:
            collection_dict = json.load(f)

        collection = PythonPostman.from_dict(collection_dict)

        assert isinstance(collection, Collection)
        assert collection.info.name == "Simple Test Collection"
        assert len(collection.items) == 2


class TestIntegrationNestedStructures:
    """Test parsing collections with complex nested folder structures."""

    def test_parse_nested_collection(self):
        """Test parsing a collection with nested folders."""
        file_path = Path(__file__).parent / "test_data" / "nested_collection.json"

        collection = PythonPostman.from_file(file_path)

        assert collection.info.name == "Nested Folder Collection"
        assert len(collection.items) == 2

        # Verify top-level folders
        auth_folder = collection.items[0]
        user_mgmt_folder = collection.items[1]

        assert isinstance(auth_folder, Folder)
        assert auth_folder.name == "Authentication"
        assert len(auth_folder.items) == 2

        assert isinstance(user_mgmt_folder, Folder)
        assert user_mgmt_folder.name == "User Management"
        assert len(user_mgmt_folder.items) == 2

    def test_recursive_request_iteration(self):
        """Test that get_all_requests works with nested folders."""
        file_path = Path(__file__).parent / "test_data" / "nested_collection.json"

        collection = PythonPostman.from_file(file_path)

        # Get all requests recursively
        all_requests = list(collection.get_all_requests())

        # Should find 5 requests total across all nested folders
        assert len(all_requests) == 5

        request_names = [req.name for req in all_requests]
        expected_names = [
            "Login",
            "Logout",
            "Get All Users",
            "Get User by ID",
            "Update Profile",
        ]

        for expected_name in expected_names:
            assert expected_name in request_names

    def test_folder_navigation(self):
        """Test navigation through nested folder structure."""
        file_path = Path(__file__).parent / "test_data" / "nested_collection.json"

        collection = PythonPostman.from_file(file_path)

        # Find folder by name
        user_mgmt_folder = collection.get_folder_by_name("User Management")
        assert user_mgmt_folder is not None
        assert user_mgmt_folder.name == "User Management"

        # Get subfolders
        subfolders = user_mgmt_folder.get_subfolders()
        assert len(subfolders) == 2

        subfolder_names = [folder.name for folder in subfolders]
        assert "Users" in subfolder_names
        assert "Profiles" in subfolder_names

    def test_nested_folder_variables_and_auth(self):
        """Test that nested folders preserve variables and auth settings."""
        file_path = Path(__file__).parent / "test_data" / "nested_collection.json"

        collection = PythonPostman.from_file(file_path)

        # Check collection-level auth and variables
        assert collection.auth is not None
        assert collection.auth.type == "apikey"
        assert len(collection.variables) == 4

        # Check folder-level auth and variables
        user_mgmt_folder = collection.get_folder_by_name("User Management")
        assert user_mgmt_folder.auth is not None
        assert user_mgmt_folder.auth.type == "bearer"
        assert len(user_mgmt_folder.variables) == 1
        assert user_mgmt_folder.variables[0].key == "user_id"


class TestIntegrationAuthenticationTypes:
    """Test parsing collections with various authentication types."""

    def test_parse_auth_collection(self):
        """Test parsing collection with different auth types."""
        file_path = Path(__file__).parent / "test_data" / "auth_collection.json"

        collection = PythonPostman.from_file(file_path)

        assert collection.info.name == "Authentication Types Collection"
        assert len(collection.items) == 4

        # Verify each request has different auth type
        requests = list(collection.get_all_requests())

        basic_auth_request = next(
            req for req in requests if req.name == "Basic Auth Request"
        )
        assert basic_auth_request.auth.type == "basic"

        bearer_request = next(
            req for req in requests if req.name == "Bearer Token Request"
        )
        assert bearer_request.auth.type == "bearer"

        api_key_request = next(req for req in requests if req.name == "API Key Request")
        assert api_key_request.auth.type == "apikey"

        oauth2_request = next(req for req in requests if req.name == "OAuth2 Request")
        assert oauth2_request.auth.type == "oauth2"

    def test_auth_configuration_access(self):
        """Test accessing auth configuration details."""
        file_path = Path(__file__).parent / "test_data" / "auth_collection.json"

        collection = PythonPostman.from_file(file_path)
        requests = list(collection.get_all_requests())

        # Test basic auth configuration
        basic_auth_request = next(
            req for req in requests if req.name == "Basic Auth Request"
        )
        basic_config = basic_auth_request.auth.get_parameter_dict()
        assert "username" in basic_config
        assert "password" in basic_config
        assert basic_config["username"] == "{{basic_username}}"

        # Test API key configuration
        api_key_request = next(req for req in requests if req.name == "API Key Request")
        api_key_config = api_key_request.auth.get_parameter_dict()
        assert "key" in api_key_config
        assert "value" in api_key_config
        assert api_key_config["key"] == "X-API-Key"


class TestIntegrationEventsAndScripts:
    """Test parsing collections with events and scripts."""

    def test_parse_events_collection(self):
        """Test parsing collection with pre-request scripts and tests."""
        file_path = Path(__file__).parent / "test_data" / "events_collection.json"

        collection = PythonPostman.from_file(file_path)

        assert collection.info.name == "Events and Scripts Collection"

        # Check collection-level events
        assert len(collection.events) == 2

        prerequest_event = next(
            event for event in collection.events if event.listen == "prerequest"
        )
        assert prerequest_event is not None
        script_content = prerequest_event.get_script_content()
        assert "console.log" in script_content

        test_event = next(
            event for event in collection.events if event.listen == "test"
        )
        assert test_event is not None
        script_content = test_event.get_script_content()
        assert "console.log" in script_content

    def test_request_level_events(self):
        """Test request-level events and scripts."""
        file_path = Path(__file__).parent / "test_data" / "events_collection.json"

        collection = PythonPostman.from_file(file_path)
        requests = list(collection.get_all_requests())

        request_with_events = requests[0]
        assert len(request_with_events.events) == 2

        # Check pre-request script
        prerequest_event = next(
            event
            for event in request_with_events.events
            if event.listen == "prerequest"
        )
        script_content = prerequest_event.get_script_content()
        assert "pm.globals.set" in script_content

        # Check test script
        test_event = next(
            event for event in request_with_events.events if event.listen == "test"
        )
        script_content = test_event.get_script_content()
        assert "pm.test" in script_content
        assert "Status code is 200" in script_content


class TestIntegrationErrorHandling:
    """Test error handling with malformed collections."""

    def test_file_not_found_error(self):
        """Test error when collection file doesn't exist."""
        non_existent_path = Path(__file__).parent / "test_data" / "non_existent.json"

        with pytest.raises(CollectionFileError) as exc_info:
            PythonPostman.from_file(non_existent_path)

        assert "not found" in str(exc_info.value).lower()

    def test_malformed_json_error(self):
        """Test error when JSON is malformed."""
        file_path = Path(__file__).parent / "test_data" / "malformed_json.json"

        with pytest.raises(CollectionParseError) as exc_info:
            PythonPostman.from_file(file_path)

        assert "json" in str(exc_info.value).lower()

    def test_invalid_collection_structure(self):
        """Test error when collection structure is invalid."""
        file_path = Path(__file__).parent / "test_data" / "invalid_collection.json"

        with pytest.raises(CollectionValidationError) as exc_info:
            PythonPostman.from_file(file_path)

        assert "validation" in str(exc_info.value).lower()

    def test_malformed_json_string_parsing(self):
        """Test error when parsing malformed JSON string."""
        malformed_json = '{"info": {"name": "Test"} "item": []}'  # Missing comma

        with pytest.raises(CollectionParseError):
            PythonPostman.from_json(malformed_json)

    def test_invalid_dict_structure(self):
        """Test error when dictionary structure is invalid."""
        invalid_dict = {"info": {"description": "Missing name field"}, "item": []}

        with pytest.raises(CollectionValidationError):
            PythonPostman.from_dict(invalid_dict)


class TestIntegrationEmptyCollections:
    """Test handling of empty collections."""

    def test_parse_empty_collection(self):
        """Test parsing an empty collection."""
        file_path = Path(__file__).parent / "test_data" / "empty_collection.json"

        collection = PythonPostman.from_file(file_path)

        assert collection.info.name == "Empty Collection"
        assert len(collection.items) == 0
        assert len(collection.variables) == 0

        # Test iteration over empty collection
        requests = list(collection.get_all_requests())
        assert len(requests) == 0

    def test_empty_collection_validation(self):
        """Test that empty collections are still valid."""
        file_path = Path(__file__).parent / "test_data" / "empty_collection.json"

        collection = PythonPostman.from_file(file_path)
        validation_result = collection.validate()

        assert validation_result.is_valid
        assert len(validation_result.errors) == 0


class TestIntegrationSearchAndNavigation:
    """Test search and navigation functionality across collections."""

    def test_request_search_by_name(self):
        """Test finding requests by name across nested structure."""
        file_path = Path(__file__).parent / "test_data" / "nested_collection.json"

        collection = PythonPostman.from_file(file_path)

        # Find specific requests
        login_request = collection.get_request_by_name("Login")
        assert login_request is not None
        assert login_request.method == "POST"

        profile_request = collection.get_request_by_name("Update Profile")
        assert profile_request is not None
        assert profile_request.method == "PUT"

        # Test non-existent request
        non_existent = collection.get_request_by_name("Non Existent Request")
        assert non_existent is None

    def test_folder_search_by_name(self):
        """Test finding folders by name."""
        file_path = Path(__file__).parent / "test_data" / "nested_collection.json"

        collection = PythonPostman.from_file(file_path)

        # Find top-level folder
        auth_folder = collection.get_folder_by_name("Authentication")
        assert auth_folder is not None
        assert len(auth_folder.items) == 2

        # Find nested folder
        users_folder = collection.get_folder_by_name("Users")
        assert users_folder is not None
        assert len(users_folder.items) == 2

        # Test non-existent folder
        non_existent = collection.get_folder_by_name("Non Existent Folder")
        assert non_existent is None


class TestIntegrationValidation:
    """Test comprehensive validation across different collection types."""

    def test_validation_with_all_collection_types(self):
        """Test validation works with all test collection types."""
        test_files = [
            "simple_collection.json",
            "nested_collection.json",
            "auth_collection.json",
            "events_collection.json",
            "empty_collection.json",
        ]

        for filename in test_files:
            file_path = Path(__file__).parent / "test_data" / filename
            collection = PythonPostman.from_file(file_path)

            validation_result = collection.validate()
            assert (
                validation_result.is_valid
            ), f"Validation failed for {filename}: {validation_result.errors}"

    def test_validation_dict_method(self):
        """Test the validate_collection_dict class method."""
        file_path = Path(__file__).parent / "test_data" / "simple_collection.json"

        with open(file_path, "r") as f:
            collection_dict = json.load(f)

        # Valid collection should return True
        is_valid = PythonPostman.validate_collection_dict(collection_dict)
        assert is_valid is True

        # Invalid collection should return False
        invalid_dict = {"info": {"description": "Missing name"}, "item": []}
        is_valid = PythonPostman.validate_collection_dict(invalid_dict)
        assert is_valid is False


class TestIntegrationEndToEndWorkflow:
    """Test complete end-to-end workflows."""

    def test_complete_parsing_workflow(self):
        """Test complete workflow from file to accessing nested data."""
        file_path = Path(__file__).parent / "test_data" / "nested_collection.json"

        # 1. Load collection
        collection = PythonPostman.from_file(file_path)

        # 2. Validate collection
        validation_result = collection.validate()
        assert validation_result.is_valid

        # 3. Access collection metadata
        assert collection.info.name == "Nested Folder Collection"
        assert len(collection.variables) == 4

        # 4. Navigate folder structure
        user_mgmt_folder = collection.get_folder_by_name("User Management")
        assert user_mgmt_folder is not None

        # 5. Access folder-level configuration
        assert user_mgmt_folder.auth.type == "bearer"
        assert len(user_mgmt_folder.variables) == 1

        # 6. Find specific request
        profile_request = collection.get_request_by_name("Update Profile")
        assert profile_request is not None

        # 7. Access request details
        assert profile_request.method == "PUT"
        assert profile_request.body is not None
        assert "Updated bio" in profile_request.body.raw

        # 8. Iterate all requests
        all_requests = list(collection.get_all_requests())
        assert len(all_requests) == 5

    def test_create_new_collection_workflow(self):
        """Test creating a new collection programmatically."""
        # Create new collection
        collection = PythonPostman.create_collection(
            name="Test Collection", description="Programmatically created collection"
        )

        # Validate new collection
        validation_result = collection.validate()
        assert validation_result.is_valid

        # Check properties
        assert collection.info.name == "Test Collection"
        assert collection.info.description == "Programmatically created collection"
        assert len(collection.items) == 0
        assert len(collection.variables) == 0

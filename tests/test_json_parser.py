"""
Tests for JSON parsing utilities.
"""

import json
import pytest
from pathlib import Path
import tempfile
import os

from python_postman.utils.json_parser import parse_json_safely, load_json_file
from python_postman.exceptions import CollectionParseError, CollectionFileError


class TestParseJsonSafely:
    """Test cases for parse_json_safely function."""

    def test_parse_valid_json_object(self):
        """Test parsing a valid JSON object."""
        json_content = '{"name": "test", "value": 123}'
        result = parse_json_safely(json_content)

        assert result == {"name": "test", "value": 123}
        assert isinstance(result, dict)

    def test_parse_complex_json_object(self):
        """Test parsing a complex JSON object with nested structures."""
        json_content = """
        {
            "info": {
                "name": "Test Collection",
                "description": "A test collection"
            },
            "items": [
                {
                    "name": "Request 1",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com"
                    }
                }
            ],
            "variables": []
        }
        """
        result = parse_json_safely(json_content)

        assert "info" in result
        assert "items" in result
        assert result["info"]["name"] == "Test Collection"
        assert len(result["items"]) == 1

    def test_parse_json_with_unicode(self):
        """Test parsing JSON with unicode characters."""
        json_content = '{"name": "测试", "emoji": "🚀", "special": "café"}'
        result = parse_json_safely(json_content)

        assert result["name"] == "测试"
        assert result["emoji"] == "🚀"
        assert result["special"] == "café"

    def test_parse_empty_json_object(self):
        """Test parsing an empty JSON object."""
        json_content = "{}"
        result = parse_json_safely(json_content)

        assert result == {}
        assert isinstance(result, dict)

    def test_parse_json_with_whitespace(self):
        """Test parsing JSON with extra whitespace."""
        json_content = '  \n\t  {"name": "test"}  \n\t  '
        result = parse_json_safely(json_content)

        assert result == {"name": "test"}

    def test_invalid_json_syntax(self):
        """Test handling of invalid JSON syntax."""
        json_content = '{"name": "test", "invalid": }'

        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely(json_content)

        error = exc_info.value
        assert "Failed to parse JSON content" in str(error)
        assert error.details["line"] == 1
        assert "column" in error.details
        assert "error_message" in error.details

    def test_malformed_json_missing_quotes(self):
        """Test handling of JSON with missing quotes."""
        json_content = '{name: "test"}'

        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely(json_content)

        error = exc_info.value
        assert "Failed to parse JSON content" in str(error)
        assert "context" in error.details

    def test_malformed_json_trailing_comma(self):
        """Test handling of JSON with trailing comma."""
        json_content = '{"name": "test", "value": 123,}'

        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely(json_content)

        error = exc_info.value
        assert "Failed to parse JSON content" in str(error)

    def test_json_array_instead_of_object(self):
        """Test handling when JSON is an array instead of object."""
        json_content = '["item1", "item2"]'

        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely(json_content)

        error = exc_info.value
        assert "Expected JSON object, got list" in str(error)
        assert error.details["parsed_type"] == "list"

    def test_json_primitive_instead_of_object(self):
        """Test handling when JSON is a primitive instead of object."""
        json_content = '"just a string"'

        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely(json_content)

        error = exc_info.value
        assert "Expected JSON object, got str" in str(error)

    def test_empty_string_input(self):
        """Test handling of empty string input."""
        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely("")

        error = exc_info.value
        assert "Empty or whitespace-only JSON content" in str(error)

    def test_whitespace_only_input(self):
        """Test handling of whitespace-only input."""
        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely("   \n\t   ")

        error = exc_info.value
        assert "Empty or whitespace-only JSON content" in str(error)

    def test_non_string_input(self):
        """Test handling of non-string input."""
        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely({"already": "parsed"})

        error = exc_info.value
        assert "Expected string input, got dict" in str(error)

    def test_none_input(self):
        """Test handling of None input."""
        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely(None)

        error = exc_info.value
        assert "Expected string input, got NoneType" in str(error)

    def test_multiline_json_error_context(self):
        """Test error context for multiline JSON."""
        json_content = """
        {
            "name": "test",
            "invalid": ,
            "other": "value"
        }
        """

        with pytest.raises(CollectionParseError) as exc_info:
            parse_json_safely(json_content)

        error = exc_info.value
        assert error.details["line"] == 4  # Error is on line 4
        assert "invalid" in error.details["error_line"]


class TestLoadJsonFile:
    """Test cases for load_json_file function."""

    def test_load_valid_json_file(self):
        """Test loading a valid JSON file."""
        test_data = {"name": "test collection", "version": "1.0"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            result = load_json_file(temp_path)
            assert result == test_data
        finally:
            os.unlink(temp_path)

    def test_load_json_file_with_path_object(self):
        """Test loading JSON file using Path object."""
        test_data = {"name": "test collection"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = Path(f.name)

        try:
            result = load_json_file(temp_path)
            assert result == test_data
        finally:
            temp_path.unlink()

    def test_load_nonexistent_file(self):
        """Test handling of nonexistent file."""
        nonexistent_path = "/path/that/does/not/exist.json"

        with pytest.raises(CollectionFileError) as exc_info:
            load_json_file(nonexistent_path)

        error = exc_info.value
        assert "File not found" in str(error)
        assert error.details["exists"] is False

    def test_load_directory_instead_of_file(self):
        """Test handling when path points to directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with pytest.raises(CollectionFileError) as exc_info:
                load_json_file(temp_dir)

            error = exc_info.value
            assert "Path is not a file" in str(error)
            assert error.details["is_file"] is False

    def test_load_file_with_invalid_json(self):
        """Test loading file with invalid JSON content."""
        invalid_json = '{"name": "test", invalid: }'

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(invalid_json)
            temp_path = f.name

        try:
            with pytest.raises(CollectionParseError):
                load_json_file(temp_path)
        finally:
            os.unlink(temp_path)

    def test_load_file_with_non_utf8_encoding(self):
        """Test loading file with non-UTF8 encoding."""
        # Create a file with invalid UTF-8 bytes
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".json", delete=False) as f:
            f.write(b'\xff\xfe{"name": "test"}')  # Invalid UTF-8 sequence
            temp_path = f.name

        try:
            with pytest.raises(CollectionFileError) as exc_info:
                load_json_file(temp_path)

            error = exc_info.value
            assert "Failed to decode file as UTF-8" in str(error)
        finally:
            os.unlink(temp_path)

    def test_load_file_permission_error(self):
        """Test handling of file permission errors."""
        # This test might not work on all systems, so we'll skip if needed
        test_data = {"name": "test"}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(test_data, f)
            temp_path = f.name

        try:
            # Try to make file unreadable (might not work on Windows)
            try:
                os.chmod(temp_path, 0o000)

                with pytest.raises(CollectionFileError) as exc_info:
                    load_json_file(temp_path)

                error = exc_info.value
                assert "Failed to read file" in str(error)

            except (OSError, PermissionError):
                # Skip this test if we can't change permissions
                pytest.skip("Cannot test permission errors on this system")

        finally:
            # Restore permissions and clean up
            try:
                os.chmod(temp_path, 0o644)
                os.unlink(temp_path)
            except (OSError, PermissionError):
                pass

    def test_load_empty_file(self):
        """Test loading an empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Write nothing to create empty file
            temp_path = f.name

        try:
            with pytest.raises(CollectionParseError) as exc_info:
                load_json_file(temp_path)

            error = exc_info.value
            assert "Empty or whitespace-only JSON content" in str(error)
        finally:
            os.unlink(temp_path)

    def test_load_large_json_file(self):
        """Test loading a large JSON file."""
        # Create a reasonably large JSON structure
        large_data = {
            "info": {"name": "Large Collection"},
            "items": [
                {
                    "name": f"Request {i}",
                    "request": {
                        "method": "GET",
                        "url": f"https://api.example.com/endpoint/{i}",
                        "headers": [
                            {"key": f"Header-{j}", "value": f"Value-{j}"}
                            for j in range(10)
                        ],
                    },
                }
                for i in range(100)
            ],
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(large_data, f)
            temp_path = f.name

        try:
            result = load_json_file(temp_path)
            assert len(result["items"]) == 100
            assert result["info"]["name"] == "Large Collection"
        finally:
            os.unlink(temp_path)

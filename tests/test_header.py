"""Tests for Header model."""

import pytest
from python_postman.models.header import Header, HeaderCollection


class TestHeader:
    """Test Header class."""

    def test_init_basic(self):
        """Test basic Header initialization."""
        header = Header(key="Content-Type", value="application/json")
        assert header.key == "Content-Type"
        assert header.value == "application/json"
        assert header.description is None
        assert header.disabled is False
        assert header.type is None

    def test_init_full(self):
        """Test Header initialization with all parameters."""
        header = Header(
            key="Authorization",
            value="Bearer token123",
            description="API authentication token",
            disabled=True,
            type="auth",
        )
        assert header.key == "Authorization"
        assert header.value == "Bearer token123"
        assert header.description == "API authentication token"
        assert header.disabled is True
        assert header.type == "auth"

    def test_is_active_enabled(self):
        """Test is_active for enabled header."""
        header = Header(key="Content-Type", value="application/json")
        assert header.is_active() is True

    def test_is_active_disabled(self):
        """Test is_active for disabled header."""
        header = Header(key="Content-Type", value="application/json", disabled=True)
        assert header.is_active() is False

    def test_is_active_empty_key(self):
        """Test is_active for header with empty key."""
        header = Header(key="", value="application/json")
        assert header.is_active() is False

    def test_get_effective_value_basic(self):
        """Test getting effective value without variables."""
        header = Header(key="Content-Type", value="application/json")
        assert header.get_effective_value() == "application/json"

    def test_get_effective_value_disabled(self):
        """Test getting effective value for disabled header."""
        header = Header(key="Content-Type", value="application/json", disabled=True)
        assert header.get_effective_value() is None

    def test_get_effective_value_empty(self):
        """Test getting effective value for header with no value."""
        header = Header(key="Content-Type")
        assert header.get_effective_value() is None

    def test_get_effective_value_with_variables(self):
        """Test getting effective value with variable resolution."""
        header = Header(key="Authorization", value="Bearer {{token}}")
        variables = {"token": "abc123"}

        result = header.get_effective_value(variables)
        assert result == "Bearer abc123"

    def test_get_effective_value_multiple_variables(self):
        """Test getting effective value with multiple variables."""
        header = Header(key="Custom-Header", value="{{prefix}}-{{suffix}}")
        variables = {"prefix": "test", "suffix": "value"}

        result = header.get_effective_value(variables)
        assert result == "test-value"

    def test_normalize_key_basic(self):
        """Test basic key normalization."""
        header = Header(key="content-type")
        assert header.normalize_key() == "Content-Type"

    def test_normalize_key_multiple_words(self):
        """Test key normalization with multiple words."""
        header = Header(key="x-custom-header")
        assert header.normalize_key() == "X-Custom-Header"

    def test_normalize_key_already_normalized(self):
        """Test key normalization when already normalized."""
        header = Header(key="Content-Type")
        assert header.normalize_key() == "Content-Type"

    def test_normalize_key_empty(self):
        """Test key normalization with empty key."""
        header = Header(key="")
        assert header.normalize_key() == ""

    def test_is_standard_header_true(self):
        """Test is_standard_header for standard headers."""
        standard_headers = [
            "Content-Type",
            "Authorization",
            "Accept",
            "User-Agent",
            "Cache-Control",
            "Set-Cookie",
            "X-Forwarded-For",
        ]

        for key in standard_headers:
            header = Header(key=key)
            assert header.is_standard_header() is True, f"{key} should be standard"

    def test_is_standard_header_false(self):
        """Test is_standard_header for non-standard headers."""
        non_standard_headers = ["X-Custom-Header", "My-Special-Header", "App-Version"]

        for key in non_standard_headers:
            header = Header(key=key)
            assert header.is_standard_header() is False, f"{key} should not be standard"

    def test_is_standard_header_case_insensitive(self):
        """Test is_standard_header is case insensitive."""
        header = Header(key="CONTENT-TYPE")
        assert header.is_standard_header() is True

    def test_validate_success(self):
        """Test successful header validation."""
        header = Header(key="Content-Type", value="application/json")
        assert header.validate() is True

    def test_validate_failure_empty_key(self):
        """Test validation failure with empty key."""
        header = Header(key="")
        with pytest.raises(ValueError, match="Header key is required"):
            header.validate()

    def test_validate_failure_none_key(self):
        """Test validation failure with None key."""
        header = Header(key=None)
        with pytest.raises(ValueError, match="Header key is required"):
            header.validate()

    def test_validate_failure_whitespace_key(self):
        """Test validation failure with whitespace-only key."""
        header = Header(key="   ")
        with pytest.raises(ValueError, match="Header key is required"):
            header.validate()

    def test_validate_failure_invalid_value_type(self):
        """Test validation failure with invalid value type."""
        header = Header(key="Content-Type", value=123)
        with pytest.raises(ValueError, match="Header value must be a string"):
            header.validate()

    def test_validate_failure_invalid_description_type(self):
        """Test validation failure with invalid description type."""
        header = Header(key="Content-Type", description=123)
        with pytest.raises(ValueError, match="Header description must be a string"):
            header.validate()

    def test_validate_failure_invalid_disabled_type(self):
        """Test validation failure with invalid disabled type."""
        header = Header(key="Content-Type")
        header.disabled = "false"  # Should be boolean
        with pytest.raises(ValueError, match="Header disabled flag must be a boolean"):
            header.validate()

    def test_validate_failure_invalid_type_type(self):
        """Test validation failure with invalid type field."""
        header = Header(key="Content-Type", type=123)
        with pytest.raises(ValueError, match="Header type must be a string"):
            header.validate()

    def test_validate_failure_invalid_characters(self):
        """Test validation failure with invalid characters in key."""
        invalid_keys = [
            "Content\nType",
            "Content\rType",
            "Content\0Type",
            "Content:Type",
        ]

        for key in invalid_keys:
            header = Header(key=key)
            with pytest.raises(
                ValueError, match="Header key contains invalid characters"
            ):
                header.validate()

    def test_from_dict_basic(self):
        """Test creating Header from dictionary."""
        data = {
            "key": "Content-Type",
            "value": "application/json",
            "description": "Content type header",
            "disabled": False,
        }

        header = Header.from_dict(data)
        assert header.key == "Content-Type"
        assert header.value == "application/json"
        assert header.description == "Content type header"
        assert header.disabled is False

    def test_from_dict_minimal(self):
        """Test creating Header from minimal dictionary."""
        data = {"key": "Accept"}

        header = Header.from_dict(data)
        assert header.key == "Accept"
        assert header.value is None
        assert header.disabled is False

    def test_from_dict_empty(self):
        """Test creating Header from empty dictionary."""
        data = {}

        header = Header.from_dict(data)
        assert header.key == ""
        assert header.value is None
        assert header.disabled is False

    def test_to_dict_full(self):
        """Test converting Header to dictionary with all fields."""
        header = Header(
            key="Authorization",
            value="Bearer token",
            description="Auth header",
            disabled=True,
            type="auth",
        )

        result = header.to_dict()
        expected = {
            "key": "Authorization",
            "value": "Bearer token",
            "description": "Auth header",
            "disabled": True,
            "type": "auth",
        }
        assert result == expected

    def test_to_dict_minimal(self):
        """Test converting Header to dictionary with minimal fields."""
        header = Header(key="Accept")

        result = header.to_dict()
        expected = {"key": "Accept", "disabled": False}
        assert result == expected

    def test_equality(self):
        """Test Header equality."""
        header1 = Header(key="Content-Type", value="application/json")
        header2 = Header(key="Content-Type", value="application/json")
        header3 = Header(key="Content-Type", value="text/plain")

        assert header1 == header2
        assert header1 != header3
        assert header1 != "not a header"

    def test_str_representation(self):
        """Test string representation for HTTP headers."""
        header = Header(key="Content-Type", value="application/json")
        assert str(header) == "Content-Type: application/json"

    def test_str_representation_disabled(self):
        """Test string representation for disabled header."""
        header = Header(key="Content-Type", value="application/json", disabled=True)
        assert str(header) == ""

    def test_str_representation_empty_key(self):
        """Test string representation for header with empty key."""
        header = Header(key="", value="application/json")
        assert str(header) == ""

    def test_str_representation_no_value(self):
        """Test string representation for header with no value."""
        header = Header(key="Content-Type")
        assert str(header) == "Content-Type: "

    def test_repr(self):
        """Test Header repr."""
        header = Header(key="Content-Type", value="application/json")
        result = repr(header)
        assert "Header" in result
        assert "Content-Type" in result
        assert "application/json" in result


class TestHeaderCollection:
    """Test HeaderCollection class."""

    def test_init_empty(self):
        """Test empty HeaderCollection initialization."""
        collection = HeaderCollection()
        assert len(collection) == 0
        assert collection.headers == []

    def test_init_with_headers(self):
        """Test HeaderCollection initialization with headers."""
        headers = [
            Header("Content-Type", "application/json"),
            Header("Accept", "application/json"),
        ]
        collection = HeaderCollection(headers)
        assert len(collection) == 2
        assert collection.headers == headers

    def test_add_header(self):
        """Test adding header to collection."""
        collection = HeaderCollection()
        header = collection.add("Content-Type", "application/json", "Content type")

        assert len(collection) == 1
        assert header.key == "Content-Type"
        assert header.value == "application/json"
        assert header.description == "Content type"

    def test_remove_header_success(self):
        """Test removing existing header."""
        collection = HeaderCollection(
            [
                Header("Content-Type", "application/json"),
                Header("Accept", "application/json"),
            ]
        )

        result = collection.remove("Content-Type")
        assert result is True
        assert len(collection) == 1
        assert collection.get("Content-Type") is None

    def test_remove_header_case_insensitive(self):
        """Test removing header is case insensitive."""
        collection = HeaderCollection([Header("Content-Type", "application/json")])

        result = collection.remove("content-type")
        assert result is True
        assert len(collection) == 0

    def test_remove_header_not_found(self):
        """Test removing non-existent header."""
        collection = HeaderCollection([Header("Content-Type", "application/json")])

        result = collection.remove("Accept")
        assert result is False
        assert len(collection) == 1

    def test_get_header_success(self):
        """Test getting existing header."""
        header = Header("Content-Type", "application/json")
        collection = HeaderCollection([header])

        found = collection.get("Content-Type")
        assert found == header

    def test_get_header_case_insensitive(self):
        """Test getting header is case insensitive."""
        header = Header("Content-Type", "application/json")
        collection = HeaderCollection([header])

        found = collection.get("content-type")
        assert found == header

    def test_get_header_not_found(self):
        """Test getting non-existent header."""
        collection = HeaderCollection([Header("Content-Type", "application/json")])

        found = collection.get("Accept")
        assert found is None

    def test_get_value_success(self):
        """Test getting header value."""
        collection = HeaderCollection([Header("Content-Type", "application/json")])

        value = collection.get_value("Content-Type")
        assert value == "application/json"

    def test_get_value_with_variables(self):
        """Test getting header value with variable resolution."""
        collection = HeaderCollection([Header("Authorization", "Bearer {{token}}")])

        value = collection.get_value("Authorization", {"token": "abc123"})
        assert value == "Bearer abc123"

    def test_get_value_not_found(self):
        """Test getting value for non-existent header."""
        collection = HeaderCollection()

        value = collection.get_value("Content-Type")
        assert value is None

    def test_set_new_header(self):
        """Test setting new header."""
        collection = HeaderCollection()
        header = collection.set("Content-Type", "application/json", "Content type")

        assert len(collection) == 1
        assert header.key == "Content-Type"
        assert header.value == "application/json"
        assert header.description == "Content type"

    def test_set_existing_header(self):
        """Test setting existing header updates value."""
        existing = Header("Content-Type", "text/plain")
        collection = HeaderCollection([existing])

        header = collection.set(
            "Content-Type", "application/json", "Updated description"
        )

        assert len(collection) == 1
        assert header == existing  # Same object
        assert header.value == "application/json"
        assert header.description == "Updated description"

    def test_get_active_headers(self):
        """Test getting only active headers."""
        collection = HeaderCollection(
            [
                Header("Content-Type", "application/json"),  # Active
                Header("Accept", "application/json", disabled=True),  # Disabled
                Header("", "value"),  # Empty key
                Header("Authorization", "Bearer token"),  # Active
            ]
        )

        active = collection.get_active_headers()
        assert len(active) == 2
        assert active[0].key == "Content-Type"
        assert active[1].key == "Authorization"

    def test_to_http_dict_basic(self):
        """Test converting to HTTP dictionary."""
        collection = HeaderCollection(
            [
                Header("Content-Type", "application/json"),
                Header("Accept", "application/json"),
                Header("Disabled", "value", disabled=True),
            ]
        )

        result = collection.to_http_dict()
        expected = {"Content-Type": "application/json", "Accept": "application/json"}
        assert result == expected

    def test_to_http_dict_with_variables(self):
        """Test converting to HTTP dictionary with variable resolution."""
        collection = HeaderCollection(
            [
                Header("Authorization", "Bearer {{token}}"),
                Header("X-Version", "{{version}}"),
            ]
        )

        variables = {"token": "abc123", "version": "1.0"}
        result = collection.to_http_dict(variables)
        expected = {"Authorization": "Bearer abc123", "X-Version": "1.0"}
        assert result == expected

    def test_validate_all_success(self):
        """Test validating all headers successfully."""
        collection = HeaderCollection(
            [
                Header("Content-Type", "application/json"),
                Header("Accept", "application/json"),
            ]
        )

        assert collection.validate_all() is True

    def test_validate_all_failure(self):
        """Test validation failure in collection."""
        collection = HeaderCollection(
            [
                Header("Content-Type", "application/json"),
                Header(""),  # Invalid empty key
            ]
        )

        with pytest.raises(ValueError):
            collection.validate_all()

    def test_iteration(self):
        """Test iterating over header collection."""
        headers = [
            Header("Content-Type", "application/json"),
            Header("Accept", "application/json"),
        ]
        collection = HeaderCollection(headers)

        result = list(collection)
        assert result == headers

    def test_indexing(self):
        """Test indexing header collection."""
        headers = [
            Header("Content-Type", "application/json"),
            Header("Accept", "application/json"),
        ]
        collection = HeaderCollection(headers)

        assert collection[0] == headers[0]
        assert collection[1] == headers[1]

    def test_repr(self):
        """Test HeaderCollection repr."""
        collection = HeaderCollection(
            [
                Header("Content-Type", "application/json"),
                Header("Accept", "application/json"),
            ]
        )

        result = repr(collection)
        assert "HeaderCollection" in result
        assert "2 headers" in result

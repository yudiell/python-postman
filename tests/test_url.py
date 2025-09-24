"""Tests for URL model."""

import pytest
from python_postman.models.url import Url, QueryParam


class TestQueryParam:
    """Test QueryParam class."""

    def test_init_basic(self):
        """Test basic QueryParam initialization."""
        param = QueryParam(key="test", value="value")
        assert param.key == "test"
        assert param.value == "value"
        assert param.description is None
        assert param.disabled is False

    def test_init_full(self):
        """Test QueryParam initialization with all parameters."""
        param = QueryParam(
            key="param1", value="value1", description="Test parameter", disabled=True
        )
        assert param.key == "param1"
        assert param.value == "value1"
        assert param.description == "Test parameter"
        assert param.disabled is True

    def test_equality(self):
        """Test QueryParam equality."""
        param1 = QueryParam(key="test", value="value")
        param2 = QueryParam(key="test", value="value")
        param3 = QueryParam(key="test", value="different")

        assert param1 == param2
        assert param1 != param3
        assert param1 != "not a param"

    def test_repr(self):
        """Test QueryParam string representation."""
        param = QueryParam(key="test", value="value")
        assert "QueryParam" in repr(param)
        assert "test" in repr(param)


class TestUrl:
    """Test Url class."""

    def test_init_empty(self):
        """Test empty URL initialization."""
        url = Url()
        assert url.raw is None
        assert url.protocol is None
        assert url.host == []
        assert url.path == []
        assert url.port is None
        assert url.query == []
        assert url.hash is None
        assert url.variable == []

    def test_init_with_raw_url(self):
        """Test URL initialization with raw URL string."""
        raw_url = (
            "https://api.example.com:8080/users/123?active=true&sort=name#section1"
        )
        url = Url(raw=raw_url)

        assert url.raw == raw_url
        assert url.protocol == "https"
        assert url.host == ["api.example.com"]
        assert url.path == ["users", "123"]
        assert url.port == "8080"
        assert len(url.query) == 2
        assert url.hash == "section1"

    def test_init_with_components(self):
        """Test URL initialization with individual components."""
        url = Url(
            protocol="https",
            host=["api", "example", "com"],
            path=["v1", "users"],
            port="443",
            query=[QueryParam("limit", "10")],
            hash="top",
        )

        assert url.protocol == "https"
        assert url.host == ["api", "example", "com"]
        assert url.path == ["v1", "users"]
        assert url.port == "443"
        assert len(url.query) == 1
        assert url.hash == "top"

    def test_parse_simple_url(self):
        """Test parsing simple URL."""
        url = Url(raw="https://example.com/path")
        assert url.protocol == "https"
        assert url.host == ["example.com"]
        assert url.path == ["path"]

    def test_parse_complex_url(self):
        """Test parsing complex URL with all components."""
        raw_url = "https://api.example.com:8080/v1/users/123?active=true&sort=name&sort=date#section"
        url = Url(raw=raw_url)

        assert url.protocol == "https"
        assert url.host == ["api.example.com"]
        assert url.path == ["v1", "users", "123"]
        assert url.port == "8080"
        assert len(url.query) == 3  # active, sort (2 values)
        assert url.hash == "section"

    def test_get_url_string_from_raw(self):
        """Test getting URL string when raw URL is provided."""
        raw_url = "https://example.com/test"
        url = Url(raw=raw_url)
        assert url.get_url_string() == raw_url

    def test_get_url_string_from_components(self):
        """Test constructing URL string from components."""
        url = Url(
            protocol="https",
            host=["api", "example", "com"],
            path=["v1", "users"],
            port="8080",
            query=[QueryParam("active", "true"), QueryParam("limit", "10")],
        )

        result = url.get_url_string()
        assert "https://api.example.com:8080/v1/users" in result
        assert "active=true" in result
        assert "limit=10" in result

    def test_get_url_string_with_variables(self):
        """Test URL string construction with variable resolution."""
        url = Url(
            protocol="https",
            host=["{{host}}"],
            path=["api", "v1", "users", ":userId"],
            query=[QueryParam("token", "{{apiKey}}")],
        )

        variables = {"host": "api.example.com", "userId": "123", "apiKey": "secret123"}

        result = url.get_url_string(resolve_variables=True, variable_context=variables)
        assert "https://api.example.com/api/v1/users/123" in result
        assert "token=secret123" in result

    def test_add_query_param(self):
        """Test adding query parameters."""
        url = Url()
        url.add_query_param("test", "value")
        url.add_query_param("empty")

        assert len(url.query) == 2
        assert url.query[0].key == "test"
        assert url.query[0].value == "value"
        assert url.query[1].key == "empty"
        assert url.query[1].value is None

    def test_remove_query_param(self):
        """Test removing query parameters."""
        url = Url(
            query=[
                QueryParam("keep", "value1"),
                QueryParam("remove", "value2"),
                QueryParam("keep2", "value3"),
            ]
        )

        result = url.remove_query_param("remove")
        assert result is True
        assert len(url.query) == 2
        assert all(q.key != "remove" for q in url.query)

        result = url.remove_query_param("nonexistent")
        assert result is False

    def test_get_query_param(self):
        """Test getting query parameter by key."""
        param = QueryParam("test", "value")
        url = Url(query=[param])

        found = url.get_query_param("test")
        assert found == param

        not_found = url.get_query_param("missing")
        assert not_found is None

    def test_get_path_variables_colon_format(self):
        """Test extracting path variables in :variable format."""
        url = Url(path=["api", "users", ":userId", "posts", ":postId"])
        variables = url.get_path_variables()
        assert "userId" in variables
        assert "postId" in variables

    def test_get_path_variables_braces_format(self):
        """Test extracting path variables in {{variable}} format."""
        url = Url(path=["api", "{{version}}", "users", "{{userId}}"])
        variables = url.get_path_variables()
        assert "version" in variables
        assert "userId" in variables

    def test_get_path_variables_mixed_format(self):
        """Test extracting path variables in mixed formats."""
        url = Url(path=["api", ":version", "users", "{{userId}}"])
        variables = url.get_path_variables()
        assert "version" in variables
        assert "userId" in variables
        assert len(variables) == 2

    def test_validate_success(self):
        """Test successful URL validation."""
        url = Url(raw="https://example.com")
        assert url.validate() is True

        url2 = Url(host=["example.com"])
        assert url2.validate() is True

    def test_validate_failure_no_url_or_host(self):
        """Test validation failure when no URL or host provided."""
        url = Url()
        with pytest.raises(
            ValueError, match="URL must have either raw URL string or host specified"
        ):
            url.validate()

    def test_validate_failure_invalid_protocol(self):
        """Test validation failure with invalid protocol."""
        url = Url(host=["example.com"], protocol=123)
        with pytest.raises(ValueError, match="Protocol must be a string"):
            url.validate()

    def test_validate_failure_invalid_port(self):
        """Test validation failure with invalid port."""
        url = Url(host=["example.com"], port=8080)
        with pytest.raises(ValueError, match="Port must be a string"):
            url.validate()

    def test_validate_failure_invalid_query_param(self):
        """Test validation failure with invalid query parameter."""
        url = Url(host=["example.com"], query=["not a QueryParam"])
        with pytest.raises(
            ValueError, match="All query items must be QueryParam instances"
        ):
            url.validate()

    def test_validate_failure_empty_query_key(self):
        """Test validation failure with empty query parameter key."""
        url = Url(host=["example.com"], query=[QueryParam("")])
        with pytest.raises(ValueError, match="Query parameter key is required"):
            url.validate()

    def test_from_dict_basic(self):
        """Test creating URL from dictionary."""
        data = {
            "raw": "https://example.com/test",
            "protocol": "https",
            "host": ["example.com"],
            "path": ["test"],
        }

        url = Url.from_dict(data)
        assert url.raw == "https://example.com/test"
        assert url.protocol == "https"
        assert url.host == ["example.com"]
        assert url.path == ["test"]

    def test_from_dict_with_query(self):
        """Test creating URL from dictionary with query parameters."""
        data = {
            "raw": "https://example.com",
            "query": [
                {"key": "param1", "value": "value1"},
                {"key": "param2", "value": "value2", "disabled": True},
            ],
        }

        url = Url.from_dict(data)
        assert len(url.query) == 2
        assert url.query[0].key == "param1"
        assert url.query[0].value == "value1"
        assert url.query[1].disabled is True

    def test_to_dict_basic(self):
        """Test converting URL to dictionary."""
        url = Url(
            raw="https://example.com/test",
            protocol="https",
            host=["example.com"],
            path=["test"],
        )

        result = url.to_dict()
        assert result["raw"] == "https://example.com/test"
        assert result["protocol"] == "https"
        assert result["host"] == ["example.com"]
        assert result["path"] == ["test"]

    def test_to_dict_with_query(self):
        """Test converting URL with query parameters to dictionary."""
        url = Url(
            raw="https://example.com",
            query=[QueryParam("param1", "value1"), QueryParam("param2", disabled=True)],
        )

        result = url.to_dict()
        assert len(result["query"]) == 2
        assert result["query"][0]["key"] == "param1"
        assert result["query"][0]["value"] == "value1"
        assert result["query"][1]["disabled"] is True

    def test_equality(self):
        """Test URL equality."""
        url1 = Url(raw="https://example.com")
        url2 = Url(raw="https://example.com")
        url3 = Url(raw="https://different.com")

        assert url1 == url2
        assert url1 != url3
        assert url1 != "not a url"

    def test_repr(self):
        """Test URL string representation."""
        url = Url(raw="https://example.com", protocol="https", host=["example.com"])
        result = repr(url)
        assert "Url" in result
        assert "https://example.com" in result

    def test_disabled_query_params_excluded(self):
        """Test that disabled query parameters are excluded from URL string."""
        url = Url(
            protocol="https",
            host=["example.com"],
            query=[
                QueryParam("active", "true"),
                QueryParam("disabled", "value", disabled=True),
                QueryParam("limit", "10"),
            ],
        )

        result = url.get_url_string()
        assert "active=true" in result
        assert "limit=10" in result
        assert "disabled=value" not in result

    def test_host_as_string_conversion(self):
        """Test that host provided as string is converted to list."""
        url = Url(host="example.com")
        assert url.host == ["example.com"]

    def test_path_as_string_conversion(self):
        """Test that path provided as string is converted to list."""
        url = Url(path="api/v1/users")
        assert url.path == ["api", "v1", "users"]

    def test_malformed_raw_url_handling(self):
        """Test handling of malformed raw URLs."""
        url = Url(raw="not-a-valid-url")
        # Should not raise exception, just keep the raw URL
        assert url.raw == "not-a-valid-url"
        # Components should remain empty/default
        assert url.protocol is None

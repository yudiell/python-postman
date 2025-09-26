"""Tests for VariableResolver class."""

import pytest
import json
from python_postman.execution.variable_resolver import VariableResolver
from python_postman.execution.context import ExecutionContext
from python_postman.execution.exceptions import VariableResolutionError
from python_postman.models.url import Url, QueryParam
from python_postman.models.header import Header
from python_postman.models.body import Body, FormParameter
from python_postman.models.auth import Auth, AuthParameter


class TestVariableResolver:
    """Test cases for VariableResolver."""

    def test_init(self):
        """Test VariableResolver initialization."""
        context = ExecutionContext()
        resolver = VariableResolver(context)
        assert resolver.context is context

    def test_resolve_string_basic(self):
        """Test basic string variable resolution."""
        context = ExecutionContext(
            collection_variables={"name": "test", "value": "123"}
        )
        resolver = VariableResolver(context)

        # Test single variable
        result = resolver.resolve_string("Hello {{name}}")
        assert result == "Hello test"

        # Test multiple variables
        result = resolver.resolve_string("{{name}}-{{value}}")
        assert result == "test-123"

        # Test no variables
        result = resolver.resolve_string("no variables here")
        assert result == "no variables here"

    def test_resolve_string_variable_precedence(self):
        """Test variable resolution follows correct precedence."""
        context = ExecutionContext(
            environment_variables={"var": "env"},
            collection_variables={"var": "collection"},
            folder_variables={"var": "folder"},
            request_variables={"var": "request"},
        )
        resolver = VariableResolver(context)

        # Request scope should take precedence
        result = resolver.resolve_string("{{var}}")
        assert result == "request"

    def test_resolve_string_recursive(self):
        """Test recursive variable resolution."""
        context = ExecutionContext(
            collection_variables={
                "base_url": "https://{{host}}",
                "host": "api.example.com",
                "endpoint": "{{base_url}}/users",
            }
        )
        resolver = VariableResolver(context)

        result = resolver.resolve_string("{{endpoint}}")
        assert result == "https://api.example.com/users"

    def test_resolve_string_circular_reference(self):
        """Test circular reference protection."""
        context = ExecutionContext(
            collection_variables={"var1": "{{var2}}", "var2": "{{var1}}"}
        )
        resolver = VariableResolver(context)

        with pytest.raises(VariableResolutionError, match="Maximum recursion depth"):
            resolver.resolve_string("{{var1}}")

    def test_resolve_string_missing_variable(self):
        """Test handling of missing variables."""
        context = ExecutionContext()
        resolver = VariableResolver(context)

        with pytest.raises(
            VariableResolutionError, match="Variable 'missing' not found"
        ):
            resolver.resolve_string("{{missing}}")

    def test_resolve_string_non_string_input(self):
        """Test handling of non-string input."""
        context = ExecutionContext()
        resolver = VariableResolver(context)

        # Should convert to string
        result = resolver.resolve_string(123)
        assert result == "123"

        result = resolver.resolve_string(None)
        assert result == ""

    def test_resolve_url_raw(self):
        """Test URL resolution with raw URL string."""
        context = ExecutionContext(
            collection_variables={
                "base_url": "https://api.example.com",
                "version": "v1",
            }
        )
        resolver = VariableResolver(context)

        url = Url(raw="{{base_url}}/{{version}}/users")
        result = resolver.resolve_url(url)
        assert result == "https://api.example.com/v1/users"

    def test_resolve_url_components(self):
        """Test URL resolution with component-based URL."""
        context = ExecutionContext(
            collection_variables={
                "host": "api.example.com",
                "version": "v1",
                "resource": "users",
            }
        )
        resolver = VariableResolver(context)

        url = Url(
            protocol="https",
            host=["{{host}}"],
            path=["{{version}}", "{{resource}}"],
            port="443",
        )
        result = resolver.resolve_url(url)
        assert result == "https://api.example.com:443/v1/users"

    def test_resolve_url_with_query_params(self):
        """Test URL resolution with query parameters."""
        context = ExecutionContext(
            collection_variables={
                "base_url": "https://api.example.com",
                "limit": "10",
                "sort": "name",
            }
        )
        resolver = VariableResolver(context)

        url = Url(
            raw="{{base_url}}/users",
            query=[
                QueryParam("limit", "{{limit}}"),
                QueryParam("sort", "{{sort}}"),
                QueryParam("disabled", "value", disabled=True),
            ],
        )
        result = resolver.resolve_url(url)
        assert "https://api.example.com/users?limit=10&sort=name" in result
        assert "disabled" not in result

    def test_resolve_url_with_hash(self):
        """Test URL resolution with hash fragment."""
        context = ExecutionContext(collection_variables={"section": "top"})
        resolver = VariableResolver(context)

        url = Url(raw="https://example.com/page", hash="{{section}}")
        result = resolver.resolve_url(url)
        assert result == "https://example.com/page#top"

    def test_resolve_url_empty(self):
        """Test URL resolution with empty URL."""
        context = ExecutionContext()
        resolver = VariableResolver(context)

        result = resolver.resolve_url(None)
        assert result == ""

        result = resolver.resolve_url(Url())
        assert result == "https://"

    def test_resolve_headers_basic(self):
        """Test basic header resolution."""
        context = ExecutionContext(
            collection_variables={"token": "abc123", "content_type": "application/json"}
        )
        resolver = VariableResolver(context)

        headers = [
            Header("Authorization", "Bearer {{token}}"),
            Header("Content-Type", "{{content_type}}"),
            Header("Disabled-Header", "value", disabled=True),
        ]

        result = resolver.resolve_headers(headers)
        expected = {
            "Authorization": "Bearer abc123",
            "Content-Type": "application/json",
        }
        assert result == expected

    def test_resolve_headers_empty(self):
        """Test header resolution with empty headers."""
        context = ExecutionContext()
        resolver = VariableResolver(context)

        result = resolver.resolve_headers([])
        assert result == {}

        result = resolver.resolve_headers(None)
        assert result == {}

    def test_resolve_headers_with_variable_keys(self):
        """Test header resolution with variables in keys."""
        context = ExecutionContext(
            collection_variables={
                "header_name": "X-Custom-Header",
                "header_value": "custom-value",
            }
        )
        resolver = VariableResolver(context)

        headers = [Header("{{header_name}}", "{{header_value}}")]
        result = resolver.resolve_headers(headers)
        assert result == {"X-Custom-Header": "custom-value"}

    def test_resolve_body_raw_text(self):
        """Test body resolution with raw text."""
        context = ExecutionContext(collection_variables={"message": "Hello World"})
        resolver = VariableResolver(context)

        body = Body(mode="raw", raw="{{message}}")
        result = resolver.resolve_body(body)
        assert result == "Hello World"

    def test_resolve_body_raw_json(self):
        """Test body resolution with raw JSON."""
        context = ExecutionContext(collection_variables={"name": "John", "age": "30"})
        resolver = VariableResolver(context)

        body = Body(mode="raw", raw='{"name": "{{name}}", "age": {{age}}}')
        result = resolver.resolve_body(body)
        expected = {"name": "John", "age": 30}
        assert result == expected

    def test_resolve_body_urlencoded(self):
        """Test body resolution with urlencoded form."""
        context = ExecutionContext(
            collection_variables={"username": "john", "password": "secret"}
        )
        resolver = VariableResolver(context)

        body = Body(
            mode="urlencoded",
            urlencoded=[
                FormParameter("username", "{{username}}"),
                FormParameter("password", "{{password}}"),
                FormParameter("disabled", "value", disabled=True),
            ],
        )

        result = resolver.resolve_body(body)
        expected = {"username": "john", "password": "secret"}
        assert result == expected

    def test_resolve_body_formdata(self):
        """Test body resolution with form-data."""
        context = ExecutionContext(
            collection_variables={"field1": "value1", "filename": "test.txt"}
        )
        resolver = VariableResolver(context)

        body = Body(
            mode="formdata",
            formdata=[
                FormParameter("field1", "{{field1}}", type="text"),
                FormParameter("file", "{{filename}}", type="file"),
                FormParameter("disabled", "value", disabled=True),
            ],
        )

        result = resolver.resolve_body(body)
        expected = [("field1", "value1", "text"), ("file", "test.txt", "file")]
        assert result == expected

    def test_resolve_body_graphql(self):
        """Test body resolution with GraphQL."""
        context = ExecutionContext(collection_variables={"userId": "123"})
        resolver = VariableResolver(context)

        body = Body(
            mode="graphql", raw='{"query": "{ user(id: {{userId}}) { name } }"}'
        )

        result = resolver.resolve_body(body)
        expected = {"query": "{ user(id: 123) { name } }"}
        assert result == expected

    def test_resolve_body_file(self):
        """Test body resolution with file mode."""
        context = ExecutionContext(
            collection_variables={"filepath": "/path/to/file.txt"}
        )
        resolver = VariableResolver(context)

        body = Body(mode="file", file={"src": "{{filepath}}"})
        result = resolver.resolve_body(body)
        assert result == "/path/to/file.txt"

    def test_resolve_body_binary(self):
        """Test body resolution with binary mode."""
        context = ExecutionContext(collection_variables={"data": "binary data"})
        resolver = VariableResolver(context)

        body = Body(mode="binary", raw="{{data}}")
        result = resolver.resolve_body(body)
        assert result == "binary data"

    def test_resolve_body_disabled(self):
        """Test body resolution with disabled body."""
        context = ExecutionContext()
        resolver = VariableResolver(context)

        body = Body(mode="raw", raw="test", disabled=True)
        result = resolver.resolve_body(body)
        assert result is None

    def test_resolve_body_none(self):
        """Test body resolution with None body."""
        context = ExecutionContext()
        resolver = VariableResolver(context)

        result = resolver.resolve_body(None)
        assert result is None

    def test_resolve_auth_basic(self):
        """Test basic auth resolution."""
        context = ExecutionContext(
            collection_variables={"username": "john", "password": "secret"}
        )
        resolver = VariableResolver(context)

        auth = Auth(
            "basic",
            [
                AuthParameter("username", "{{username}}"),
                AuthParameter("password", "{{password}}"),
            ],
        )

        result = resolver.resolve_auth(auth)
        expected = {
            "type": "basic",
            "parameters": {"username": "john", "password": "secret"},
        }
        assert result == expected

    def test_resolve_auth_bearer(self):
        """Test bearer auth resolution."""
        context = ExecutionContext(collection_variables={"token": "abc123"})
        resolver = VariableResolver(context)

        auth = Auth("bearer", [AuthParameter("token", "{{token}}")])
        result = resolver.resolve_auth(auth)
        expected = {"type": "bearer", "parameters": {"token": "abc123"}}
        assert result == expected

    def test_resolve_auth_apikey(self):
        """Test API key auth resolution."""
        context = ExecutionContext(
            collection_variables={"api_key": "secret-key", "key_name": "X-API-Key"}
        )
        resolver = VariableResolver(context)

        auth = Auth(
            "apikey",
            [
                AuthParameter("key", "{{key_name}}"),
                AuthParameter("value", "{{api_key}}"),
                AuthParameter("in", "header"),
            ],
        )

        result = resolver.resolve_auth(auth)
        expected = {
            "type": "apikey",
            "parameters": {"key": "X-API-Key", "value": "secret-key", "in": "header"},
        }
        assert result == expected

    def test_resolve_auth_none(self):
        """Test auth resolution with None auth."""
        context = ExecutionContext()
        resolver = VariableResolver(context)

        result = resolver.resolve_auth(None)
        assert result is None

    def test_resolve_dict_values(self):
        """Test dictionary value resolution."""
        context = ExecutionContext(
            collection_variables={"name": "John", "age": "30", "city": "New York"}
        )
        resolver = VariableResolver(context)

        data = {
            "user": "{{name}}",
            "details": {"age": "{{age}}", "location": "{{city}}"},
            "tags": ["user-{{name}}", "age-{{age}}"],
        }

        result = resolver.resolve_dict_values(data)
        expected = {
            "user": "John",
            "details": {"age": "30", "location": "New York"},
            "tags": ["user-John", "age-30"],
        }
        assert result == expected

    def test_resolve_list_values(self):
        """Test list value resolution."""
        context = ExecutionContext(
            collection_variables={"item1": "first", "item2": "second"}
        )
        resolver = VariableResolver(context)

        data = [
            "{{item1}}",
            {"name": "{{item2}}"},
            ["nested-{{item1}}", "nested-{{item2}}"],
        ]

        result = resolver.resolve_list_values(data)
        expected = ["first", {"name": "second"}, ["nested-first", "nested-second"]]
        assert result == expected

    def test_resolve_string_max_depth_custom(self):
        """Test custom max depth for recursion protection."""
        context = ExecutionContext(
            collection_variables={
                "var1": "{{var2}}",
                "var2": "{{var3}}",
                "var3": "{{var4}}",
                "var4": "final",
            }
        )
        resolver = VariableResolver(context)

        # Should work with sufficient depth
        result = resolver.resolve_string("{{var1}}", max_depth=5)
        assert result == "final"

        # Should fail with insufficient depth
        with pytest.raises(VariableResolutionError):
            resolver.resolve_string("{{var1}}", max_depth=2)

    def test_resolve_complex_json_body(self):
        """Test resolution of complex JSON body with nested variables."""
        context = ExecutionContext(
            collection_variables={
                "user_id": "123",
                "user_name": "John Doe",
                "user_email": "john@example.com",
                "role": "admin",
            }
        )
        resolver = VariableResolver(context)

        json_body = """
        {
            "user": {
                "id": "{{user_id}}",
                "name": "{{user_name}}",
                "email": "{{user_email}}",
                "profile": {
                    "role": "{{role}}",
                    "active": true
                }
            },
            "metadata": {
                "created_by": "{{user_name}}",
                "timestamp": "2023-01-01"
            }
        }
        """

        body = Body(mode="raw", raw=json_body)
        result = resolver.resolve_body(body)

        # Should be parsed as JSON
        assert isinstance(result, dict)
        assert result["user"]["id"] == "123"
        assert result["user"]["name"] == "John Doe"
        assert result["user"]["email"] == "john@example.com"
        assert result["user"]["profile"]["role"] == "admin"
        assert result["metadata"]["created_by"] == "John Doe"

    def test_resolve_malformed_json_body(self):
        """Test resolution of malformed JSON body."""
        context = ExecutionContext(collection_variables={"name": "John"})
        resolver = VariableResolver(context)

        # Malformed JSON should return as string
        body = Body(mode="raw", raw='{"name": "{{name}}", invalid}')
        result = resolver.resolve_body(body)
        assert result == '{"name": "John", invalid}'
        assert isinstance(result, str)

    def test_edge_cases(self):
        """Test various edge cases."""
        context = ExecutionContext(
            collection_variables={
                "empty": "",
                "null": None,
                "zero": "0",
                "false": "false",
            }
        )
        resolver = VariableResolver(context)

        # Empty variable
        result = resolver.resolve_string("{{empty}}")
        assert result == ""  # Empty string stays empty

        # Null variable
        result = resolver.resolve_string("{{null}}")
        assert result == "None"  # None gets converted to string

        # Zero value
        result = resolver.resolve_string("{{zero}}")
        assert result == "0"

        # False value
        result = resolver.resolve_string("{{false}}")
        assert result == "false"

    def test_variable_in_variable_name(self):
        """Test variables within variable names with recursive resolution."""
        context = ExecutionContext(
            collection_variables={"var": "test", "test": "value"}
        )
        resolver = VariableResolver(context)

        # This resolves {{var}} to "test", then {{test}} to "value", leaving {value}
        result = resolver.resolve_string("{{{{{var}}}}}")
        assert result == "{value}"

        # Test a case that should actually fail - missing variable
        with pytest.raises(VariableResolutionError):
            resolver.resolve_string("{{missing_variable}}")

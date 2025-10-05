"""Tests for RequestExtensions class."""

import pytest
import json
from unittest.mock import Mock

from python_postman.execution.extensions import RequestExtensions
from python_postman.execution.context import ExecutionContext
from python_postman.models.request import Request
from python_postman.models.url import Url, QueryParam
from python_postman.models.header import Header
from python_postman.models.body import Body, FormParameter, BodyMode
from python_postman.models.auth import Auth, AuthParameter


class TestRequestExtensions:
    """Test RequestExtensions functionality."""

    def test_init_empty(self):
        """Test initialization with no parameters."""
        extensions = RequestExtensions()

        assert extensions.url_substitutions == {}
        assert extensions.header_substitutions == {}
        assert extensions.header_extensions == {}
        assert extensions.param_substitutions == {}
        assert extensions.param_extensions == {}
        assert extensions.body_substitutions == {}
        assert extensions.body_extensions == {}
        assert extensions.auth_substitutions == {}
        assert not extensions.has_modifications()

    def test_init_with_parameters(self):
        """Test initialization with parameters."""
        extensions = RequestExtensions(
            url_substitutions={"host": "api.example.com"},
            header_extensions={"X-API-Key": "secret"},
            param_extensions={"version": "v2"},
            body_substitutions={"name": "John"},
            auth_substitutions={"token": "new-token"},
        )

        assert extensions.url_substitutions == {"host": "api.example.com"}
        assert extensions.header_extensions == {"X-API-Key": "secret"}
        assert extensions.param_extensions == {"version": "v2"}
        assert extensions.body_substitutions == {"name": "John"}
        assert extensions.auth_substitutions == {"token": "new-token"}
        assert extensions.has_modifications()

    def test_apply_url_substitutions(self):
        """Test URL component substitutions."""
        # Create original URL
        url = Url(
            protocol="http",
            host=["localhost"],
            port="8080",
            path=["api", "v1", "users"],
            hash="section1",
        )

        # Create request
        request = Request(name="Test", method="GET", url=url)

        # Create extensions
        extensions = RequestExtensions(
            url_substitutions={
                "protocol": "https",
                "host": "api.example.com",
                "port": "443",
                "path": "api/v2/users",
                "hash": "section2",
            }
        )

        # Create context
        context = ExecutionContext()

        # Apply extensions
        modified_request = extensions.apply_to_request(request, context)

        # Verify modifications
        assert modified_request.url.protocol == "https"
        assert modified_request.url.host == ["api.example.com"]
        assert modified_request.url.port == "443"
        assert modified_request.url.path == ["api", "v2", "users"]
        assert modified_request.url.hash == "section2"

        # Verify original is unchanged
        assert request.url.protocol == "http"
        assert request.url.host == ["localhost"]

    def test_apply_url_substitutions_with_variables(self):
        """Test URL substitutions with variable resolution."""
        url = Url(host=["localhost"], path=["api"])
        request = Request(name="Test", method="GET", url=url)

        extensions = RequestExtensions(
            url_substitutions={"host": "{{base_url}}", "path": "{{api_path}}/users"}
        )

        context = ExecutionContext(
            collection_variables={"base_url": "api.example.com", "api_path": "v2"}
        )

        modified_request = extensions.apply_to_request(request, context)

        assert modified_request.url.host == ["api.example.com"]
        assert modified_request.url.path == ["v2", "users"]

    def test_apply_query_parameter_substitutions(self):
        """Test query parameter substitutions."""
        url = Url(
            host=["api.example.com"],
            query=[
                QueryParam(key="version", value="v1"),
                QueryParam(key="format", value="json"),
            ],
        )
        request = Request(name="Test", method="GET", url=url)

        extensions = RequestExtensions(
            param_substitutions={"version": "v2", "format": "xml"}
        )

        context = ExecutionContext()
        modified_request = extensions.apply_to_request(request, context)

        # Find parameters by key
        version_param = next(
            p for p in modified_request.url.query if p.key == "version"
        )
        format_param = next(p for p in modified_request.url.query if p.key == "format")

        assert version_param.value == "v2"
        assert format_param.value == "xml"

    def test_apply_query_parameter_extensions(self):
        """Test query parameter extensions (adding new parameters)."""
        url = Url(
            host=["api.example.com"], query=[QueryParam(key="version", value="v1")]
        )
        request = Request(name="Test", method="GET", url=url)

        extensions = RequestExtensions(
            param_extensions={"api_key": "secret123", "format": "json"}
        )

        context = ExecutionContext()
        modified_request = extensions.apply_to_request(request, context)

        # Should have original + new parameters
        assert len(modified_request.url.query) == 3

        param_dict = {p.key: p.value for p in modified_request.url.query}
        assert param_dict["version"] == "v1"  # Original
        assert param_dict["api_key"] == "secret123"  # New
        assert param_dict["format"] == "json"  # New

    def test_apply_header_substitutions(self):
        """Test header substitutions."""
        headers = [
            Header(key="Content-Type", value="application/json"),
            Header(key="Authorization", value="Bearer old-token"),
        ]
        request = Request(
            name="Test",
            method="POST",
            url=Url(host=["api.example.com"]),
            headers=headers,
        )

        extensions = RequestExtensions(
            header_substitutions={
                "Content-Type": "application/xml",
                "authorization": "Bearer new-token",  # Test case-insensitive
            }
        )

        context = ExecutionContext()
        modified_request = extensions.apply_to_request(request, context)

        # Find headers by key (case-insensitive)
        content_type = next(
            h for h in modified_request.headers if h.key.lower() == "content-type"
        )
        auth_header = next(
            h for h in modified_request.headers if h.key.lower() == "authorization"
        )

        assert content_type.value == "application/xml"
        assert auth_header.value == "Bearer new-token"

    def test_apply_header_extensions(self):
        """Test header extensions (adding new headers)."""
        headers = [Header(key="Content-Type", value="application/json")]
        request = Request(
            name="Test",
            method="POST",
            url=Url(host=["api.example.com"]),
            headers=headers,
        )

        extensions = RequestExtensions(
            header_extensions={
                "X-API-Key": "secret123",
                "X-Request-ID": "{{request_id}}",
            }
        )

        context = ExecutionContext(collection_variables={"request_id": "req-456"})
        modified_request = extensions.apply_to_request(request, context)

        # Should have original + new headers
        assert len(modified_request.headers) == 3

        header_dict = {h.key: h.value for h in modified_request.headers}
        assert header_dict["Content-Type"] == "application/json"  # Original
        assert header_dict["X-API-Key"] == "secret123"  # New
        assert header_dict["X-Request-ID"] == "req-456"  # New with variable

    def test_apply_raw_body_substitutions(self):
        """Test raw body substitutions."""
        body = Body(mode="raw", raw='{"name": "{{name}}", "age": {{age}}}')
        request = Request(
            name="Test", method="POST", url=Url(host=["api.example.com"]), body=body
        )

        extensions = RequestExtensions(
            body_substitutions={"name": "John Doe", "age": "25"}
        )

        context = ExecutionContext(collection_variables={"name": "Original Name"})
        modified_request = extensions.apply_to_request(request, context)

        expected_content = '{"name": "John Doe", "age": 25}'
        assert modified_request.body.raw == expected_content

    def test_apply_raw_body_json_extensions(self):
        """Test raw body JSON extensions."""
        body = Body(
            mode="raw",
            raw='{"name": "John", "age": 30}',
            options={"raw": {"language": "json"}},
        )
        request = Request(
            name="Test", method="POST", url=Url(host=["api.example.com"]), body=body
        )

        extensions = RequestExtensions(
            body_extensions={"email": "john@example.com", "active": "true"}
        )

        context = ExecutionContext()
        modified_request = extensions.apply_to_request(request, context)

        # Parse the modified JSON
        modified_json = json.loads(modified_request.body.raw)
        assert modified_json["name"] == "John"  # Original
        assert modified_json["age"] == 30  # Original
        assert modified_json["email"] == "john@example.com"  # New
        assert modified_json["active"] == True  # New (parsed as boolean)

    def test_apply_urlencoded_body_substitutions(self):
        """Test urlencoded body substitutions."""
        form_params = [
            FormParameter(key="username", value="olduser"),
            FormParameter(key="password", value="oldpass"),
        ]
        body = Body(mode="urlencoded", urlencoded=form_params)
        request = Request(
            name="Test", method="POST", url=Url(host=["api.example.com"]), body=body
        )

        extensions = RequestExtensions(
            body_substitutions={"username": "newuser", "password": "{{new_password}}"}
        )

        context = ExecutionContext(collection_variables={"new_password": "secret123"})
        modified_request = extensions.apply_to_request(request, context)

        param_dict = {p.key: p.value for p in modified_request.body.urlencoded}
        assert param_dict["username"] == "newuser"
        assert param_dict["password"] == "secret123"

    def test_apply_urlencoded_body_extensions(self):
        """Test urlencoded body extensions."""
        form_params = [FormParameter(key="username", value="user")]
        body = Body(mode="urlencoded", urlencoded=form_params)
        request = Request(
            name="Test", method="POST", url=Url(host=["api.example.com"]), body=body
        )

        extensions = RequestExtensions(
            body_extensions={"email": "user@example.com", "active": "true"}
        )

        context = ExecutionContext()
        modified_request = extensions.apply_to_request(request, context)

        # Should have original + new parameters
        assert len(modified_request.body.urlencoded) == 3

        param_dict = {p.key: p.value for p in modified_request.body.urlencoded}
        assert param_dict["username"] == "user"  # Original
        assert param_dict["email"] == "user@example.com"  # New
        assert param_dict["active"] == "true"  # New

    def test_apply_formdata_body_extensions(self):
        """Test formdata body extensions."""
        form_params = [FormParameter(key="name", value="John")]
        body = Body(mode="formdata", formdata=form_params)
        request = Request(
            name="Test", method="POST", url=Url(host=["api.example.com"]), body=body
        )

        extensions = RequestExtensions(
            body_extensions={"email": "john@example.com", "file": "document.pdf"}
        )

        context = ExecutionContext()
        modified_request = extensions.apply_to_request(request, context)

        # Should have original + new parameters
        assert len(modified_request.body.formdata) == 3

        param_dict = {p.key: p.value for p in modified_request.body.formdata}
        assert param_dict["name"] == "John"  # Original
        assert param_dict["email"] == "john@example.com"  # New
        assert param_dict["file"] == "document.pdf"  # New

    def test_apply_graphql_body_extensions(self):
        """Test GraphQL body extensions."""
        graphql_body = {"query": "query { user { name } }", "variables": {"id": 1}}
        body = Body(mode="graphql", raw=json.dumps(graphql_body))
        request = Request(
            name="Test", method="POST", url=Url(host=["api.example.com"]), body=body
        )

        extensions = RequestExtensions(
            body_extensions={
                "operationName": "GetUser",
                "variables": '{"id": 2, "includeEmail": true}',
            }
        )

        context = ExecutionContext()
        modified_request = extensions.apply_to_request(request, context)

        # Parse the modified GraphQL body
        modified_graphql = json.loads(modified_request.body.raw)
        assert modified_graphql["query"] == "query { user { name } }"  # Original
        assert modified_graphql["operationName"] == "GetUser"  # New
        # Variables should be parsed as JSON
        assert modified_graphql["variables"]["id"] == 2
        assert modified_graphql["variables"]["includeEmail"] is True

    def test_apply_auth_substitutions(self):
        """Test authentication substitutions."""
        auth_params = [
            AuthParameter(key="token", value="old-token"),
            AuthParameter(key="username", value="olduser"),
        ]
        auth = Auth(type="bearer", parameters=auth_params)
        request = Request(
            name="Test", method="GET", url=Url(host=["api.example.com"]), auth=auth
        )

        extensions = RequestExtensions(
            auth_substitutions={"token": "{{new_token}}", "username": "newuser"}
        )

        context = ExecutionContext(
            collection_variables={"new_token": "secret-token-123"}
        )
        modified_request = extensions.apply_to_request(request, context)

        param_dict = {p.key: p.value for p in modified_request.auth.parameters}
        assert param_dict["token"] == "secret-token-123"
        assert param_dict["username"] == "newuser"

    def test_no_modifications_when_no_extensions(self):
        """Test that request is unchanged when no extensions are applied."""
        url = Url(host=["api.example.com"], path=["users"])
        headers = [Header(key="Content-Type", value="application/json")]
        request = Request(name="Test", method="GET", url=url, headers=headers)

        extensions = RequestExtensions()  # No extensions
        context = ExecutionContext()

        modified_request = extensions.apply_to_request(request, context)

        # Should be a deep copy but with same values
        assert modified_request is not request  # Different objects
        assert modified_request.url.host == request.url.host
        assert modified_request.headers[0].key == request.headers[0].key
        assert modified_request.headers[0].value == request.headers[0].value

    def test_original_request_unchanged(self):
        """Test that original request is not modified."""
        url = Url(host=["localhost"])
        request = Request(name="Test", method="GET", url=url)

        extensions = RequestExtensions(url_substitutions={"host": "api.example.com"})

        context = ExecutionContext()
        modified_request = extensions.apply_to_request(request, context)

        # Original should be unchanged
        assert request.url.host == ["localhost"]
        # Modified should be changed
        assert modified_request.url.host == ["api.example.com"]

    def test_complex_combined_extensions(self):
        """Test applying multiple types of extensions together."""
        # Create a complex request
        url = Url(
            host=["localhost"],
            path=["api", "v1"],
            query=[QueryParam(key="format", value="json")],
        )
        headers = [Header(key="Content-Type", value="application/json")]
        body = Body(mode="raw", raw='{"name": "{{name}}"}')
        auth = Auth(
            type="bearer", parameters=[AuthParameter(key="token", value="old-token")]
        )

        request = Request(
            name="Complex Test",
            method="POST",
            url=url,
            headers=headers,
            body=body,
            auth=auth,
        )

        # Create comprehensive extensions
        extensions = RequestExtensions(
            url_substitutions={"host": "{{api_host}}"},
            param_extensions={"version": "{{api_version}}"},
            header_extensions={"X-API-Key": "{{api_key}}"},
            body_substitutions={"name": "{{user_name}}"},
            auth_substitutions={"token": "{{auth_token}}"},
        )

        context = ExecutionContext(
            collection_variables={
                "api_host": "api.example.com",
                "api_version": "v2",
                "api_key": "secret123",
                "user_name": "John Doe",
                "auth_token": "bearer-token-456",
            }
        )

        modified_request = extensions.apply_to_request(request, context)

        # Verify all modifications
        assert modified_request.url.host == ["api.example.com"]

        # Check new query parameter
        version_param = next(
            p for p in modified_request.url.query if p.key == "version"
        )
        assert version_param.value == "v2"

        # Check new header
        api_key_header = next(
            h for h in modified_request.headers if h.key == "X-API-Key"
        )
        assert api_key_header.value == "secret123"

        # Check body substitution
        assert '"name": "John Doe"' in modified_request.body.raw

        # Check auth substitution
        token_param = next(
            p for p in modified_request.auth.parameters if p.key == "token"
        )
        assert token_param.value == "bearer-token-456"

    def test_repr(self):
        """Test string representation."""
        extensions = RequestExtensions(
            url_substitutions={"host": "example.com"},
            header_extensions={"X-Key": "value"},
            param_extensions={"v": "1"},
        )

        repr_str = repr(extensions)
        assert "RequestExtensions" in repr_str
        assert "url_subs=1" in repr_str
        assert "header_exts=1" in repr_str
        assert "param_exts=1" in repr_str

    def test_has_modifications(self):
        """Test has_modifications method."""
        # Empty extensions
        extensions = RequestExtensions()
        assert not extensions.has_modifications()

        # With URL substitutions
        extensions = RequestExtensions(url_substitutions={"host": "example.com"})
        assert extensions.has_modifications()

        # With header extensions
        extensions = RequestExtensions(header_extensions={"X-Key": "value"})
        assert extensions.has_modifications()

        # With multiple types
        extensions = RequestExtensions(
            param_extensions={"v": "1"}, body_substitutions={"name": "test"}
        )
        assert extensions.has_modifications()

    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        extensions = RequestExtensions()
        context = ExecutionContext()

        # Test with None body
        request = Request(
            name="Test", method="GET", url=Url(host=["api.example.com"]), body=None
        )
        modified_request = extensions.apply_to_request(request, context)
        assert modified_request.body is None

        # Test with None auth
        request = Request(
            name="Test", method="GET", url=Url(host=["api.example.com"]), auth=None
        )
        modified_request = extensions.apply_to_request(request, context)
        assert modified_request.auth is None

        # Test with empty headers list
        request = Request(
            name="Test", method="GET", url=Url(host=["api.example.com"]), headers=[]
        )
        modified_request = extensions.apply_to_request(request, context)
        assert modified_request.headers == []

    def test_variable_resolution_in_extensions(self):
        """Test that variables are properly resolved in all extension types."""
        extensions = RequestExtensions(
            url_substitutions={"host": "{{base_url}}"},
            header_extensions={"X-Token": "{{token}}"},
            param_extensions={"key": "{{api_key}}"},
            body_substitutions={"user": "testuser"},
            auth_substitutions={"token": "{{auth_token}}"},
        )

        context = ExecutionContext(
            collection_variables={
                "base_url": "api.example.com",
                "token": "header-token",
                "api_key": "param-key",
                "username": "testuser",
                "auth_token": "auth-token",
            }
        )

        # Create a request with all components
        url = Url(host=["localhost"], query=[QueryParam(key="existing", value="param")])
        headers = [Header(key="Content-Type", value="application/json")]
        body = Body(mode="raw", raw='{"user": "{{user}}"}')
        auth = Auth(type="bearer", parameters=[AuthParameter(key="token", value="old")])

        request = Request(
            name="Test", method="POST", url=url, headers=headers, body=body, auth=auth
        )

        modified_request = extensions.apply_to_request(request, context)

        # Verify all variables were resolved
        assert modified_request.url.host == ["api.example.com"]

        token_header = next(h for h in modified_request.headers if h.key == "X-Token")
        assert token_header.value == "header-token"

        key_param = next(p for p in modified_request.url.query if p.key == "key")
        assert key_param.value == "param-key"

        assert '"user": "testuser"' in modified_request.body.raw

        auth_param = next(
            p for p in modified_request.auth.parameters if p.key == "token"
        )
        assert auth_param.value == "auth-token"

"""Unit tests for AuthHandler class."""

import base64
import pytest
from python_postman.execution.auth_handler import AuthHandler
from python_postman.execution.context import ExecutionContext
from python_postman.execution.exceptions import AuthenticationError
from python_postman.models.auth import Auth, AuthParameter


class TestAuthHandler:
    """Test cases for AuthHandler class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = AuthHandler()
        self.context = ExecutionContext(
            collection_variables={"api_token": "collection_token", "username": "john"},
            environment_variables={"env_token": "env_token", "password": "secret"},
        )

    def test_apply_auth_no_auth(self):
        """Test apply_auth with no authentication."""
        result = self.handler.apply_auth(None, None, self.context)
        expected = {"headers": {}, "params": {}}
        assert result == expected

    def test_apply_auth_request_precedence(self):
        """Test that request-level auth takes precedence over collection-level auth."""
        request_auth = Auth(
            type="bearer", parameters=[AuthParameter("token", "request_token")]
        )
        collection_auth = Auth(
            type="basic",
            parameters=[
                AuthParameter("username", "user"),
                AuthParameter("password", "pass"),
            ],
        )

        result = self.handler.apply_auth(request_auth, collection_auth, self.context)

        # Should use bearer auth from request, not basic auth from collection
        assert "Authorization" in result["headers"]
        assert result["headers"]["Authorization"] == "Bearer request_token"

    def test_apply_auth_collection_fallback(self):
        """Test that collection-level auth is used when request-level auth is None."""
        collection_auth = Auth(
            type="bearer", parameters=[AuthParameter("token", "collection_token")]
        )

        result = self.handler.apply_auth(None, collection_auth, self.context)

        assert "Authorization" in result["headers"]
        assert result["headers"]["Authorization"] == "Bearer collection_token"

    def test_apply_auth_noauth_type(self):
        """Test apply_auth with noauth type."""
        auth = Auth(type="noauth")
        result = self.handler.apply_auth(auth, None, self.context)
        expected = {"headers": {}, "params": {}}
        assert result == expected

    def test_apply_auth_unsupported_type(self):
        """Test apply_auth with unsupported auth type."""
        auth = Auth(type="oauth1", parameters=[AuthParameter("consumer_key", "key")])
        result = self.handler.apply_auth(auth, None, self.context)
        # Should return empty but not fail
        expected = {"headers": {}, "params": {}}
        assert result == expected

    def test_apply_auth_bearer_success(self):
        """Test successful bearer auth application."""
        auth = Auth(type="bearer", parameters=[AuthParameter("token", "test_token")])
        result = self.handler.apply_auth(auth, None, self.context)

        assert result["headers"]["Authorization"] == "Bearer test_token"
        assert result["params"] == {}

    def test_apply_auth_basic_success(self):
        """Test successful basic auth application."""
        auth = Auth(
            type="basic",
            parameters=[
                AuthParameter("username", "user"),
                AuthParameter("password", "pass"),
            ],
        )
        result = self.handler.apply_auth(auth, None, self.context)

        expected_creds = base64.b64encode("user:pass".encode("utf-8")).decode("ascii")
        assert result["headers"]["Authorization"] == f"Basic {expected_creds}"
        assert result["params"] == {}

    def test_apply_auth_apikey_header_success(self):
        """Test successful API key auth application to headers."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "X-API-Key"),
                AuthParameter("value", "secret123"),
                AuthParameter("in", "header"),
            ],
        )
        result = self.handler.apply_auth(auth, None, self.context)

        assert result["headers"]["X-API-Key"] == "secret123"
        assert result["params"] == {}

    def test_apply_auth_apikey_query_success(self):
        """Test successful API key auth application to query params."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "api_key"),
                AuthParameter("value", "secret123"),
                AuthParameter("in", "query"),
            ],
        )
        result = self.handler.apply_auth(auth, None, self.context)

        assert result["headers"] == {}
        assert result["params"]["api_key"] == "secret123"

    def test_apply_auth_exception_handling(self):
        """Test that exceptions during auth processing are wrapped properly."""
        # Create auth with invalid bearer token (None)
        auth = Auth(type="bearer", parameters=[])

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.apply_auth(auth, None, self.context)

        assert "Bearer token is required" in str(exc_info.value)
        assert exc_info.value.auth_type == "bearer"


class TestProcessBearerAuth:
    """Test cases for process_bearer_auth method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = AuthHandler()
        self.context = ExecutionContext(
            collection_variables={"api_token": "collection_token"}
        )

    def test_process_bearer_auth_success(self):
        """Test successful bearer auth processing."""
        auth = Auth(type="bearer", parameters=[AuthParameter("token", "test_token")])
        result = self.handler.process_bearer_auth(auth, self.context)

        expected = {"Authorization": "Bearer test_token"}
        assert result == expected

    def test_process_bearer_auth_with_variables(self):
        """Test bearer auth processing with variable substitution."""
        auth = Auth(type="bearer", parameters=[AuthParameter("token", "{{api_token}}")])
        result = self.handler.process_bearer_auth(auth, self.context)

        expected = {"Authorization": "Bearer collection_token"}
        assert result == expected

    def test_process_bearer_auth_wrong_type(self):
        """Test bearer auth processing with wrong auth type."""
        auth = Auth(type="basic", parameters=[AuthParameter("username", "user")])

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_bearer_auth(auth, self.context)

        assert "Auth object is not bearer type" in str(exc_info.value)
        assert exc_info.value.auth_type == "basic"

    def test_process_bearer_auth_missing_token(self):
        """Test bearer auth processing with missing token."""
        auth = Auth(type="bearer", parameters=[])

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_bearer_auth(auth, self.context)

        assert "Bearer token is required but not found" in str(exc_info.value)
        assert exc_info.value.auth_type == "bearer"
        assert exc_info.value.auth_parameter == "token"

    def test_process_bearer_auth_empty_token(self):
        """Test bearer auth processing with empty token after resolution."""
        auth = Auth(type="bearer", parameters=[AuthParameter("token", "   ")])

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_bearer_auth(auth, self.context)

        assert "Bearer token cannot be empty" in str(exc_info.value)
        assert exc_info.value.auth_parameter == "token"

    def test_process_bearer_auth_variable_resolution_error(self):
        """Test bearer auth processing with variable resolution error."""
        auth = Auth(
            type="bearer", parameters=[AuthParameter("token", "{{missing_var}}")]
        )

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_bearer_auth(auth, self.context)

        assert "Failed to resolve variables in bearer token" in str(exc_info.value)
        assert exc_info.value.auth_parameter == "token"


class TestProcessBasicAuth:
    """Test cases for process_basic_auth method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = AuthHandler()
        self.context = ExecutionContext(
            collection_variables={"username": "john", "password": "secret"}
        )

    def test_process_basic_auth_success(self):
        """Test successful basic auth processing."""
        auth = Auth(
            type="basic",
            parameters=[
                AuthParameter("username", "user"),
                AuthParameter("password", "pass"),
            ],
        )
        result = self.handler.process_basic_auth(auth, self.context)

        expected_creds = base64.b64encode("user:pass".encode("utf-8")).decode("ascii")
        expected = {"Authorization": f"Basic {expected_creds}"}
        assert result == expected

    def test_process_basic_auth_with_variables(self):
        """Test basic auth processing with variable substitution."""
        auth = Auth(
            type="basic",
            parameters=[
                AuthParameter("username", "{{username}}"),
                AuthParameter("password", "{{password}}"),
            ],
        )
        result = self.handler.process_basic_auth(auth, self.context)

        expected_creds = base64.b64encode("john:secret".encode("utf-8")).decode("ascii")
        expected = {"Authorization": f"Basic {expected_creds}"}
        assert result == expected

    def test_process_basic_auth_username_only(self):
        """Test basic auth processing with username only."""
        auth = Auth(type="basic", parameters=[AuthParameter("username", "user")])
        result = self.handler.process_basic_auth(auth, self.context)

        expected_creds = base64.b64encode("user:".encode("utf-8")).decode("ascii")
        expected = {"Authorization": f"Basic {expected_creds}"}
        assert result == expected

    def test_process_basic_auth_password_only(self):
        """Test basic auth processing with password only."""
        auth = Auth(type="basic", parameters=[AuthParameter("password", "pass")])
        result = self.handler.process_basic_auth(auth, self.context)

        expected_creds = base64.b64encode(":pass".encode("utf-8")).decode("ascii")
        expected = {"Authorization": f"Basic {expected_creds}"}
        assert result == expected

    def test_process_basic_auth_empty_credentials(self):
        """Test basic auth processing with empty credentials."""
        auth = Auth(
            type="basic",
            parameters=[AuthParameter("username", ""), AuthParameter("password", "")],
        )
        result = self.handler.process_basic_auth(auth, self.context)

        expected_creds = base64.b64encode(":".encode("utf-8")).decode("ascii")
        expected = {"Authorization": f"Basic {expected_creds}"}
        assert result == expected

    def test_process_basic_auth_wrong_type(self):
        """Test basic auth processing with wrong auth type."""
        auth = Auth(type="bearer", parameters=[AuthParameter("token", "token")])

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_basic_auth(auth, self.context)

        assert "Auth object is not basic type" in str(exc_info.value)
        assert exc_info.value.auth_type == "bearer"

    def test_process_basic_auth_missing_credentials(self):
        """Test basic auth processing with missing credentials."""
        auth = Auth(type="basic", parameters=[])

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_basic_auth(auth, self.context)

        assert "Basic auth credentials are required but not found" in str(
            exc_info.value
        )
        assert exc_info.value.auth_type == "basic"

    def test_process_basic_auth_variable_resolution_error(self):
        """Test basic auth processing with variable resolution error."""
        auth = Auth(
            type="basic",
            parameters=[
                AuthParameter("username", "{{missing_var}}"),
                AuthParameter("password", "pass"),
            ],
        )

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_basic_auth(auth, self.context)

        assert "Failed to resolve variables in basic auth credentials" in str(
            exc_info.value
        )
        assert exc_info.value.auth_type == "basic"


class TestProcessApiKeyAuth:
    """Test cases for process_api_key_auth method."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = AuthHandler()
        self.context = ExecutionContext(
            collection_variables={"api_key": "secret123", "key_name": "X-API-Key"}
        )

    def test_process_api_key_auth_header_success(self):
        """Test successful API key auth processing for headers."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "X-API-Key"),
                AuthParameter("value", "secret123"),
                AuthParameter("in", "header"),
            ],
        )
        result = self.handler.process_api_key_auth(auth, self.context)

        expected = {"headers": {"X-API-Key": "secret123"}, "params": {}}
        assert result == expected

    def test_process_api_key_auth_query_success(self):
        """Test successful API key auth processing for query params."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "api_key"),
                AuthParameter("value", "secret123"),
                AuthParameter("in", "query"),
            ],
        )
        result = self.handler.process_api_key_auth(auth, self.context)

        expected = {"headers": {}, "params": {"api_key": "secret123"}}
        assert result == expected

    def test_process_api_key_auth_default_location(self):
        """Test API key auth processing with default location (header)."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "X-API-Key"),
                AuthParameter("value", "secret123"),
            ],
        )
        result = self.handler.process_api_key_auth(auth, self.context)

        expected = {"headers": {"X-API-Key": "secret123"}, "params": {}}
        assert result == expected

    def test_process_api_key_auth_with_variables(self):
        """Test API key auth processing with variable substitution."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "{{key_name}}"),
                AuthParameter("value", "{{api_key}}"),
                AuthParameter("in", "header"),
            ],
        )
        result = self.handler.process_api_key_auth(auth, self.context)

        expected = {"headers": {"X-API-Key": "secret123"}, "params": {}}
        assert result == expected

    def test_process_api_key_auth_case_insensitive_location(self):
        """Test API key auth processing with case insensitive location."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "api_key"),
                AuthParameter("value", "secret123"),
                AuthParameter("in", "QUERY"),
            ],
        )
        result = self.handler.process_api_key_auth(auth, self.context)

        expected = {"headers": {}, "params": {"api_key": "secret123"}}
        assert result == expected

    def test_process_api_key_auth_wrong_type(self):
        """Test API key auth processing with wrong auth type."""
        auth = Auth(type="bearer", parameters=[AuthParameter("token", "token")])

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_api_key_auth(auth, self.context)

        assert "Auth object is not API key type" in str(exc_info.value)
        assert exc_info.value.auth_type == "bearer"

    def test_process_api_key_auth_missing_config(self):
        """Test API key auth processing with missing configuration."""
        auth = Auth(type="apikey", parameters=[])

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_api_key_auth(auth, self.context)

        assert "API key configuration is required but not found" in str(exc_info.value)
        assert exc_info.value.auth_type == "apikey"

    def test_process_api_key_auth_empty_key(self):
        """Test API key auth processing with empty key name."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "   "),
                AuthParameter("value", "secret123"),
            ],
        )

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_api_key_auth(auth, self.context)

        assert "API key name cannot be empty" in str(exc_info.value)
        assert exc_info.value.auth_parameter == "key"

    def test_process_api_key_auth_empty_value(self):
        """Test API key auth processing with empty key value."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "X-API-Key"),
                AuthParameter("value", "   "),
            ],
        )

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_api_key_auth(auth, self.context)

        assert "API key value cannot be empty" in str(exc_info.value)
        assert exc_info.value.auth_parameter == "value"

    def test_process_api_key_auth_invalid_location(self):
        """Test API key auth processing with invalid location."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "X-API-Key"),
                AuthParameter("value", "secret123"),
                AuthParameter("in", "invalid"),
            ],
        )

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_api_key_auth(auth, self.context)

        assert "Invalid API key location 'invalid'" in str(exc_info.value)
        assert exc_info.value.auth_parameter == "in"

    def test_process_api_key_auth_variable_resolution_error(self):
        """Test API key auth processing with variable resolution error."""
        auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "{{missing_var}}"),
                AuthParameter("value", "secret123"),
            ],
        )

        with pytest.raises(AuthenticationError) as exc_info:
            self.handler.process_api_key_auth(auth, self.context)

        assert "Failed to resolve variables in API key" in str(exc_info.value)
        assert exc_info.value.auth_type == "apikey"


class TestAuthHandlerIntegration:
    """Integration tests for AuthHandler with various scenarios."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = AuthHandler()

    def test_complex_variable_resolution(self):
        """Test auth handler with complex variable resolution scenarios."""
        context = ExecutionContext(
            environment_variables={"base_token": "env_"},
            collection_variables={"token_suffix": "collection"},
            folder_variables={"api_key": "folder_key"},
            request_variables={"final_token": "{{base_token}}{{token_suffix}}"},
        )

        # Test bearer auth with nested variable resolution
        auth = Auth(
            type="bearer", parameters=[AuthParameter("token", "{{final_token}}")]
        )
        result = self.handler.process_bearer_auth(auth, context)

        assert result["Authorization"] == "Bearer env_collection"

    def test_auth_precedence_scenarios(self):
        """Test various auth precedence scenarios."""
        context = ExecutionContext()

        # Test request auth overrides collection auth
        request_auth = Auth(
            type="bearer", parameters=[AuthParameter("token", "request_token")]
        )
        collection_auth = Auth(
            type="basic",
            parameters=[
                AuthParameter("username", "user"),
                AuthParameter("password", "pass"),
            ],
        )

        result = self.handler.apply_auth(request_auth, collection_auth, context)
        assert "Bearer request_token" in result["headers"]["Authorization"]

        # Test collection auth used when no request auth
        result = self.handler.apply_auth(None, collection_auth, context)
        assert "Basic" in result["headers"]["Authorization"]

    def test_mixed_auth_types_in_collection(self):
        """Test handling different auth types at different levels."""
        context = ExecutionContext(
            collection_variables={"collection_token": "coll_123"},
            request_variables={"request_key": "req_456"},
        )

        # Collection uses bearer, request uses API key
        collection_auth = Auth(
            type="bearer", parameters=[AuthParameter("token", "{{collection_token}}")]
        )
        request_auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter("key", "X-Request-Key"),
                AuthParameter("value", "{{request_key}}"),
                AuthParameter("in", "header"),
            ],
        )

        result = self.handler.apply_auth(request_auth, collection_auth, context)

        # Should use request auth (API key), not collection auth (bearer)
        assert result["headers"]["X-Request-Key"] == "req_456"
        assert "Authorization" not in result["headers"]

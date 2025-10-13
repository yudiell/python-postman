"""Unit tests for enhanced type safety features."""

import pytest
from python_postman.models.request import Request
from python_postman.models.auth import Auth
from python_postman.models.url import Url
from python_postman.types import (
    HttpMethod,
    HttpMethodLiteral,
    HttpMethodType,
    AuthTypeEnum,
    AuthTypeLiteral,
    AuthTypeType,
)


class TestHttpMethodTypes:
    """Test cases for HTTP method type definitions."""

    def test_http_method_enum_values(self):
        """Test HttpMethod enum has all standard methods."""
        assert HttpMethod.GET.value == "GET"
        assert HttpMethod.POST.value == "POST"
        assert HttpMethod.PUT.value == "PUT"
        assert HttpMethod.PATCH.value == "PATCH"
        assert HttpMethod.DELETE.value == "DELETE"
        assert HttpMethod.HEAD.value == "HEAD"
        assert HttpMethod.OPTIONS.value == "OPTIONS"
        assert HttpMethod.TRACE.value == "TRACE"
        assert HttpMethod.CONNECT.value == "CONNECT"

    def test_http_method_enum_count(self):
        """Test HttpMethod enum has expected number of methods."""
        assert len(HttpMethod) == 9


class TestAuthTypeEnumTypes:
    """Test cases for authentication type definitions."""

    def test_auth_type_enum_values(self):
        """Test AuthTypeEnum has all authentication types."""
        assert AuthTypeEnum.BASIC.value == "basic"
        assert AuthTypeEnum.BEARER.value == "bearer"
        assert AuthTypeEnum.DIGEST.value == "digest"
        assert AuthTypeEnum.HAWK.value == "hawk"
        assert AuthTypeEnum.NOAUTH.value == "noauth"
        assert AuthTypeEnum.OAUTH1.value == "oauth1"
        assert AuthTypeEnum.OAUTH2.value == "oauth2"
        assert AuthTypeEnum.NTLM.value == "ntlm"
        assert AuthTypeEnum.APIKEY.value == "apikey"
        assert AuthTypeEnum.AWSV4.value == "awsv4"

    def test_auth_type_enum_count(self):
        """Test AuthTypeEnum has expected number of types."""
        assert len(AuthTypeEnum) == 10


class TestRequestMethodValidation:
    """Test cases for Request HTTP method validation."""

    def test_request_with_valid_method_uppercase(self):
        """Test Request accepts valid uppercase HTTP method."""
        url = Url("https://api.example.com/users")
        request = Request(name="Get Users", method="GET", url=url)
        assert request.method == "GET"

    def test_request_with_valid_method_lowercase(self):
        """Test Request accepts valid lowercase HTTP method."""
        url = Url("https://api.example.com/users")
        request = Request(name="Get Users", method="get", url=url)
        assert request.method == "get"

    def test_request_with_valid_method_mixed_case(self):
        """Test Request accepts valid mixed case HTTP method."""
        url = Url("https://api.example.com/users")
        request = Request(name="Get Users", method="Post", url=url)
        assert request.method == "Post"

    def test_request_with_all_standard_methods(self):
        """Test Request accepts all standard HTTP methods."""
        url = Url("https://api.example.com/users")
        methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT"]
        
        for method in methods:
            request = Request(name=f"{method} Request", method=method, url=url)
            assert request.method == method

    def test_request_with_invalid_method(self):
        """Test Request rejects invalid HTTP method."""
        url = Url("https://api.example.com/users")
        with pytest.raises(ValueError, match="Invalid HTTP method 'INVALID'"):
            Request(name="Invalid Request", method="INVALID", url=url)

    def test_request_with_empty_method(self):
        """Test Request rejects empty HTTP method."""
        url = Url("https://api.example.com/users")
        with pytest.raises(ValueError, match="HTTP method must be a non-empty string"):
            Request(name="Empty Method", method="", url=url)

    def test_request_with_none_method(self):
        """Test Request rejects None as HTTP method."""
        url = Url("https://api.example.com/users")
        with pytest.raises(ValueError, match="HTTP method must be a non-empty string"):
            Request(name="None Method", method=None, url=url)

    def test_request_with_non_string_method(self):
        """Test Request rejects non-string HTTP method."""
        url = Url("https://api.example.com/users")
        with pytest.raises(ValueError, match="HTTP method must be a non-empty string"):
            Request(name="Numeric Method", method=123, url=url)

    def test_request_validation_error_message_includes_valid_methods(self):
        """Test validation error message lists valid HTTP methods."""
        url = Url("https://api.example.com/users")
        with pytest.raises(ValueError) as exc_info:
            Request(name="Invalid", method="INVALID", url=url)
        
        error_message = str(exc_info.value)
        assert "GET" in error_message
        assert "POST" in error_message
        assert "PUT" in error_message
        assert "DELETE" in error_message


class TestAuthTypeValidation:
    """Test cases for Auth type validation."""

    def test_auth_with_valid_type_lowercase(self):
        """Test Auth accepts valid lowercase auth type."""
        auth = Auth(type="basic")
        assert auth.type == "basic"

    def test_auth_with_valid_type_uppercase(self):
        """Test Auth accepts valid uppercase auth type."""
        auth = Auth(type="BASIC")
        assert auth.type == "BASIC"

    def test_auth_with_all_standard_types(self):
        """Test Auth accepts all standard authentication types."""
        types = ["basic", "bearer", "digest", "hawk", "noauth", "oauth1", "oauth2", "ntlm", "apikey", "awsv4"]
        
        for auth_type in types:
            auth = Auth(type=auth_type)
            assert auth.type == auth_type

    def test_auth_with_invalid_type(self):
        """Test Auth rejects invalid authentication type."""
        with pytest.raises(ValueError, match="Invalid authentication type 'invalid'"):
            Auth(type="invalid")

    def test_auth_with_empty_type(self):
        """Test Auth rejects empty authentication type."""
        with pytest.raises(ValueError, match="Authentication type must be a non-empty string"):
            Auth(type="")

    def test_auth_with_none_type(self):
        """Test Auth rejects None as authentication type."""
        with pytest.raises(ValueError, match="Authentication type must be a non-empty string"):
            Auth(type=None)

    def test_auth_with_non_string_type(self):
        """Test Auth rejects non-string authentication type."""
        with pytest.raises(ValueError, match="Authentication type must be a non-empty string"):
            Auth(type=123)

    def test_auth_validation_error_message_includes_valid_types(self):
        """Test validation error message lists valid authentication types."""
        with pytest.raises(ValueError) as exc_info:
            Auth(type="invalid")
        
        error_message = str(exc_info.value)
        assert "basic" in error_message
        assert "bearer" in error_message
        assert "oauth1" in error_message
        assert "apikey" in error_message


class TestTypeHints:
    """Test cases for type hint usage (these are mainly for IDE/mypy, but we can test runtime behavior)."""

    def test_request_accepts_http_method_enum(self):
        """Test Request can be created with HttpMethod enum."""
        url = Url("https://api.example.com/users")
        # This tests that the enum value (which is a string) works
        request = Request(name="Get Users", method=HttpMethod.GET.value, url=url)
        assert request.method == "GET"

    def test_auth_accepts_auth_type_enum(self):
        """Test Auth can be created with AuthTypeEnum."""
        # This tests that the enum value (which is a string) works
        auth = Auth(type=AuthTypeEnum.BASIC.value)
        assert auth.type == "basic"

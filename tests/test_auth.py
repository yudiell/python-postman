"""Unit tests for Auth model."""

import pytest
from python_postman.models.auth import Auth, AuthParameter, AuthType


class TestAuthParameter:
    """Test cases for AuthParameter class."""

    def test_init_minimal(self):
        """Test AuthParameter initialization with minimal parameters."""
        param = AuthParameter(key="username")
        assert param.key == "username"
        assert param.value is None
        assert param.type == "string"

    def test_init_complete(self):
        """Test AuthParameter initialization with all parameters."""
        param = AuthParameter(key="token", value="abc123", type="secret")
        assert param.key == "token"
        assert param.value == "abc123"
        assert param.type == "secret"

    def test_from_dict(self):
        """Test creating AuthParameter from dictionary."""
        data = {"key": "username", "value": "john", "type": "string"}
        param = AuthParameter.from_dict(data)
        assert param.key == "username"
        assert param.value == "john"
        assert param.type == "string"

    def test_from_dict_minimal(self):
        """Test creating AuthParameter from minimal dictionary."""
        data = {"key": "token", "value": "abc123"}
        param = AuthParameter.from_dict(data)
        assert param.key == "token"
        assert param.value == "abc123"
        assert param.type == "string"  # default

    def test_to_dict(self):
        """Test converting AuthParameter to dictionary."""
        param = AuthParameter(key="password", value="secret", type="password")
        result = param.to_dict()
        expected = {"key": "password", "value": "secret", "type": "password"}
        assert result == expected

    def test_repr(self):
        """Test string representation."""
        param = AuthParameter(key="key", value="value", type="string")
        expected = "AuthParameter(key='key', value='value', type='string')"
        assert repr(param) == expected

    def test_equality(self):
        """Test equality comparison."""
        param1 = AuthParameter(key="test", value="value", type="string")
        param2 = AuthParameter(key="test", value="value", type="string")
        param3 = AuthParameter(key="test", value="different", type="string")

        assert param1 == param2
        assert param1 != param3
        assert param1 != "not an AuthParameter"


class TestAuth:
    """Test cases for Auth class."""

    def test_init_minimal(self):
        """Test Auth initialization with minimal parameters."""
        auth = Auth(type="basic")
        assert auth.type == "basic"
        assert auth.parameters == []

    def test_init_with_parameters(self):
        """Test Auth initialization with parameters."""
        params = [
            AuthParameter("username", "john"),
            AuthParameter("password", "secret"),
        ]
        auth = Auth(type="basic", parameters=params)
        assert auth.type == "basic"
        assert len(auth.parameters) == 2
        assert auth.parameters[0].key == "username"
        assert auth.parameters[1].key == "password"

    def test_get_auth_type_valid(self):
        """Test getting valid auth type as enum."""
        auth = Auth(type="basic")
        assert auth.get_auth_type() == AuthType.BASIC

        auth = Auth(type="BEARER")
        assert auth.get_auth_type() == AuthType.BEARER

    def test_get_auth_type_invalid(self):
        """Test getting invalid auth type defaults to NOAUTH."""
        auth = Auth(type="invalid")
        assert auth.get_auth_type() == AuthType.NOAUTH

        auth = Auth(type=None)
        assert auth.get_auth_type() == AuthType.NOAUTH

    def test_get_parameter_exists(self):
        """Test getting existing parameter."""
        params = [AuthParameter("username", "john")]
        auth = Auth(type="basic", parameters=params)
        assert auth.get_parameter("username") == "john"

    def test_get_parameter_not_exists(self):
        """Test getting non-existing parameter."""
        auth = Auth(type="basic")
        assert auth.get_parameter("username") is None

    def test_get_parameter_dict(self):
        """Test getting all parameters as dictionary."""
        params = [
            AuthParameter("username", "john"),
            AuthParameter("password", "secret"),
        ]
        auth = Auth(type="basic", parameters=params)
        result = auth.get_parameter_dict()
        expected = {"username": "john", "password": "secret"}
        assert result == expected

    def test_get_parameter_dict_empty(self):
        """Test getting parameter dictionary when no parameters."""
        auth = Auth(type="basic")
        result = auth.get_parameter_dict()
        assert result == {}

    def test_add_parameter_new(self):
        """Test adding new parameter."""
        auth = Auth(type="basic")
        auth.add_parameter("username", "john")
        assert len(auth.parameters) == 1
        assert auth.get_parameter("username") == "john"

    def test_add_parameter_update(self):
        """Test updating existing parameter."""
        params = [AuthParameter("username", "old")]
        auth = Auth(type="basic", parameters=params)
        auth.add_parameter("username", "new")
        assert len(auth.parameters) == 1
        assert auth.get_parameter("username") == "new"

    def test_remove_parameter_exists(self):
        """Test removing existing parameter."""
        params = [AuthParameter("username", "john")]
        auth = Auth(type="basic", parameters=params)
        result = auth.remove_parameter("username")
        assert result is True
        assert len(auth.parameters) == 0

    def test_remove_parameter_not_exists(self):
        """Test removing non-existing parameter."""
        auth = Auth(type="basic")
        result = auth.remove_parameter("username")
        assert result is False

    def test_is_basic_auth(self):
        """Test basic auth type checking."""
        auth = Auth(type="basic")
        assert auth.is_basic_auth() is True
        assert auth.is_bearer_auth() is False

    def test_is_bearer_auth(self):
        """Test bearer auth type checking."""
        auth = Auth(type="bearer")
        assert auth.is_bearer_auth() is True
        assert auth.is_basic_auth() is False

    def test_is_api_key_auth(self):
        """Test API key auth type checking."""
        auth = Auth(type="apikey")
        assert auth.is_api_key_auth() is True
        assert auth.is_basic_auth() is False

    def test_is_oauth1_auth(self):
        """Test OAuth 1.0 auth type checking."""
        auth = Auth(type="oauth1")
        assert auth.is_oauth1_auth() is True
        assert auth.is_oauth2_auth() is False

    def test_is_oauth2_auth(self):
        """Test OAuth 2.0 auth type checking."""
        auth = Auth(type="oauth2")
        assert auth.is_oauth2_auth() is True
        assert auth.is_oauth1_auth() is False

    def test_get_basic_credentials_valid(self):
        """Test getting basic auth credentials."""
        params = [
            AuthParameter("username", "john"),
            AuthParameter("password", "secret"),
        ]
        auth = Auth(type="basic", parameters=params)
        result = auth.get_basic_credentials()
        expected = {"username": "john", "password": "secret"}
        assert result == expected

    def test_get_basic_credentials_partial(self):
        """Test getting basic auth credentials with only username."""
        params = [AuthParameter("username", "john")]
        auth = Auth(type="basic", parameters=params)
        result = auth.get_basic_credentials()
        expected = {"username": "john", "password": ""}
        assert result == expected

    def test_get_basic_credentials_wrong_type(self):
        """Test getting basic auth credentials for non-basic auth."""
        auth = Auth(type="bearer")
        result = auth.get_basic_credentials()
        assert result is None

    def test_get_basic_credentials_no_params(self):
        """Test getting basic auth credentials with no parameters."""
        auth = Auth(type="basic")
        result = auth.get_basic_credentials()
        assert result is None

    def test_get_bearer_token_valid(self):
        """Test getting bearer token."""
        params = [AuthParameter("token", "abc123")]
        auth = Auth(type="bearer", parameters=params)
        result = auth.get_bearer_token()
        assert result == "abc123"

    def test_get_bearer_token_wrong_type(self):
        """Test getting bearer token for non-bearer auth."""
        auth = Auth(type="basic")
        result = auth.get_bearer_token()
        assert result is None

    def test_get_bearer_token_no_token(self):
        """Test getting bearer token with no token parameter."""
        auth = Auth(type="bearer")
        result = auth.get_bearer_token()
        assert result is None

    def test_get_api_key_config_valid(self):
        """Test getting API key configuration."""
        params = [
            AuthParameter("key", "X-API-Key"),
            AuthParameter("value", "secret123"),
            AuthParameter("in", "header"),
        ]
        auth = Auth(type="apikey", parameters=params)
        result = auth.get_api_key_config()
        expected = {"key": "X-API-Key", "value": "secret123", "in": "header"}
        assert result == expected

    def test_get_api_key_config_minimal(self):
        """Test getting API key configuration with minimal parameters."""
        params = [AuthParameter("key", "X-API-Key")]
        auth = Auth(type="apikey", parameters=params)
        result = auth.get_api_key_config()
        expected = {"key": "X-API-Key", "value": "", "in": "header"}
        assert result == expected

    def test_get_api_key_config_wrong_type(self):
        """Test getting API key config for non-apikey auth."""
        auth = Auth(type="basic")
        result = auth.get_api_key_config()
        assert result is None

    def test_validate_success_basic(self):
        """Test successful validation for basic auth."""
        params = [AuthParameter("username", "john")]
        auth = Auth(type="basic", parameters=params)
        assert auth.validate() is True

    def test_validate_success_bearer(self):
        """Test successful validation for bearer auth."""
        params = [AuthParameter("token", "abc123")]
        auth = Auth(type="bearer", parameters=params)
        assert auth.validate() is True

    def test_validate_success_apikey(self):
        """Test successful validation for API key auth."""
        params = [AuthParameter("key", "X-API-Key"), AuthParameter("value", "secret")]
        auth = Auth(type="apikey", parameters=params)
        assert auth.validate() is True

    def test_validate_empty_type_fails(self):
        """Test validation fails with empty type."""
        auth = Auth(type="")
        with pytest.raises(ValueError, match="Auth type is required"):
            auth.validate()

    def test_validate_none_type_fails(self):
        """Test validation fails with None type."""
        auth = Auth(type=None)
        with pytest.raises(ValueError, match="Auth type is required"):
            auth.validate()

    def test_validate_non_string_type_fails(self):
        """Test validation fails with non-string type."""
        auth = Auth(type=123)
        with pytest.raises(ValueError, match="Auth type is required"):
            auth.validate()

    def test_validate_non_list_parameters_fails(self):
        """Test validation fails with non-list parameters."""
        auth = Auth(type="basic", parameters="not a list")
        with pytest.raises(ValueError, match="Auth parameters must be a list"):
            auth.validate()

    def test_validate_invalid_parameter_type_fails(self):
        """Test validation fails with invalid parameter type."""
        auth = Auth(type="basic", parameters=["not an AuthParameter"])
        with pytest.raises(
            ValueError, match="All auth parameters must be AuthParameter instances"
        ):
            auth.validate()

    def test_validate_empty_parameter_key_fails(self):
        """Test validation fails with empty parameter key."""
        params = [AuthParameter("")]
        auth = Auth(type="basic", parameters=params)
        with pytest.raises(ValueError, match="Auth parameter key is required"):
            auth.validate()

    def test_validate_basic_missing_credentials_fails(self):
        """Test validation fails for basic auth without credentials."""
        auth = Auth(type="basic", parameters=[AuthParameter("other", "value")])
        with pytest.raises(
            ValueError, match="Basic auth requires username and/or password"
        ):
            auth.validate()

    def test_validate_bearer_missing_token_fails(self):
        """Test validation fails for bearer auth without token."""
        auth = Auth(type="bearer", parameters=[AuthParameter("other", "value")])
        with pytest.raises(ValueError, match="Bearer auth requires token parameter"):
            auth.validate()

    def test_validate_apikey_missing_required_fails(self):
        """Test validation fails for API key auth without required parameters."""
        auth = Auth(type="apikey", parameters=[AuthParameter("other", "value")])
        with pytest.raises(ValueError, match="API key auth requires parameters"):
            auth.validate()

    def test_from_dict_basic_list_format(self):
        """Test creating Auth from dictionary with list format."""
        data = {
            "type": "basic",
            "basic": [
                {"key": "username", "value": "john", "type": "string"},
                {"key": "password", "value": "secret", "type": "string"},
            ],
        }
        auth = Auth.from_dict(data)
        assert auth.type == "basic"
        assert len(auth.parameters) == 2
        assert auth.get_parameter("username") == "john"
        assert auth.get_parameter("password") == "secret"

    def test_from_dict_dict_format(self):
        """Test creating Auth from dictionary with dict format."""
        data = {"type": "basic", "basic": {"username": "john", "password": "secret"}}
        auth = Auth.from_dict(data)
        assert auth.type == "basic"
        assert len(auth.parameters) == 2
        assert auth.get_parameter("username") == "john"
        assert auth.get_parameter("password") == "secret"

    def test_from_dict_complex_dict_format(self):
        """Test creating Auth from dictionary with complex dict format."""
        data = {
            "type": "bearer",
            "bearer": {"token": {"value": "abc123", "type": "secret"}},
        }
        auth = Auth.from_dict(data)
        assert auth.type == "bearer"
        assert len(auth.parameters) == 1
        assert auth.get_parameter("token") == "abc123"

    def test_from_dict_minimal(self):
        """Test creating Auth from minimal dictionary."""
        data = {"type": "noauth"}
        auth = Auth.from_dict(data)
        assert auth.type == "noauth"
        assert len(auth.parameters) == 0

    def test_to_dict(self):
        """Test converting Auth to dictionary."""
        params = [
            AuthParameter("username", "john"),
            AuthParameter("password", "secret"),
        ]
        auth = Auth(type="basic", parameters=params)
        result = auth.to_dict()
        expected = {
            "type": "basic",
            "basic": [
                {"key": "username", "value": "john", "type": "string"},
                {"key": "password", "value": "secret", "type": "string"},
            ],
        }
        assert result == expected

    def test_to_dict_no_parameters(self):
        """Test converting Auth to dictionary with no parameters."""
        auth = Auth(type="noauth")
        result = auth.to_dict()
        expected = {"type": "noauth"}
        assert result == expected

    def test_repr(self):
        """Test string representation."""
        params = [AuthParameter("key", "value")]
        auth = Auth(type="basic", parameters=params)
        expected = f"Auth(type='basic', parameters={params!r})"
        assert repr(auth) == expected

    def test_equality(self):
        """Test equality comparison."""
        params1 = [AuthParameter("username", "john")]
        params2 = [AuthParameter("username", "john")]
        params3 = [AuthParameter("username", "jane")]

        auth1 = Auth(type="basic", parameters=params1)
        auth2 = Auth(type="basic", parameters=params2)
        auth3 = Auth(type="basic", parameters=params3)
        auth4 = Auth(type="bearer", parameters=params1)

        assert auth1 == auth2
        assert auth1 != auth3
        assert auth1 != auth4
        assert auth1 != "not an Auth object"


class TestAuthType:
    """Test cases for AuthType enum."""

    def test_enum_values(self):
        """Test AuthType enum values."""
        assert AuthType.BASIC.value == "basic"
        assert AuthType.BEARER.value == "bearer"
        assert AuthType.DIGEST.value == "digest"
        assert AuthType.HAWK.value == "hawk"
        assert AuthType.NOAUTH.value == "noauth"
        assert AuthType.OAUTH1.value == "oauth1"
        assert AuthType.OAUTH2.value == "oauth2"
        assert AuthType.NTLM.value == "ntlm"
        assert AuthType.APIKEY.value == "apikey"
        assert AuthType.AWSV4.value == "awsv4"

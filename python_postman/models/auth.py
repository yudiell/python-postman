"""Auth model for Postman collection authentication."""

from typing import Optional, Dict, Any, List
from enum import Enum


class AuthType(Enum):
    """Enumeration of authentication types."""

    BASIC = "basic"
    BEARER = "bearer"
    DIGEST = "digest"
    HAWK = "hawk"
    NOAUTH = "noauth"
    OAUTH1 = "oauth1"
    OAUTH2 = "oauth2"
    NTLM = "ntlm"
    APIKEY = "apikey"
    AWSV4 = "awsv4"


class AuthParameter:
    """Represents an authentication parameter with key, value, and type."""

    def __init__(self, key: str, value: Any = None, type: str = "string"):
        """
        Initialize AuthParameter.

        Args:
            key: Parameter key/name
            value: Parameter value
            type: Parameter type (default: "string")
        """
        self.key = key
        self.value = value
        self.type = type

    @classmethod
    def from_dict(cls, data: dict) -> "AuthParameter":
        """Create AuthParameter from dictionary data."""
        return cls(
            key=data.get("key"),
            value=data.get("value"),
            type=data.get("type", "string"),
        )

    def to_dict(self) -> dict:
        """Convert AuthParameter to dictionary."""
        return {"key": self.key, "value": self.value, "type": self.type}

    def __repr__(self) -> str:
        return (
            f"AuthParameter(key='{self.key}', value={self.value!r}, type='{self.type}')"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, AuthParameter):
            return False
        return (
            self.key == other.key
            and self.value == other.value
            and self.type == other.type
        )


class Auth:
    """Represents authentication configuration with support for different auth types."""

    def __init__(self, type: str, parameters: Optional[List[AuthParameter]] = None):
        """
        Initialize Auth.

        Args:
            type: Authentication type
            parameters: List of authentication parameters
        """
        self.type = type
        self._parameters = []
        self._parameter_lookup: Dict[str, AuthParameter] = {}
        
        # Set parameters using property to maintain lookup dict
        if parameters:
            self.parameters = parameters

    @property
    def parameters(self) -> List[AuthParameter]:
        """Get the list of authentication parameters."""
        return self._parameters

    @parameters.setter
    def parameters(self, value: List[AuthParameter]) -> None:
        """Set the list of authentication parameters and update lookup dict."""
        self._parameters = value or []
        # Handle case where non-list values are passed (for validation testing)
        try:
            self._parameter_lookup = {param.key: param for param in self._parameters}
        except (AttributeError, TypeError):
            # If parameters are not AuthParameter objects, create empty lookup
            self._parameter_lookup = {}

    def get_auth_type(self) -> AuthType:
        """
        Get the authentication type as enum.

        Returns:
            AuthType enum value, defaults to NOAUTH for unknown types
        """
        try:
            return AuthType(self.type.lower())
        except (ValueError, AttributeError):
            return AuthType.NOAUTH

    def get_parameter(self, key: str) -> Optional[Any]:
        """
        Get authentication parameter value by key.

        Args:
            key: Parameter key to retrieve

        Returns:
            Parameter value or None if not found
        """
        param = self._parameter_lookup.get(key)
        return param.value if param else None

    def get_parameter_dict(self) -> Dict[str, Any]:
        """
        Get all parameters as a dictionary.

        Returns:
            Dictionary of parameter key-value pairs
        """
        return {key: param.value for key, param in self._parameter_lookup.items()}

    def add_parameter(self, key: str, value: Any, type: str = "string") -> None:
        """
        Add or update an authentication parameter.

        Args:
            key: Parameter key
            value: Parameter value
            type: Parameter type
        """
        new_param = AuthParameter(key, value, type)
        
        # If parameter exists, replace it
        if key in self._parameter_lookup:
            # Find and replace in list
            for i, param in enumerate(self._parameters):
                if param.key == key:
                    self._parameters[i] = new_param
                    break
        else:
            # Add new parameter
            self._parameters.append(new_param)
        
        # Update lookup dict
        self._parameter_lookup[key] = new_param

    def remove_parameter(self, key: str) -> bool:
        """
        Remove an authentication parameter by key.

        Args:
            key: Parameter key to remove

        Returns:
            True if parameter was removed, False if not found
        """
        if key not in self._parameter_lookup:
            return False
        
        # Remove from lookup dict
        del self._parameter_lookup[key]
        
        # Remove from list
        self._parameters = [p for p in self._parameters if p.key != key]
        
        return True

    def is_basic_auth(self) -> bool:
        """Check if this is basic authentication."""
        return self.get_auth_type() == AuthType.BASIC

    def is_bearer_auth(self) -> bool:
        """Check if this is bearer token authentication."""
        return self.get_auth_type() == AuthType.BEARER

    def is_api_key_auth(self) -> bool:
        """Check if this is API key authentication."""
        return self.get_auth_type() == AuthType.APIKEY

    def is_oauth1_auth(self) -> bool:
        """Check if this is OAuth 1.0 authentication."""
        return self.get_auth_type() == AuthType.OAUTH1

    def is_oauth2_auth(self) -> bool:
        """Check if this is OAuth 2.0 authentication."""
        return self.get_auth_type() == AuthType.OAUTH2

    def get_basic_credentials(self) -> Optional[Dict[str, str]]:
        """
        Get basic auth credentials.

        Returns:
            Dictionary with 'username' and 'password' keys, or None
        """
        if not self.is_basic_auth():
            return None

        username = self.get_parameter("username")
        password = self.get_parameter("password")

        if username is not None or password is not None:
            return {"username": username or "", "password": password or ""}
        return None

    def get_bearer_token(self) -> Optional[str]:
        """
        Get bearer token.

        Returns:
            Bearer token string or None
        """
        if not self.is_bearer_auth():
            return None
        return self.get_parameter("token")

    def get_api_key_config(self) -> Optional[Dict[str, str]]:
        """
        Get API key configuration.

        Returns:
            Dictionary with 'key', 'value', and 'in' keys, or None
        """
        if not self.is_api_key_auth():
            return None

        key = self.get_parameter("key")
        value = self.get_parameter("value")
        in_location = self.get_parameter("in")

        if key is not None or value is not None:
            return {
                "key": key or "",
                "value": value or "",
                "in": in_location or "header",
            }
        return None

    def validate(self) -> bool:
        """
        Validate the authentication configuration.

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        if not self.type or not isinstance(self.type, str):
            raise ValueError("Auth type is required and must be a string")

        if not isinstance(self.parameters, list):
            raise ValueError("Auth parameters must be a list")

        # Validate each parameter
        for param in self.parameters:
            if not isinstance(param, AuthParameter):
                raise ValueError("All auth parameters must be AuthParameter instances")
            if not param.key or not isinstance(param.key, str):
                raise ValueError("Auth parameter key is required and must be a string")

        # Type-specific validation
        auth_type = self.get_auth_type()

        if auth_type == AuthType.BASIC:
            # Basic auth should have username and/or password
            if not any(p.key in ["username", "password"] for p in self.parameters):
                raise ValueError(
                    "Basic auth requires username and/or password parameters"
                )

        elif auth_type == AuthType.BEARER:
            # Bearer auth should have token
            if not any(p.key == "token" for p in self.parameters):
                raise ValueError("Bearer auth requires token parameter")

        elif auth_type == AuthType.APIKEY:
            # API key auth should have key and value
            required_keys = {"key", "value"}
            param_keys = {p.key for p in self.parameters}
            if not required_keys.issubset(param_keys):
                missing = required_keys - param_keys
                raise ValueError(
                    f"API key auth requires parameters: {', '.join(missing)}"
                )

        return True

    @classmethod
    def from_dict(cls, data: dict) -> "Auth":
        """
        Create Auth from dictionary data.

        Args:
            data: Dictionary containing auth data

        Returns:
            Auth instance
        """
        auth_type = data.get("type")
        parameters = []

        # Handle different parameter formats
        if auth_type in data:
            # Parameters are nested under the auth type key
            type_data = data[auth_type]
            if isinstance(type_data, list):
                parameters = [AuthParameter.from_dict(param) for param in type_data]
            elif isinstance(type_data, dict):
                # Convert dict to list of parameters
                for key, value in type_data.items():
                    if isinstance(value, dict) and "value" in value:
                        # Parameter is an object with value and possibly type
                        param_type = value.get("type", "string")
                        param_value = value["value"]
                    else:
                        # Parameter is a simple key-value pair
                        param_type = "string"
                        param_value = value
                    parameters.append(AuthParameter(key, param_value, param_type))

        return cls(type=auth_type, parameters=parameters)

    def to_dict(self) -> dict:
        """
        Convert Auth to dictionary.

        Returns:
            Dictionary representation of Auth
        """
        result = {"type": self.type}

        if self.parameters:
            # Group parameters under the auth type key
            type_params = []
            for param in self.parameters:
                type_params.append(param.to_dict())
            result[self.type] = type_params

        return result

    def __repr__(self) -> str:
        return f"Auth(type='{self.type}', parameters={self.parameters!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Auth):
            return False
        return self.type == other.type and self.parameters == other.parameters

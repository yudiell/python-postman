"""
Authentication handler for request processing.

This module contains the AuthHandler class, which processes authentication
configurations and applies them to requests, supporting bearer tokens,
basic authentication, and API key authentication.
"""

import base64
from typing import Optional, Dict, Any
from .context import ExecutionContext
from .exceptions import AuthenticationError
from ..models.auth import Auth, AuthType


class AuthHandler:
    """
    Handles authentication processing for requests.

    The AuthHandler processes different authentication types and applies
    them to requests by generating appropriate headers or parameters.
    """

    def apply_auth(
        self,
        request_auth: Optional[Auth],
        collection_auth: Optional[Auth],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """
        Apply authentication to request, returning headers/params to add.

        Args:
            request_auth: Request-level authentication
            collection_auth: Collection-level authentication
            context: Execution context for variable resolution

        Returns:
            Dictionary containing headers and/or parameters to add to request
            Format: {"headers": {...}, "params": {...}}

        Raises:
            AuthenticationError: If authentication processing fails
        """
        # Request-level auth takes precedence over collection-level auth
        auth_to_use = request_auth if request_auth else collection_auth

        if not auth_to_use:
            return {"headers": {}, "params": {}}

        auth_type = auth_to_use.get_auth_type()

        try:
            if auth_type == AuthType.BEARER:
                headers = self.process_bearer_auth(auth_to_use, context)
                return {"headers": headers, "params": {}}
            elif auth_type == AuthType.BASIC:
                headers = self.process_basic_auth(auth_to_use, context)
                return {"headers": headers, "params": {}}
            elif auth_type == AuthType.APIKEY:
                result = self.process_api_key_auth(auth_to_use, context)
                return result
            elif auth_type == AuthType.NOAUTH:
                return {"headers": {}, "params": {}}
            else:
                # For unsupported auth types, return empty but don't fail
                return {"headers": {}, "params": {}}

        except Exception as e:
            if isinstance(e, AuthenticationError):
                raise
            raise AuthenticationError(
                f"Failed to process {auth_type.value} authentication: {str(e)}",
                auth_type=auth_type.value,
            )

    def process_bearer_auth(
        self, auth: Auth, context: ExecutionContext
    ) -> Dict[str, str]:
        """
        Process bearer token authentication.

        Args:
            auth: Auth object with bearer configuration
            context: Execution context for variable resolution

        Returns:
            Dictionary of headers to add

        Raises:
            AuthenticationError: If bearer token is missing or invalid
        """
        if not auth.is_bearer_auth():
            raise AuthenticationError(
                "Auth object is not bearer type", auth_type=auth.type
            )

        token = auth.get_bearer_token()
        if token is None:
            raise AuthenticationError(
                "Bearer token is required but not found",
                auth_type="bearer",
                auth_parameter="token",
            )

        # Resolve variables in the token
        try:
            resolved_token = context.resolve_variables(str(token))
        except Exception as e:
            raise AuthenticationError(
                f"Failed to resolve variables in bearer token: {str(e)}",
                auth_type="bearer",
                auth_parameter="token",
            )

        if not resolved_token.strip():
            raise AuthenticationError(
                "Bearer token cannot be empty after variable resolution",
                auth_type="bearer",
                auth_parameter="token",
            )

        return {"Authorization": f"Bearer {resolved_token}"}

    def process_basic_auth(
        self, auth: Auth, context: ExecutionContext
    ) -> Dict[str, str]:
        """
        Process basic authentication.

        Args:
            auth: Auth object with basic auth configuration
            context: Execution context for variable resolution

        Returns:
            Dictionary of headers to add

        Raises:
            AuthenticationError: If basic auth credentials are invalid
        """
        if not auth.is_basic_auth():
            raise AuthenticationError(
                "Auth object is not basic type", auth_type=auth.type
            )

        credentials = auth.get_basic_credentials()
        if credentials is None:
            raise AuthenticationError(
                "Basic auth credentials are required but not found", auth_type="basic"
            )

        username = credentials.get("username", "")
        password = credentials.get("password", "")

        # Resolve variables in username and password
        try:
            resolved_username = (
                context.resolve_variables(str(username)) if username else ""
            )
            resolved_password = (
                context.resolve_variables(str(password)) if password else ""
            )
        except Exception as e:
            raise AuthenticationError(
                f"Failed to resolve variables in basic auth credentials: {str(e)}",
                auth_type="basic",
            )

        # Create base64 encoded credentials
        credentials_string = f"{resolved_username}:{resolved_password}"
        try:
            encoded_credentials = base64.b64encode(
                credentials_string.encode("utf-8")
            ).decode("ascii")
        except Exception as e:
            raise AuthenticationError(
                f"Failed to encode basic auth credentials: {str(e)}", auth_type="basic"
            )

        return {"Authorization": f"Basic {encoded_credentials}"}

    def process_api_key_auth(
        self, auth: Auth, context: ExecutionContext
    ) -> Dict[str, Any]:
        """
        Process API key authentication.

        Args:
            auth: Auth object with API key configuration
            context: Execution context for variable resolution

        Returns:
            Dictionary of headers and/or parameters to add
            Format: {"headers": {...}, "params": {...}}

        Raises:
            AuthenticationError: If API key configuration is invalid
        """
        if not auth.is_api_key_auth():
            raise AuthenticationError(
                "Auth object is not API key type", auth_type=auth.type
            )

        config = auth.get_api_key_config()
        if config is None:
            raise AuthenticationError(
                "API key configuration is required but not found", auth_type="apikey"
            )

        key = config.get("key", "")
        value = config.get("value", "")
        location = config.get("in", "header").lower()

        if not key.strip():
            raise AuthenticationError(
                "API key name cannot be empty", auth_type="apikey", auth_parameter="key"
            )

        if not value.strip():
            raise AuthenticationError(
                "API key value cannot be empty",
                auth_type="apikey",
                auth_parameter="value",
            )

        # Resolve variables in key and value
        try:
            resolved_key = context.resolve_variables(str(key))
            resolved_value = context.resolve_variables(str(value))
        except Exception as e:
            raise AuthenticationError(
                f"Failed to resolve variables in API key: {str(e)}", auth_type="apikey"
            )

        # Apply API key based on location
        if location == "header":
            return {"headers": {resolved_key: resolved_value}, "params": {}}
        elif location == "query":
            return {"headers": {}, "params": {resolved_key: resolved_value}}
        else:
            raise AuthenticationError(
                f"Invalid API key location '{location}'. Must be 'header' or 'query'",
                auth_type="apikey",
                auth_parameter="in",
            )

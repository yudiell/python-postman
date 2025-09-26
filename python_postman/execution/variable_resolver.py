"""
Variable resolution and substitution logic.

This module contains the VariableResolver class, which handles variable
substitution in URLs, headers, body content, and authentication parameters,
with support for recursive resolution and circular reference protection.
"""

from typing import Optional, List, Dict, Any, Union
import json
from .context import ExecutionContext
from .exceptions import VariableResolutionError
from ..models.url import Url
from ..models.header import Header
from ..models.body import Body, BodyMode
from ..models.auth import Auth


class VariableResolver:
    """
    Handles variable resolution and substitution.

    The VariableResolver processes variable references in request components,
    resolving them using the execution context while protecting against
    circular references and infinite recursion.
    """

    def __init__(self, context: ExecutionContext):
        """
        Initialize with execution context.

        Args:
            context: Execution context containing variables
        """
        self.context = context

    def resolve_url(self, url: Url) -> str:
        """
        Resolve variables in URL components.

        Args:
            url: URL object with potential variable references

        Returns:
            Resolved URL string
        """
        if not url:
            return ""

        # If URL has a raw string, resolve variables in it and handle query/hash
        if url.raw:
            resolved_raw = self.resolve_string(url.raw)

            # Only add query parameters if they don't already exist in the raw URL
            # This prevents duplication when both raw URL contains query params AND url.query exists
            if url.query and "?" not in resolved_raw:
                query_parts = []
                for param in url.query:
                    if not param.disabled and param.key:
                        resolved_key = self.resolve_string(param.key)
                        resolved_value = (
                            self.resolve_string(param.value) if param.value else ""
                        )
                        query_parts.append(f"{resolved_key}={resolved_value}")

                if query_parts:
                    resolved_raw += "?" + "&".join(query_parts)

            # Add hash/fragment if it exists
            if url.hash:
                resolved_hash = self.resolve_string(url.hash)
                resolved_raw += f"#{resolved_hash}"

            return resolved_raw

        # Build URL from components with variable resolution
        protocol = self.resolve_string(url.protocol) if url.protocol else "https"

        # Resolve host components
        host_parts = []
        if url.host:
            for host_part in url.host:
                if host_part:
                    resolved_part = self.resolve_string(str(host_part))
                    host_parts.append(resolved_part)

        host = ".".join(host_parts) if host_parts else ""

        # Resolve path components
        path_parts = []
        if url.path:
            for path_part in url.path:
                if path_part:
                    resolved_part = self.resolve_string(str(path_part))
                    path_parts.append(resolved_part)

        path = "/" + "/".join(path_parts) if path_parts else ""

        # Build base URL
        base_url = f"{protocol}://{host}"
        if url.port:
            resolved_port = self.resolve_string(str(url.port))
            base_url += f":{resolved_port}"

        base_url += path

        # Resolve query parameters
        if url.query:
            query_parts = []
            for param in url.query:
                if not param.disabled and param.key:
                    resolved_key = self.resolve_string(param.key)
                    resolved_value = (
                        self.resolve_string(param.value) if param.value else ""
                    )
                    query_parts.append(f"{resolved_key}={resolved_value}")

            if query_parts:
                base_url += "?" + "&".join(query_parts)

        # Resolve hash/fragment
        if url.hash:
            resolved_hash = self.resolve_string(url.hash)
            base_url += f"#{resolved_hash}"

        return base_url

    def resolve_headers(self, headers: List[Header]) -> Dict[str, str]:
        """
        Resolve variables in headers.

        Args:
            headers: List of header objects with potential variable references

        Returns:
            Dictionary of resolved headers
        """
        resolved_headers = {}

        if not headers:
            return resolved_headers

        for header in headers:
            if header.is_active():
                resolved_key = self.resolve_string(header.key)
                resolved_value = (
                    self.resolve_string(header.value) if header.value else ""
                )
                resolved_headers[resolved_key] = resolved_value

        return resolved_headers

    def resolve_body(self, body: Optional[Body]) -> Optional[Any]:
        """
        Resolve variables in request body.

        Args:
            body: Body object with potential variable references

        Returns:
            Resolved body content
        """
        if not body or not body.is_active():
            return None

        mode = body.get_mode()
        if not mode:
            return None

        if mode == BodyMode.RAW:
            if body.raw:
                resolved_raw = self.resolve_string(body.raw)
                # Try to parse as JSON if it looks like JSON
                if resolved_raw.strip().startswith(("{", "[")):
                    try:
                        return json.loads(resolved_raw)
                    except json.JSONDecodeError:
                        pass
                return resolved_raw
            return None

        elif mode == BodyMode.URLENCODED:
            resolved_params = {}
            for param in body.urlencoded:
                if param.is_active():
                    resolved_key = self.resolve_string(param.key)
                    resolved_value = (
                        self.resolve_string(param.value) if param.value else ""
                    )
                    resolved_params[resolved_key] = resolved_value
            return resolved_params

        elif mode == BodyMode.FORMDATA:
            resolved_formdata = []
            for param in body.formdata:
                if param.is_active():
                    resolved_key = self.resolve_string(param.key)
                    if param.is_file():
                        # For file parameters, resolve the src path or value
                        file_value = param.src or param.value or ""
                        resolved_value = self.resolve_string(file_value)
                        resolved_formdata.append((resolved_key, resolved_value, "file"))
                    else:
                        resolved_value = (
                            self.resolve_string(param.value) if param.value else ""
                        )
                        resolved_formdata.append((resolved_key, resolved_value, "text"))
            return resolved_formdata

        elif mode == BodyMode.GRAPHQL:
            if body.raw:
                resolved_raw = self.resolve_string(body.raw)
                try:
                    return json.loads(resolved_raw)
                except json.JSONDecodeError:
                    return resolved_raw
            return None

        elif mode == BodyMode.FILE:
            if body.file and body.file.get("src"):
                return self.resolve_string(body.file["src"])
            return None

        elif mode == BodyMode.BINARY:
            if body.raw:
                return self.resolve_string(body.raw)
            return None

        return None

    def resolve_auth(self, auth: Optional[Auth]) -> Optional[Dict[str, Any]]:
        """
        Resolve variables in authentication.

        Args:
            auth: Auth object with potential variable references

        Returns:
            Dictionary of resolved authentication parameters
        """
        if not auth:
            return None

        resolved_auth = {"type": auth.type, "parameters": {}}

        # Resolve all authentication parameters
        for param in auth.parameters:
            resolved_key = self.resolve_string(param.key)
            resolved_value = (
                self.resolve_string(str(param.value))
                if param.value is not None
                else None
            )
            resolved_auth["parameters"][resolved_key] = resolved_value

        return resolved_auth

    def resolve_string(self, text: str, max_depth: int = 10) -> str:
        """
        Resolve variables in string with recursion protection.

        Supports both Postman-style variables ({{variable}}) and path parameters (:parameter).

        Args:
            text: Text containing variable references
            max_depth: Maximum recursion depth to prevent infinite loops

        Returns:
            Text with variables resolved
        """
        if not isinstance(text, str):
            return str(text) if text is not None else ""

        resolved_text = text

        try:
            # Use the context's resolve_variables method which now handles both
            # Postman-style variables {{variable}} and path parameters :parameter
            resolved_text = self.context.resolve_variables(resolved_text, max_depth)

            return resolved_text
        except VariableResolutionError:
            # Re-raise variable resolution errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions in VariableResolutionError
            raise VariableResolutionError(
                f"Error resolving variables in text '{text}': {str(e)}"
            )

    def resolve_dict_values(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve variables in dictionary values recursively.

        Args:
            data: Dictionary with potential variable references in values

        Returns:
            Dictionary with resolved values
        """
        resolved_dict = {}

        for key, value in data.items():
            resolved_key = self.resolve_string(str(key))

            if isinstance(value, str):
                resolved_dict[resolved_key] = self.resolve_string(value)
            elif isinstance(value, dict):
                resolved_dict[resolved_key] = self.resolve_dict_values(value)
            elif isinstance(value, list):
                resolved_dict[resolved_key] = self.resolve_list_values(value)
            else:
                resolved_dict[resolved_key] = value

        return resolved_dict

    def resolve_list_values(self, data: List[Any]) -> List[Any]:
        """
        Resolve variables in list values recursively.

        Args:
            data: List with potential variable references

        Returns:
            List with resolved values
        """
        resolved_list = []

        for item in data:
            if isinstance(item, str):
                resolved_list.append(self.resolve_string(item))
            elif isinstance(item, dict):
                resolved_list.append(self.resolve_dict_values(item))
            elif isinstance(item, list):
                resolved_list.append(self.resolve_list_values(item))
            else:
                resolved_list.append(item)

        return resolved_list

"""
RequestExtensions for runtime modifications of request components.

This module provides the RequestExtensions class that allows runtime substitution
and extension of URL, headers, parameters, body, and authentication components.
"""

from typing import Optional, Dict, Any, List, Union
import copy
import json
import re
from urllib.parse import urlencode

from ..models.request import Request
from ..models.url import Url, QueryParam
from ..models.header import Header
from ..models.body import Body, FormParameter, BodyMode
from ..models.auth import Auth, AuthParameter
from .context import ExecutionContext


class RequestExtensions:
    """
    Defines runtime modifications to request components.

    Supports substitution (replacing existing values) and extension (adding new values)
    for URL, headers, parameters, body, and authentication components.
    """

    def __init__(
        self,
        url_substitutions: Optional[Dict[str, str]] = None,
        header_substitutions: Optional[Dict[str, str]] = None,
        header_extensions: Optional[Dict[str, str]] = None,
        param_substitutions: Optional[Dict[str, str]] = None,
        param_extensions: Optional[Dict[str, str]] = None,
        body_substitutions: Optional[Dict[str, Any]] = None,
        body_extensions: Optional[Dict[str, Any]] = None,
        auth_substitutions: Optional[Dict[str, str]] = None,
    ):
        """
        Initialize RequestExtensions.

        Args:
            url_substitutions: Substitutions for URL components (protocol, host, port, path)
            header_substitutions: Substitutions for existing header values
            header_extensions: New headers to add
            param_substitutions: Substitutions for existing query parameter values
            param_extensions: New query parameters to add
            body_substitutions: Substitutions for body content
            body_extensions: Extensions to body content
            auth_substitutions: Substitutions for authentication parameters
        """
        self.url_substitutions = url_substitutions or {}
        self.header_substitutions = header_substitutions or {}
        self.header_extensions = header_extensions or {}
        self.param_substitutions = param_substitutions or {}
        self.param_extensions = param_extensions or {}
        self.body_substitutions = body_substitutions or {}
        self.body_extensions = body_extensions or {}
        self.auth_substitutions = auth_substitutions or {}

    def apply_to_request(self, request: Request, context: ExecutionContext) -> Request:
        """
        Apply extensions to create a modified request.

        Args:
            request: Original request to modify
            context: Execution context for variable resolution

        Returns:
            New Request object with extensions applied
        """
        # Create a deep copy of the request to avoid modifying the original
        modified_request = copy.deepcopy(request)

        # Apply URL modifications
        if self.url_substitutions or self.param_substitutions or self.param_extensions:
            modified_request.url = self._apply_url_extensions(
                modified_request.url, context
            )

        # Apply header modifications
        if self.header_substitutions or self.header_extensions:
            modified_request.headers = self._apply_header_extensions(
                modified_request.headers, context
            )

        # Apply body modifications
        if self.body_substitutions or self.body_extensions:
            modified_request.body = self._apply_body_extensions(
                modified_request.body, context
            )

        # Apply auth modifications
        if self.auth_substitutions:
            modified_request.auth = self._apply_auth_extensions(
                modified_request.auth, context
            )

        return modified_request

    def _apply_url_extensions(self, url: Url, context: ExecutionContext) -> Url:
        """Apply URL extensions and substitutions."""
        modified_url = copy.deepcopy(url)

        # Apply URL component substitutions
        for component, value in self.url_substitutions.items():
            resolved_value = context.resolve_variables(value)

            if component == "protocol":
                modified_url.protocol = resolved_value
            elif component == "host":
                if isinstance(resolved_value, str):
                    modified_url.host = [resolved_value]
                elif isinstance(resolved_value, list):
                    modified_url.host = resolved_value
            elif component == "port":
                modified_url.port = resolved_value
            elif component == "path":
                if isinstance(resolved_value, str):
                    modified_url.path = (
                        resolved_value.split("/") if resolved_value else []
                    )
                elif isinstance(resolved_value, list):
                    modified_url.path = resolved_value
            elif component == "hash":
                modified_url.hash = resolved_value

        # Apply query parameter substitutions
        for param_key, new_value in self.param_substitutions.items():
            resolved_value = context.resolve_variables(new_value)
            for param in modified_url.query:
                if param.key == param_key:
                    param.value = resolved_value

        # Apply query parameter extensions (add new parameters)
        for param_key, param_value in self.param_extensions.items():
            resolved_value = context.resolve_variables(param_value)
            # Check if parameter already exists
            existing_param = next(
                (p for p in modified_url.query if p.key == param_key), None
            )
            if not existing_param:
                modified_url.query.append(
                    QueryParam(key=param_key, value=resolved_value)
                )

        return modified_url

    def _apply_header_extensions(
        self, headers: List[Header], context: ExecutionContext
    ) -> List[Header]:
        """Apply header extensions and substitutions."""
        modified_headers = copy.deepcopy(headers)

        # Apply header substitutions
        for header_key, new_value in self.header_substitutions.items():
            resolved_value = context.resolve_variables(new_value)
            # Find header by key (case-insensitive)
            for header in modified_headers:
                if header.key.lower() == header_key.lower():
                    header.value = resolved_value

        # Apply header extensions (add new headers)
        for header_key, header_value in self.header_extensions.items():
            resolved_value = context.resolve_variables(header_value)
            # Check if header already exists (case-insensitive)
            existing_header = next(
                (h for h in modified_headers if h.key.lower() == header_key.lower()),
                None,
            )
            if not existing_header:
                modified_headers.append(Header(key=header_key, value=resolved_value))

        return modified_headers

    def _apply_body_extensions(
        self, body: Optional[Body], context: ExecutionContext
    ) -> Optional[Body]:
        """Apply body extensions and substitutions."""
        if not body:
            return body

        modified_body = copy.deepcopy(body)
        body_mode = modified_body.get_mode()

        if body_mode == BodyMode.RAW:
            modified_body = self._apply_raw_body_extensions(modified_body, context)
        elif body_mode == BodyMode.URLENCODED:
            modified_body = self._apply_form_body_extensions(
                modified_body, context, "urlencoded"
            )
        elif body_mode == BodyMode.FORMDATA:
            modified_body = self._apply_form_body_extensions(
                modified_body, context, "formdata"
            )
        elif body_mode == BodyMode.GRAPHQL:
            modified_body = self._apply_graphql_body_extensions(modified_body, context)

        return modified_body

    def _apply_raw_body_extensions(self, body: Body, context: ExecutionContext) -> Body:
        """Apply extensions to raw body content."""
        if not body.raw:
            return body

        # Apply substitutions to raw content
        modified_content = body.raw
        for key, value in self.body_substitutions.items():
            resolved_value = context.resolve_variables(str(value))
            # Only replace specific placeholder patterns, not arbitrary text
            placeholder_patterns = [
                f"{{{{{key}}}}}",  # {{key}} format
                f":{key}",  # :key format (for path parameters)
            ]
            for pattern in placeholder_patterns:
                modified_content = modified_content.replace(pattern, resolved_value)

        # For JSON content, try to parse and extend
        if self.body_extensions and self._is_json_content(body):
            try:
                json_data = json.loads(modified_content)
                if isinstance(json_data, dict):
                    # Apply extensions to JSON object
                    for key, value in self.body_extensions.items():
                        resolved_value = context.resolve_variables(str(value))
                        # Try to parse as JSON, fallback to string
                        try:
                            json_data[key] = json.loads(resolved_value)
                        except json.JSONDecodeError:
                            json_data[key] = resolved_value
                    modified_content = json.dumps(json_data)
            except json.JSONDecodeError:
                # If not valid JSON, treat as plain text
                pass

        body.raw = modified_content
        return body

    def _apply_form_body_extensions(
        self, body: Body, context: ExecutionContext, form_type: str
    ) -> Body:
        """Apply extensions to form body content (urlencoded or formdata)."""
        form_params = body.urlencoded if form_type == "urlencoded" else body.formdata

        # Apply parameter substitutions
        for param_key, new_value in self.body_substitutions.items():
            resolved_value = context.resolve_variables(str(new_value))
            for param in form_params:
                if param.key == param_key:
                    param.value = resolved_value

        # Apply parameter extensions (add new parameters)
        for param_key, param_value in self.body_extensions.items():
            resolved_value = context.resolve_variables(str(param_value))
            # Check if parameter already exists
            existing_param = next((p for p in form_params if p.key == param_key), None)
            if not existing_param:
                new_param = FormParameter(key=param_key, value=resolved_value)
                form_params.append(new_param)

        return body

    def _apply_graphql_body_extensions(
        self, body: Body, context: ExecutionContext
    ) -> Body:
        """Apply extensions to GraphQL body content."""
        if not body.raw:
            return body

        try:
            graphql_data = json.loads(body.raw)
            if isinstance(graphql_data, dict):
                # Apply substitutions to GraphQL fields
                for key, value in self.body_substitutions.items():
                    resolved_value = context.resolve_variables(str(value))
                    if key in graphql_data:
                        # Try to parse as JSON, fallback to string
                        try:
                            graphql_data[key] = json.loads(resolved_value)
                        except json.JSONDecodeError:
                            graphql_data[key] = resolved_value

                # Apply extensions to GraphQL object
                for key, value in self.body_extensions.items():
                    resolved_value = context.resolve_variables(str(value))
                    # Try to parse as JSON, fallback to string
                    try:
                        graphql_data[key] = json.loads(resolved_value)
                    except json.JSONDecodeError:
                        graphql_data[key] = resolved_value

                body.raw = json.dumps(graphql_data)
        except json.JSONDecodeError:
            # If not valid JSON, treat as raw text
            body = self._apply_raw_body_extensions(body, context)

        return body

    def _apply_auth_extensions(
        self, auth: Optional[Auth], context: ExecutionContext
    ) -> Optional[Auth]:
        """Apply authentication extensions and substitutions."""
        if not auth:
            return auth

        modified_auth = copy.deepcopy(auth)

        # Apply auth parameter substitutions
        for param_key, new_value in self.auth_substitutions.items():
            resolved_value = context.resolve_variables(new_value)
            # Find and update the parameter
            for param in modified_auth.parameters:
                if param.key == param_key:
                    param.value = resolved_value

        return modified_auth

    def _is_json_content(self, body: Body) -> bool:
        """Check if body content appears to be JSON."""
        if not body.raw:
            return False

        # Check options for JSON language setting
        raw_options = body.options.get("raw", {})
        if raw_options.get("language") == "json":
            return True

        # Try to detect JSON by parsing
        try:
            json.loads(body.raw)
            return True
        except json.JSONDecodeError:
            return False

    def _resolve_variable_placeholders(
        self, text: str, context: ExecutionContext
    ) -> str:
        """
        Resolve variable placeholders in text.

        Args:
            text: Text containing variable placeholders
            context: Execution context for variable resolution

        Returns:
            Text with resolved variables
        """
        if not text:
            return text

        # Use context's resolve_variables method
        return context.resolve_variables(text)

    def has_modifications(self) -> bool:
        """
        Check if this extensions object has any modifications.

        Returns:
            True if any extensions or substitutions are defined
        """
        return bool(
            self.url_substitutions
            or self.header_substitutions
            or self.header_extensions
            or self.param_substitutions
            or self.param_extensions
            or self.body_substitutions
            or self.body_extensions
            or self.auth_substitutions
        )

    def __repr__(self) -> str:
        return (
            f"RequestExtensions("
            f"url_subs={len(self.url_substitutions)}, "
            f"header_subs={len(self.header_substitutions)}, "
            f"header_exts={len(self.header_extensions)}, "
            f"param_subs={len(self.param_substitutions)}, "
            f"param_exts={len(self.param_extensions)}, "
            f"body_subs={len(self.body_substitutions)}, "
            f"body_exts={len(self.body_extensions)}, "
            f"auth_subs={len(self.auth_substitutions)}"
            f")"
        )

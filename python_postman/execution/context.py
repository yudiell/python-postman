"""Execution context for managing variables and execution state."""

from typing import Any, Dict, Optional, Union
import re
from ..exceptions import PostmanCollectionError
from .exceptions import VariableResolutionError


class ExecutionContext:
    """Maintains execution state including variables and environment.

    Manages variable scoping with precedence: request > folder > collection > environment.
    Provides methods for getting, setting, and resolving variables with support for
    nested variable references.

    Examples:
        Basic usage:

        >>> context = ExecutionContext(
        ...     environment_variables={"base_url": "https://api.example.com"},
        ...     collection_variables={"api_version": "v1", "timeout": "30"},
        ...     folder_variables={"endpoint": "/users"},
        ...     request_variables={"user_id": "12345"}
        ... )
        >>>
        >>> # Variable precedence: request > folder > collection > environment
        >>> print(context.get_variable("user_id"))  # "12345" (from request)
        >>> print(context.get_variable("endpoint"))  # "/users" (from folder)

        Variable resolution:

        >>> context = ExecutionContext(
        ...     environment_variables={"protocol": "https", "domain": "api.example.com"},
        ...     collection_variables={"base_url": "{{protocol}}://{{domain}}"}
        ... )
        >>>
        >>> resolved = context.resolve_variables("{{base_url}}/v1/users")
        >>> print(resolved)  # "https://api.example.com/v1/users"

        Dynamic variable updates:

        >>> context.set_variable("session_token", "abc123", "environment")
        >>> token = context.get_variable("session_token")
        >>> print(f"Token: {token}")  # "Token: abc123"
    """

    def __init__(
        self,
        collection_variables: Optional[Dict[str, Any]] = None,
        folder_variables: Optional[Dict[str, Any]] = None,
        environment_variables: Optional[Dict[str, Any]] = None,
        request_variables: Optional[Dict[str, Any]] = None,
    ):
        """Initialize execution context with variable scopes.

        Args:
            collection_variables: Variables defined at collection level
            folder_variables: Variables defined at folder level
            environment_variables: Variables defined at environment level
            request_variables: Variables defined at request level
        """
        self.environment_variables = environment_variables or {}
        self.collection_variables = collection_variables or {}
        self.folder_variables = folder_variables or {}
        self.request_variables = request_variables or {}

        # Pattern for matching variables in strings like {{variable_name}}
        # More precise pattern that requires exactly two braces on each side
        self._variable_pattern = re.compile(r"\{\{([^{}]+)\}\}")

    def get_variable(self, key: str) -> Optional[Any]:
        """Get variable value following precedence: request > folder > collection > environment.

        Args:
            key: Variable name to retrieve

        Returns:
            Variable value if found, None otherwise
        """
        # Check request scope first (highest precedence)
        if key in self.request_variables:
            return self.request_variables[key]

        # Check folder scope
        if key in self.folder_variables:
            return self.folder_variables[key]

        # Check collection scope
        if key in self.collection_variables:
            return self.collection_variables[key]

        # Check environment scope (lowest precedence)
        if key in self.environment_variables:
            return self.environment_variables[key]

        return None

    def _variable_exists(self, key: str) -> bool:
        """Check if variable exists in any scope, including None values."""
        return (
            key in self.request_variables
            or key in self.folder_variables
            or key in self.collection_variables
            or key in self.environment_variables
        )

    def set_variable(self, key: str, value: Any, scope: str = "collection") -> None:
        """Set variable in specified scope.

        Args:
            key: Variable name
            value: Variable value
            scope: Scope to set variable in ("request", "folder", "collection", "environment")

        Raises:
            ValueError: If scope is invalid
        """
        if scope == "request":
            self.request_variables[key] = value
        elif scope == "folder":
            self.folder_variables[key] = value
        elif scope == "collection":
            self.collection_variables[key] = value
        elif scope == "environment":
            self.environment_variables[key] = value
        else:
            raise ValueError(
                f"Invalid scope: {scope}. Must be one of: request, folder, collection, environment"
            )

    def resolve_variables(self, text: str, max_depth: int = 10) -> str:
        """Resolve all variables in a text string with recursion protection.

        Args:
            text: Text containing variables in {{variable_name}} format
            max_depth: Maximum recursion depth to prevent infinite loops

        Returns:
            Text with variables resolved

        Raises:
            VariableResolutionError: If variable not found or max depth exceeded

        Examples:
            Simple variable resolution:

            >>> context = ExecutionContext(
            ...     collection_variables={"api_host": "api.example.com", "port": "443"}
            ... )
            >>> url = context.resolve_variables("https://{{api_host}}:{{port}}/users")
            >>> print(url)  # "https://api.example.com:443/users"

            Nested variable resolution:

            >>> context = ExecutionContext(
            ...     environment_variables={"env": "prod"},
            ...     collection_variables={"host": "{{env}}.api.example.com"}
            ... )
            >>> resolved = context.resolve_variables("https://{{host}}/api")
            >>> print(resolved)  # "https://prod.api.example.com/api"

            Error handling:

            >>> try:
            ...     context.resolve_variables("{{missing_variable}}")
            ... except VariableResolutionError as e:
            ...     print(f"Error: {e}")
        """
        if not isinstance(text, str):
            return str(text)

        resolved_text = text
        depth = 0

        while depth < max_depth:
            # Find all variable references with their positions
            matches = list(self._variable_pattern.finditer(resolved_text))

            if not matches:
                # No more variables to resolve
                break

            # Track if any substitutions were made this iteration
            substitutions_made = False

            # Process matches in reverse order to maintain positions
            for match in reversed(matches):
                var_name = match.group(1).strip()

                # Check if variable exists (including None values)
                if not self._variable_exists(var_name):
                    raise VariableResolutionError(
                        f"Variable '{var_name}' not found in any scope"
                    )

                var_value = self.get_variable(var_name)

                # Replace the variable reference with its value
                start, end = match.span()
                resolved_text = (
                    resolved_text[:start] + str(var_value) + resolved_text[end:]
                )
                substitutions_made = True

            if not substitutions_made:
                # No substitutions made, avoid infinite loop
                break

            depth += 1

        # Check if we hit max depth with unresolved variables
        if depth >= max_depth and self._variable_pattern.search(resolved_text):
            raise VariableResolutionError(
                f"Maximum recursion depth ({max_depth}) exceeded while resolving variables. "
                f"Possible circular reference in: {resolved_text}"
            )

        return resolved_text

    def create_child_context(
        self, request_variables: Optional[Dict[str, Any]] = None
    ) -> "ExecutionContext":
        """Create child context for request execution.

        Args:
            request_variables: Variables specific to the request

        Returns:
            New ExecutionContext with request-level variables
        """
        return ExecutionContext(
            collection_variables=self.collection_variables.copy(),
            folder_variables=self.folder_variables.copy(),
            environment_variables=self.environment_variables.copy(),
            request_variables=request_variables or {},
        )

    def has_variable(self, key: str) -> bool:
        """Check if variable exists in any scope.

        Args:
            key: Variable name to check

        Returns:
            True if variable exists, False otherwise
        """
        return self._variable_exists(key)

    def get_all_variables(self) -> Dict[str, Any]:
        """Get all variables merged with proper precedence.

        Returns:
            Dictionary with all variables, request scope taking precedence
        """
        merged = {}

        # Add in reverse precedence order so higher precedence overwrites
        merged.update(self.environment_variables)
        merged.update(self.collection_variables)
        merged.update(self.folder_variables)
        merged.update(self.request_variables)

        return merged

    def clear_scope(self, scope: str) -> None:
        """Clear all variables in specified scope.

        Args:
            scope: Scope to clear ("request", "folder", "collection", "environment")

        Raises:
            ValueError: If scope is invalid
        """
        if scope == "request":
            self.request_variables.clear()
        elif scope == "folder":
            self.folder_variables.clear()
        elif scope == "collection":
            self.collection_variables.clear()
        elif scope == "environment":
            self.environment_variables.clear()
        else:
            raise ValueError(
                f"Invalid scope: {scope}. Must be one of: request, folder, collection, environment"
            )

    def __repr__(self) -> str:
        """String representation of the execution context."""
        total_vars = (
            len(self.environment_variables)
            + len(self.collection_variables)
            + len(self.folder_variables)
            + len(self.request_variables)
        )
        return f"ExecutionContext(total_variables={total_vars})"

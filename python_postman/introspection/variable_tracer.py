"""Variable scope introspection and tracing utilities."""

from typing import Dict, List, Optional, Set, Any, TYPE_CHECKING
from enum import Enum
import re

from ..models.variable import VariableScope

if TYPE_CHECKING:
    from ..models.collection import Collection
    from ..execution.context import ExecutionContext


class VariableReference:
    """Represents a variable reference with its location and scope information."""

    def __init__(
        self,
        variable_name: str,
        scope: VariableScope,
        value: Any,
        location: str,
    ):
        """
        Initialize a VariableReference.

        Args:
            variable_name: Name of the variable
            scope: Scope where the variable is defined
            value: Value of the variable
            location: Human-readable location description
        """
        self.variable_name = variable_name
        self.scope = scope
        self.value = value
        self.location = location

    def __repr__(self) -> str:
        return (
            f"VariableReference(name='{self.variable_name}', "
            f"scope={self.scope.value}, value={self.value!r}, location='{self.location}')"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, VariableReference):
            return False
        return (
            self.variable_name == other.variable_name
            and self.scope == other.scope
            and self.value == other.value
            and self.location == other.location
        )


class VariableTracer:
    """Traces and analyzes variable usage and scoping in collections."""

    def __init__(self, collection: "Collection"):
        """
        Initialize VariableTracer with a collection.

        Args:
            collection: Collection to analyze
        """
        self.collection = collection
        # Pattern for matching variables in strings like {{variable_name}}
        self._variable_pattern = re.compile(r"\{\{([^{}]+)\}\}")
        # Pattern for path parameters like :paramName
        self._path_param_pattern = re.compile(
            r"(?<![a-zA-Z0-9_]):([a-zA-Z_][a-zA-Z0-9_]*)(?=/|\?|$|&|#)"
        )

    def trace_variable(
        self,
        variable_name: str,
        context: Optional["ExecutionContext"] = None,
    ) -> List[VariableReference]:
        """
        Trace all definitions of a variable across scopes.

        Returns list ordered by precedence (highest first):
        REQUEST > FOLDER > COLLECTION > ENVIRONMENT

        Args:
            variable_name: Name of the variable to trace
            context: Optional execution context for runtime variables

        Returns:
            List of VariableReference objects ordered by precedence

        Examples:
            >>> tracer = VariableTracer(collection)
            >>> references = tracer.trace_variable("api_key")
            >>> for ref in references:
            ...     print(f"{ref.scope.value}: {ref.value} at {ref.location}")
        """
        references = []

        # Check runtime context if provided
        if context:
            # Request scope
            if variable_name in context.request_variables:
                references.append(
                    VariableReference(
                        variable_name,
                        VariableScope.REQUEST,
                        context.request_variables[variable_name],
                        "request context",
                    )
                )

            # Folder scope
            if variable_name in context.folder_variables:
                references.append(
                    VariableReference(
                        variable_name,
                        VariableScope.FOLDER,
                        context.folder_variables[variable_name],
                        "folder context",
                    )
                )

            # Collection scope
            if variable_name in context.collection_variables:
                references.append(
                    VariableReference(
                        variable_name,
                        VariableScope.COLLECTION,
                        context.collection_variables[variable_name],
                        "collection context",
                    )
                )

            # Environment scope (stored in context.environment_variables)
            if variable_name in context.environment_variables:
                references.append(
                    VariableReference(
                        variable_name,
                        VariableScope.REQUEST,  # Using REQUEST as proxy for ENVIRONMENT
                        context.environment_variables[variable_name],
                        "environment context",
                    )
                )

        # Check collection-level variables
        for var in self.collection.variables:
            if var.key == variable_name:
                references.append(
                    VariableReference(
                        variable_name,
                        VariableScope.COLLECTION,
                        var.value,
                        f"collection '{self.collection.info.name}'",
                    )
                )

        # Check folder-level variables (walk through all folders)
        self._trace_in_folders(variable_name, self.collection.items, [], references)

        return references

    def _trace_in_folders(
        self,
        variable_name: str,
        items: List,
        path: List[str],
        references: List[VariableReference],
    ) -> None:
        """Recursively trace variables in folder hierarchy."""
        from ..models.folder import Folder

        for item in items:
            if isinstance(item, Folder):
                current_path = path + [item.name]
                # Check folder variables
                if hasattr(item, "variables") and item.variables:
                    for var in item.variables:
                        if var.key == variable_name:
                            references.append(
                                VariableReference(
                                    variable_name,
                                    VariableScope.FOLDER,
                                    var.value,
                                    f"folder '{' > '.join(current_path)}'",
                                )
                            )
                # Recurse into subfolders
                self._trace_in_folders(
                    variable_name, item.items, current_path, references
                )

    def find_shadowed_variables(self) -> Dict[str, List[VariableReference]]:
        """
        Find variables defined in multiple scopes (shadowing).

        Returns:
            Dictionary mapping variable names to list of their definitions
            across different scopes. Only includes variables defined in 2+ scopes.

        Examples:
            >>> tracer = VariableTracer(collection)
            >>> shadowed = tracer.find_shadowed_variables()
            >>> for var_name, refs in shadowed.items():
            ...     print(f"Variable '{var_name}' is defined in {len(refs)} scopes:")
            ...     for ref in refs:
            ...         print(f"  - {ref.scope.value}: {ref.value}")
        """
        # Collect all variable definitions
        all_variables: Dict[str, List[VariableReference]] = {}

        # Collection-level variables
        for var in self.collection.variables:
            if var.key not in all_variables:
                all_variables[var.key] = []
            all_variables[var.key].append(
                VariableReference(
                    var.key,
                    VariableScope.COLLECTION,
                    var.value,
                    f"collection '{self.collection.info.name}'",
                )
            )

        # Folder-level variables
        self._collect_folder_variables(self.collection.items, [], all_variables)

        # Filter to only variables defined in multiple scopes
        shadowed = {
            var_name: refs for var_name, refs in all_variables.items() if len(refs) > 1
        }

        return shadowed

    def _collect_folder_variables(
        self,
        items: List,
        path: List[str],
        all_variables: Dict[str, List[VariableReference]],
    ) -> None:
        """Recursively collect variables from folder hierarchy."""
        from ..models.folder import Folder

        for item in items:
            if isinstance(item, Folder):
                current_path = path + [item.name]
                # Collect folder variables
                if hasattr(item, "variables") and item.variables:
                    for var in item.variables:
                        if var.key not in all_variables:
                            all_variables[var.key] = []
                        all_variables[var.key].append(
                            VariableReference(
                                var.key,
                                VariableScope.FOLDER,
                                var.value,
                                f"folder '{' > '.join(current_path)}'",
                            )
                        )
                # Recurse into subfolders
                self._collect_folder_variables(
                    item.items, current_path, all_variables
                )

    def find_undefined_references(self) -> List[str]:
        """
        Find variable references that are not defined anywhere in the collection.

        Returns:
            List of variable names that are referenced but not defined

        Examples:
            >>> tracer = VariableTracer(collection)
            >>> undefined = tracer.find_undefined_references()
            >>> if undefined:
            ...     print("Undefined variables:")
            ...     for var in undefined:
            ...         print(f"  - {var}")
        """
        # Collect all defined variables
        defined_vars = self._collect_all_defined_variables()

        # Collect all referenced variables
        referenced_vars = self._collect_all_variable_references()

        # Find references without definitions
        undefined = referenced_vars - defined_vars

        return sorted(list(undefined))

    def _collect_all_defined_variables(self) -> Set[str]:
        """Collect all variable names defined in the collection."""
        defined = set()

        # Collection-level variables
        for var in self.collection.variables:
            defined.add(var.key)

        # Folder-level variables
        self._collect_defined_in_folders(self.collection.items, defined)

        return defined

    def _collect_defined_in_folders(self, items: List, defined: Set[str]) -> None:
        """Recursively collect defined variables from folders."""
        from ..models.folder import Folder

        for item in items:
            if isinstance(item, Folder):
                if hasattr(item, "variables") and item.variables:
                    for var in item.variables:
                        defined.add(var.key)
                # Recurse into subfolders
                self._collect_defined_in_folders(item.items, defined)

    def _collect_all_variable_references(self) -> Set[str]:
        """Collect all variable names referenced in the collection."""
        referenced = set()

        # Search through all requests
        for request in self.collection.get_requests():
            # Check URL
            url_str = request.url.to_string()
            referenced.update(self._extract_variable_names(url_str))

            # Check headers
            for header in request.headers:
                if header.value:
                    referenced.update(self._extract_variable_names(header.value))

            # Check body
            if request.body:
                if request.body.raw:
                    referenced.update(self._extract_variable_names(request.body.raw))
                if request.body.formdata:
                    for param in request.body.formdata:
                        if param.value:
                            referenced.update(
                                self._extract_variable_names(param.value)
                            )
                if request.body.urlencoded:
                    for param in request.body.urlencoded:
                        if param.value:
                            referenced.update(
                                self._extract_variable_names(param.value)
                            )

            # Check auth
            if request.auth:
                for param in request.auth.parameters:
                    if param.value:
                        referenced.update(self._extract_variable_names(str(param.value)))

            # Check scripts (events)
            for event in request.events:
                script_content = event.get_script_content()
                if script_content:
                    referenced.update(self._extract_variable_names(script_content))

        return referenced

    def _extract_variable_names(self, text: str) -> Set[str]:
        """Extract variable names from text containing {{variable}} or :parameter syntax."""
        if not isinstance(text, str):
            return set()

        variables = set()

        # Extract Postman-style variables {{variable_name}}
        for match in self._variable_pattern.finditer(text):
            var_name = match.group(1).strip()
            variables.add(var_name)

        # Extract path parameters :paramName
        for match in self._path_param_pattern.finditer(text):
            param_name = match.group(1)
            variables.add(param_name)

        return variables

    def find_variable_usage(self, variable_name: str) -> List[str]:
        """
        Find all locations where a variable is referenced.

        Args:
            variable_name: Name of the variable to find usage for

        Returns:
            List of human-readable location strings where the variable is used

        Examples:
            >>> tracer = VariableTracer(collection)
            >>> usage = tracer.find_variable_usage("api_key")
            >>> print(f"Variable 'api_key' is used in {len(usage)} locations:")
            >>> for location in usage:
            ...     print(f"  - {location}")
        """
        usage_locations = []

        # Search through all requests
        for request in self.collection.get_requests():
            request_path = self._get_request_path(request)

            # Check URL
            url_str = request.url.to_string()
            if variable_name in self._extract_variable_names(url_str):
                usage_locations.append(f"{request_path} - URL")

            # Check headers
            for header in request.headers:
                if header.value and variable_name in self._extract_variable_names(
                    header.value
                ):
                    usage_locations.append(
                        f"{request_path} - Header '{header.key}'"
                    )

            # Check body
            if request.body:
                if request.body.raw and variable_name in self._extract_variable_names(
                    request.body.raw
                ):
                    usage_locations.append(f"{request_path} - Body (raw)")

                if request.body.formdata:
                    for param in request.body.formdata:
                        if param.value and variable_name in self._extract_variable_names(
                            param.value
                        ):
                            usage_locations.append(
                                f"{request_path} - Body form-data '{param.key}'"
                            )

                if request.body.urlencoded:
                    for param in request.body.urlencoded:
                        if param.value and variable_name in self._extract_variable_names(
                            param.value
                        ):
                            usage_locations.append(
                                f"{request_path} - Body urlencoded '{param.key}'"
                            )

            # Check auth
            if request.auth:
                for param in request.auth.parameters:
                    if param.value and variable_name in self._extract_variable_names(
                        str(param.value)
                    ):
                        usage_locations.append(
                            f"{request_path} - Auth parameter '{param.key}'"
                        )

            # Check scripts
            for event in request.events:
                script_content = event.get_script_content()
                if script_content and variable_name in self._extract_variable_names(
                    script_content
                ):
                    usage_locations.append(
                        f"{request_path} - {event.listen} script"
                    )

        return usage_locations

    def _get_request_path(self, request) -> str:
        """Get human-readable path to a request."""
        # Try to build path from parent references if available
        path_parts = [request.name]

        # Walk up parent folders if available
        current = getattr(request, "_parent_folder", None)
        while current:
            path_parts.insert(0, current.name)
            current = getattr(current, "_parent_folder", None)

        return " > ".join(path_parts)

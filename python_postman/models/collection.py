"""
Main Collection class representing a Postman collection.
"""

from typing import List, Optional, Iterator, TYPE_CHECKING, Dict, Any
from .item import Item
from .collection_info import CollectionInfo
from .variable import Variable
from .auth import Auth
from .event import Event

if TYPE_CHECKING:
    from .request import Request
    from .folder import Folder
    from ..execution.executor import RequestExecutor
    from ..execution.results import CollectionExecutionResult
else:
    # Import for runtime use in search methods
    from .folder import Folder


class ValidationResult:
    """Represents the result of collection validation."""

    def __init__(self, is_valid: bool = True, errors: Optional[List[str]] = None):
        """
        Initialize ValidationResult.

        Args:
            is_valid: Whether validation passed
            errors: List of validation error messages
        """
        self.is_valid = is_valid
        self.errors = errors or []

    def add_error(self, error: str) -> None:
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False

    def __repr__(self) -> str:
        return f"ValidationResult(is_valid={self.is_valid}, errors={self.errors})"


class Collection:
    """
    Represents a Postman collection with all its components.

    This is the main entry point for working with parsed collection data.
    """

    def __init__(
        self,
        info: CollectionInfo,
        items: Optional[List[Item]] = None,
        variables: Optional[List[Variable]] = None,
        auth: Optional[Auth] = None,
        events: Optional[List[Event]] = None,
    ):
        """
        Initialize a Collection.

        Args:
            info: Collection metadata
            items: List of items (requests and folders) in the collection
            variables: Optional list of collection-level variables
            auth: Optional collection-level authentication
            events: Optional list of collection-level events
        """
        self.info = info
        self.items = items or []
        self.variables = variables or []
        self.auth = auth
        self.events = events or []

    def validate(self) -> ValidationResult:
        """
        Validate the collection structure and content.

        Returns:
            ValidationResult with validation status and any errors
        """
        result = ValidationResult()

        # Validate collection info
        try:
            self.info.validate()
        except ValueError as e:
            result.add_error(f"Collection info validation failed: {str(e)}")

        # Validate items list
        if not isinstance(self.items, list):
            result.add_error("Collection items must be a list")
        else:
            for i, item in enumerate(self.items):
                if not isinstance(item, Item):
                    result.add_error(f"Item at index {i} is not a valid Item instance")

        # Validate variables list
        if not isinstance(self.variables, list):
            result.add_error("Collection variables must be a list")
        else:
            for i, variable in enumerate(self.variables):
                if not isinstance(variable, Variable):
                    result.add_error(
                        f"Variable at index {i} is not a valid Variable instance"
                    )
                else:
                    try:
                        variable.validate()
                    except ValueError as e:
                        result.add_error(
                            f"Variable '{variable.key}' validation failed: {str(e)}"
                        )

        # Validate auth if present
        if self.auth is not None:
            if not isinstance(self.auth, Auth):
                result.add_error("Collection auth must be an Auth instance")
            else:
                try:
                    self.auth.validate()
                except ValueError as e:
                    result.add_error(f"Collection auth validation failed: {str(e)}")

        # Validate events list
        if not isinstance(self.events, list):
            result.add_error("Collection events must be a list")
        else:
            for i, event in enumerate(self.events):
                if not isinstance(event, Event):
                    result.add_error(
                        f"Event at index {i} is not a valid Event instance"
                    )
                else:
                    try:
                        event.validate()
                    except ValueError as e:
                        result.add_error(
                            f"Event '{event.listen}' validation failed: {str(e)}"
                        )

        # Check for Postman schema version compatibility
        if self.info.schema:
            schema_version = self.info.schema.lower()
            supported_versions = [
                "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
                "https://schema.getpostman.com/json/collection/v2.0.0/collection.json",
            ]

            if not any(version in schema_version for version in supported_versions):
                result.add_error(
                    f"Unsupported schema version: {self.info.schema}. Supported versions: v2.0.0, v2.1.0"
                )

        return result

    @classmethod
    def from_dict(cls, data: dict) -> "Collection":
        """
        Create Collection from dictionary data.

        Args:
            data: Dictionary containing collection data

        Returns:
            Collection instance
        """
        # Import here to avoid circular imports
        from .request import Request
        from .folder import Folder

        # Parse collection info
        info_data = data.get("info", {})
        info = CollectionInfo.from_dict(info_data)

        # Parse items
        items = []
        items_data = data.get("item", [])
        for item_data in items_data:
            if "request" in item_data:
                # This is a request item
                items.append(Request.from_dict(item_data))
            else:
                # This is a folder item
                items.append(Folder.from_dict(item_data))

        # Parse variables
        variables = []
        variables_data = data.get("variable", [])
        for var_data in variables_data:
            variables.append(Variable.from_dict(var_data))

        # Parse auth
        auth = None
        auth_data = data.get("auth")
        if auth_data:
            auth = Auth.from_dict(auth_data)

        # Parse events
        events = []
        events_data = data.get("event", [])
        for event_data in events_data:
            events.append(Event.from_dict(event_data))

        return cls(
            info=info, items=items, variables=variables, auth=auth, events=events
        )

    def to_dict(self) -> dict:
        """
        Convert Collection to dictionary.

        Returns:
            Dictionary representation of Collection
        """
        result = {
            "info": self.info.to_dict(),
            "item": [item.to_dict() for item in self.items],
        }

        if self.variables:
            result["variable"] = [var.to_dict() for var in self.variables]

        if self.auth:
            result["auth"] = self.auth.to_dict()

        if self.events:
            result["event"] = [event.to_dict() for event in self.events]

        return result

    def get_all_requests(self) -> Iterator["Request"]:
        """
        Get all requests in the collection, traversing folders recursively.

        Returns:
            Iterator of all Request objects in the collection
        """
        for item in self.items:
            yield from item.get_requests()

    def get_request_by_name(self, name: str) -> Optional["Request"]:
        """
        Find a request by name.

        Args:
            name: Name of the request to find

        Returns:
            Request object if found, None otherwise
        """
        for request in self.get_all_requests():
            if request.name == name:
                return request
        return None

    def get_folder_by_name(self, name: str) -> Optional["Folder"]:
        """
        Find a folder by name.

        Args:
            name: Name of the folder to find

        Returns:
            Folder object if found, None otherwise
        """

        def _search_folders(items: List[Item]) -> Optional["Folder"]:
            for item in items:
                if isinstance(item, Folder):
                    if item.name == name:
                        return item
                    # Recursively search in subfolders
                    result = _search_folders(item.items)
                    if result:
                        return result
            return None

        return _search_folders(self.items)

    def __repr__(self) -> str:
        return f"Collection(name='{self.info.name}', items={len(self.items)}, variables={len(self.variables)})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Collection):
            return False
        return (
            self.info == other.info
            and self.items == other.items
            and self.variables == other.variables
            and self.auth == other.auth
            and self.events == other.events
        )

    def create_executor(self, **kwargs) -> "RequestExecutor":
        """
        Create a configured executor for this collection.

        This convenience method creates a RequestExecutor instance with
        collection-specific configuration and variable context.

        Args:
            **kwargs: Additional configuration options for RequestExecutor

        Returns:
            RequestExecutor: Configured executor instance

        Raises:
            ImportError: If execution module is not available
        """
        try:
            from ..execution.executor import RequestExecutor
        except ImportError as e:
            raise ImportError(
                "Execution functionality requires httpx. Install with: pip install httpx"
            ) from e

        # Extract collection variables for default configuration
        collection_vars = {}
        if self.variables:
            for var in self.variables:
                if hasattr(var, "key") and hasattr(var, "value"):
                    collection_vars[var.key] = var.value

        # Set up default variable overrides if not provided
        if "variable_overrides" not in kwargs:
            kwargs["variable_overrides"] = collection_vars

        return RequestExecutor(**kwargs)

    async def execute(
        self,
        executor: Optional["RequestExecutor"] = None,
        parallel: bool = False,
        stop_on_error: bool = False,
    ) -> "CollectionExecutionResult":
        """
        Execute all requests in this collection.

        This method executes all requests in the collection using the provided
        executor or creating a new one if none is provided. It supports both
        sequential and parallel execution modes.

        Args:
            executor: Optional RequestExecutor instance to use for execution.
                     If None, a new executor will be created.
            parallel: Whether to execute requests in parallel (default: False)
            stop_on_error: Whether to stop execution on first error (default: False)

        Returns:
            CollectionExecutionResult: Result of the collection execution

        Raises:
            ImportError: If execution module is not available
        """
        try:
            from ..execution.executor import RequestExecutor
        except ImportError as e:
            raise ImportError(
                "Execution functionality requires httpx. Install with: pip install httpx"
            ) from e

        # Create executor if not provided
        if executor is None:
            executor = self.create_executor()

        # Execute the collection
        return await executor.execute_collection(
            collection=self,
            parallel=parallel,
            stop_on_error=stop_on_error,
        )

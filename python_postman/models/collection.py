"""
Main Collection class representing a Postman collection.
"""

from typing import List, Optional, Iterator, TYPE_CHECKING, Dict, Any
from .item import Item
from .collection_info import CollectionInfo
from .variable import Variable
from .auth import Auth
from .event import Event
from .schema import SchemaValidator, SchemaVersion

if TYPE_CHECKING:
    from .request import Request
    from .folder import Folder
    from ..execution.executor import RequestExecutor
    from ..execution.results import CollectionExecutionResult
    from ..search.query import RequestQuery
    from ..statistics.collector import CollectionStatistics
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
        
        # Detect and store schema version
        self.schema_version = SchemaValidator.detect_version(info.schema)

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

        # Validate schema version using SchemaValidator
        is_valid, error_message = SchemaValidator.validate_version(self.info.schema)
        if not is_valid:
            result.add_error(error_message)

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

    def get_requests(self) -> Iterator["Request"]:
        """
        Get all requests in the collection, traversing folders recursively.

        Returns:
            Iterator of all Request objects in the collection
        """
        for item in self.items:
            yield from item.get_requests()

    def list_requests(self) -> List[str]:
        """
        Get a list of all request names in the collection.

        Returns:
            List of request names
        """
        return [request.name for request in self.get_requests()]

    def get_request_by_name(self, name: str) -> Optional["Request"]:
        """
        Find a request by name.

        Args:
            name: Name of the request to find

        Returns:
            Request object if found, None otherwise
        """
        for request in self.get_requests():
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

    def get_variables(self) -> Dict[str, Any]:
        """
        Get all collection variables as a dictionary.

        Returns:
            Dictionary with variable keys as keys and variable values as values.
            Disabled variables are excluded from the result.
        """
        variables_dict = {}
        for variable in self.variables:
            if not variable.disabled:
                variables_dict[variable.key] = variable.value
        return variables_dict

    def search(self) -> "RequestQuery":
        """
        Create a new search query builder for this collection.
        
        Returns:
            RequestQuery: Query builder for searching and filtering requests
            
        Examples:
            >>> # Find all POST requests
            >>> results = collection.search().by_method("POST").execute()
            >>> 
            >>> # Find requests to a specific host with bearer auth
            >>> results = collection.search() \\
            ...     .by_host("api.example.com") \\
            ...     .by_auth_type("bearer") \\
            ...     .execute()
            >>> 
            >>> # Find requests with test scripts
            >>> results = collection.search().has_scripts("test").execute()
            >>> for result in results:
            ...     print(f"{result.full_path}: {result.request.name}")
            >>> 
            >>> # Complex query with multiple filters
            >>> results = collection.search() \\
            ...     .by_method("GET") \\
            ...     .by_url_pattern(r"/api/v\\d+/users") \\
            ...     .in_folder("User Management") \\
            ...     .execute()
        """
        from ..search.query import RequestQuery
        return RequestQuery(self)

    def get_statistics(self) -> "CollectionStatistics":
        """
        Get statistics and metadata about this collection.
        
        Returns:
            CollectionStatistics: Statistics analyzer for this collection
            
        Examples:
            >>> # Get basic statistics
            >>> stats = collection.get_statistics()
            >>> data = stats.collect()
            >>> print(f"Total requests: {data['total_requests']}")
            >>> print(f"Total folders: {data['total_folders']}")
            >>> print(f"Max depth: {data['max_nesting_depth']}")
            >>> 
            >>> # Get breakdown by method
            >>> by_method = stats.count_by_method()
            >>> print(f"GET: {by_method.get('GET', 0)}")
            >>> print(f"POST: {by_method.get('POST', 0)}")
            >>> 
            >>> # Export to JSON
            >>> json_output = stats.to_json()
            >>> with open("collection_stats.json", "w") as f:
            ...     f.write(json_output)
            >>> 
            >>> # Export to CSV
            >>> csv_output = stats.to_csv()
            >>> with open("collection_stats.csv", "w") as f:
            ...     f.write(csv_output)
        """
        from ..statistics.collector import CollectionStatistics
        return CollectionStatistics(self)

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

        Examples:
            Simple collection execution:

            >>> import asyncio
            >>> result = await collection.execute()
            >>> print(f"Executed {result.total_requests} requests")
            >>> print(f"Success rate: {result.successful_requests}/{result.total_requests}")

            Parallel execution:

            >>> result = await collection.execute(parallel=True)
            >>> print(f"Parallel execution completed in {result.total_time_ms:.2f}ms")

            With custom executor:

            >>> from python_postman.execution import RequestExecutor
            >>>
            >>> executor = RequestExecutor(
            ...     client_config={"timeout": 60.0},
            ...     global_headers={"User-Agent": "my-test-suite/1.0"}
            ... )
            >>> result = await collection.execute(
            ...     executor=executor,
            ...     parallel=True,
            ...     stop_on_error=True
            ... )

            Error handling:

            >>> result = await collection.execute(stop_on_error=False)
            >>> if result.failed_requests > 0:
            ...     print(f"⚠️  {result.failed_requests} requests failed")
            ...     for exec_result in result.results:
            ...         if not exec_result.success:
            ...             print(f"  ❌ {exec_result.request.name}: {exec_result.error}")
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

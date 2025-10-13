"""
Request class representing HTTP requests in a collection.
"""

from typing import List, Optional, Iterator, Dict, Any, TYPE_CHECKING
from .item import Item
from .url import Url
from .header import Header
from .body import Body
from .auth import Auth
from .event import Event
from .response import ExampleResponse
from ..types.http_methods import HttpMethodType, HttpMethod

# Import execution types only for type checking to avoid circular imports
if TYPE_CHECKING:
    from ..execution import (
        RequestExecutor,
        ExecutionContext,
        ExecutionResult,
        RequestExtensions,
    )
    from .folder import Folder
    from .collection import Collection
    from ..introspection.auth_resolver import ResolvedAuth


class Request(Item):
    """
    Represents an HTTP request within a Postman collection.
    """

    def __init__(
        self,
        name: str,
        method: HttpMethodType,
        url: Url,
        description: Optional[str] = None,
        headers: Optional[List[Header]] = None,
        body: Optional[Body] = None,
        auth: Optional[Auth] = None,
        events: Optional[List[Event]] = None,
        responses: Optional[List[ExampleResponse]] = None,
    ):
        """
        Initialize a Request.

        Args:
            name: Name of the request
            method: HTTP method (GET, POST, etc.)
            url: Request URL object
            description: Optional description
            headers: Optional list of headers
            body: Optional request body
            auth: Optional authentication override
            events: Optional list of events (pre-request scripts, tests)
            responses: Optional list of example responses
        """
        super().__init__(name, description)
        self._validate_method(method)
        self.method = method
        self.url = url
        self.headers = headers or []
        self.body = body
        self.auth = auth
        self.events = events or []
        self.responses = responses or []
        
        # Hierarchy references for authentication resolution
        self._parent_folder: Optional["Folder"] = None
        self._collection: Optional["Collection"] = None

    def _validate_method(self, method: str) -> None:
        """
        Validate HTTP method at runtime.
        
        Args:
            method: HTTP method to validate
            
        Raises:
            ValueError: If the method is not a valid HTTP method
        """
        if not method or not isinstance(method, str):
            raise ValueError(
                "HTTP method must be a non-empty string. "
                f"Valid methods are: {', '.join(m.value for m in HttpMethod)}"
            )
        
        try:
            HttpMethod(method.upper())
        except ValueError:
            valid_methods = [m.value for m in HttpMethod]
            raise ValueError(
                f"Invalid HTTP method '{method}'. "
                f"Valid methods are: {', '.join(valid_methods)}"
            ) from None

    def get_requests(self) -> Iterator["Request"]:
        """
        Get requests contained in this item (returns self for Request objects).

        Returns:
            Iterator containing only this request
        """
        yield self

    @classmethod
    def from_dict(cls, data: dict) -> "Request":
        """
        Create Request from dictionary data.

        Args:
            data: Dictionary containing request data

        Returns:
            Request instance
        """
        name = data.get("name", "")

        # Parse request details
        request_data = data.get("request", {})
        method = request_data.get("method", "GET")

        # Parse URL
        url_data = request_data.get("url", {})
        if isinstance(url_data, str):
            url = Url.from_string(url_data)
        else:
            url = Url.from_dict(url_data)

        # Parse headers
        headers = []
        headers_data = request_data.get("header", [])
        for header_data in headers_data:
            headers.append(Header.from_dict(header_data))

        # Parse body
        body = None
        body_data = request_data.get("body")
        if body_data:
            body = Body.from_dict(body_data)

        # Parse auth
        auth = None
        auth_data = request_data.get("auth")
        if auth_data:
            auth = Auth.from_dict(auth_data)

        # Parse events
        events = []
        events_data = data.get("event", [])
        for event_data in events_data:
            events.append(Event.from_dict(event_data))

        # Parse example responses
        responses = []
        responses_data = data.get("response", [])
        for response_data in responses_data:
            responses.append(ExampleResponse.from_dict(response_data))

        return cls(
            name=name,
            method=method,
            url=url,
            description=data.get("description"),
            headers=headers,
            body=body,
            auth=auth,
            events=events,
            responses=responses,
        )

    def to_dict(self) -> dict:
        """
        Convert Request to dictionary.

        Returns:
            Dictionary representation of Request
        """
        result = {
            "name": self.name,
            "request": {
                "method": self.method,
                "header": [header.to_dict() for header in self.headers],
                "url": self.url.to_dict(),
            },
        }

        if self.description:
            result["description"] = self.description

        if self.body:
            result["request"]["body"] = self.body.to_dict()

        if self.auth:
            result["request"]["auth"] = self.auth.to_dict()

        if self.events:
            result["event"] = [event.to_dict() for event in self.events]

        if self.responses:
            result["response"] = [response.to_dict() for response in self.responses]

        return result

    def add_response(self, response: ExampleResponse) -> None:
        """
        Add an example response to this request.

        Args:
            response: ExampleResponse to add
        """
        self.responses.append(response)

    def get_response_by_name(self, name: str) -> Optional[ExampleResponse]:
        """
        Find an example response by name.

        Args:
            name: Name of the response to find

        Returns:
            ExampleResponse if found, None otherwise
        """
        for response in self.responses:
            if response.name == name:
                return response
        return None

    def set_parent(self, parent: Optional["Folder"]) -> None:
        """
        Set parent folder for hierarchy traversal.
        
        Args:
            parent: Parent folder or None if this is a top-level request
        """
        self._parent_folder = parent

    def set_collection(self, collection: Optional["Collection"]) -> None:
        """
        Set collection reference for hierarchy traversal.
        
        Args:
            collection: Collection containing this request
        """
        self._collection = collection

    def get_effective_auth(
        self,
        parent_folder: Optional["Folder"] = None,
        collection: Optional["Collection"] = None
    ) -> "ResolvedAuth":
        """
        Get the effective authentication for this request.
        
        Resolves authentication by walking up the hierarchy:
        Request auth > Folder auth > Collection auth
        
        Args:
            parent_folder: Optional parent folder to use for resolution.
                          If not provided, uses self._parent_folder
            collection: Optional collection to use for resolution.
                       If not provided, uses self._collection
        
        Returns:
            ResolvedAuth: Contains the resolved auth, its source, and hierarchy path
            
        Examples:
            >>> # Get effective auth using stored hierarchy references
            >>> resolved = request.get_effective_auth()
            >>> print(f"Auth type: {resolved.auth.type if resolved.auth else 'None'}")
            >>> print(f"Source: {resolved.source.value}")
            >>> 
            >>> # Get effective auth with explicit hierarchy
            >>> resolved = request.get_effective_auth(
            ...     parent_folder=my_folder,
            ...     collection=my_collection
            ... )
            >>> if resolved.auth:
            ...     print(f"Using {resolved.auth.type} auth from {resolved.source.value}")
        """
        from ..introspection.auth_resolver import AuthResolver
        
        # Use provided arguments or fall back to stored references
        folder = parent_folder if parent_folder is not None else self._parent_folder
        coll = collection if collection is not None else self._collection
        
        return AuthResolver.resolve_auth(self, folder, coll)

    # Convenience methods for checking request characteristics

    def has_body(self) -> bool:
        """
        Check if request has a body.
        
        Returns:
            True if the request has a body with content, False otherwise
            
        Examples:
            >>> if request.has_body():
            ...     print(f"Body mode: {request.body.mode}")
        """
        return self.body is not None and bool(self.body.raw or self.body.formdata or self.body.urlencoded)

    def has_auth(self) -> bool:
        """
        Check if request has authentication configured.
        
        Returns:
            True if the request has authentication, False otherwise
            
        Examples:
            >>> if request.has_auth():
            ...     print(f"Auth type: {request.auth.type}")
        """
        return self.auth is not None

    def has_headers(self) -> bool:
        """
        Check if request has headers.
        
        Returns:
            True if the request has one or more headers, False otherwise
            
        Examples:
            >>> if request.has_headers():
            ...     for header in request.headers:
            ...         print(f"{header.key}: {header.value}")
        """
        return bool(self.headers)

    def has_prerequest_script(self) -> bool:
        """
        Check if request has pre-request scripts.
        
        Returns:
            True if the request has pre-request scripts, False otherwise
            
        Examples:
            >>> if request.has_prerequest_script():
            ...     print("Request has pre-request script")
        """
        return any(event.listen == "prerequest" for event in self.events)

    def has_test_script(self) -> bool:
        """
        Check if request has test scripts.
        
        Returns:
            True if the request has test scripts, False otherwise
            
        Examples:
            >>> if request.has_test_script():
            ...     print("Request has test script")
        """
        return any(event.listen == "test" for event in self.events)

    def get_content_type(self) -> Optional[str]:
        """
        Get the Content-Type header value.
        
        Returns:
            Content-Type header value if present, None otherwise
            
        Examples:
            >>> content_type = request.get_content_type()
            >>> if content_type:
            ...     print(f"Content-Type: {content_type}")
        """
        for header in self.headers:
            if header.key.lower() == "content-type":
                return header.value
        return None

    def is_idempotent(self) -> bool:
        """
        Check if request method is idempotent.
        
        Idempotent methods: GET, HEAD, PUT, DELETE, OPTIONS
        These methods can be called multiple times with the same result.
        
        Returns:
            True if the request method is idempotent, False otherwise
            
        Examples:
            >>> if request.is_idempotent():
            ...     print("Safe to retry this request")
        """
        idempotent_methods = {"GET", "HEAD", "PUT", "DELETE", "OPTIONS"}
        return self.method.upper() in idempotent_methods

    def is_cacheable(self) -> bool:
        """
        Check if request method is cacheable.
        
        Cacheable methods: GET, HEAD
        These methods can have their responses cached by default.
        
        Returns:
            True if the request method is cacheable, False otherwise
            
        Examples:
            >>> if request.is_cacheable():
            ...     print("Response can be cached")
        """
        cacheable_methods = {"GET", "HEAD"}
        return self.method.upper() in cacheable_methods

    def is_safe(self) -> bool:
        """
        Check if request method is safe.
        
        Safe methods: GET, HEAD, OPTIONS
        These methods should not modify server state.
        
        Returns:
            True if the request method is safe, False otherwise
            
        Examples:
            >>> if request.is_safe():
            ...     print("Request is read-only")
        """
        safe_methods = {"GET", "HEAD", "OPTIONS"}
        return self.method.upper() in safe_methods

    async def execute(
        self,
        executor: Optional["RequestExecutor"] = None,
        context: Optional["ExecutionContext"] = None,
        substitutions: Optional[Dict[str, Any]] = None,
        extensions: Optional["RequestExtensions"] = None,
    ) -> "ExecutionResult":
        """
        Execute this request asynchronously.

        This is a convenience method that creates a default executor and context
        if not provided, making it easy to execute individual requests.

        Args:
            executor: Optional RequestExecutor instance. If not provided, a default one will be created
            context: Optional ExecutionContext. If not provided, an empty context will be created
            substitutions: Optional runtime variable substitutions
            extensions: Optional runtime request extensions

        Returns:
            ExecutionResult: Result of the request execution

        Raises:
            ExecutionError: If httpx is not available or execution fails

        Examples:
            Simple execution:

            >>> import asyncio
            >>> result = await request.execute()
            >>> if result.success:
            ...     print(f"Status: {result.response.status_code}")
            ...     print(f"Response: {result.response.text}")

            With custom executor and context:

            >>> from python_postman.execution import RequestExecutor, ExecutionContext
            >>>
            >>> executor = RequestExecutor(
            ...     client_config={"timeout": 60.0},
            ...     global_headers={"User-Agent": "my-app/1.0"}
            ... )
            >>> context = ExecutionContext(
            ...     environment_variables={"base_url": "https://api.example.com"}
            ... )
            >>> result = await request.execute(executor=executor, context=context)

            With runtime substitutions and extensions:

            >>> from python_postman.execution import RequestExtensions
            >>>
            >>> result = await request.execute(
            ...     substitutions={"api_key": "secret-key", "user_id": "12345"},
            ...     extensions=RequestExtensions(
            ...         header_extensions={"X-Request-ID": "req-123"},
            ...         param_extensions={"debug": "true"}
            ...     )
            ... )
        """
        # Import here to avoid circular imports and handle optional dependency
        try:
            from ..execution import RequestExecutor, ExecutionContext
        except ImportError as e:
            raise ImportError(
                "Execution functionality requires httpx. Install with: pip install httpx"
            ) from e

        # Create default executor if not provided
        if executor is None:
            executor = RequestExecutor()

        # Create default context if not provided
        if context is None:
            context = ExecutionContext()

        # Execute the request
        return await executor.execute_request(
            request=self,
            context=context,
            substitutions=substitutions,
            extensions=extensions,
        )

    def execute_sync(
        self,
        executor: Optional["RequestExecutor"] = None,
        context: Optional["ExecutionContext"] = None,
        substitutions: Optional[Dict[str, Any]] = None,
        extensions: Optional["RequestExtensions"] = None,
    ) -> "ExecutionResult":
        """
        Execute this request synchronously.

        This is a convenience method that creates a default executor and context
        if not provided, making it easy to execute individual requests.

        Args:
            executor: Optional RequestExecutor instance. If not provided, a default one will be created
            context: Optional ExecutionContext. If not provided, an empty context will be created
            substitutions: Optional runtime variable substitutions
            extensions: Optional runtime request extensions

        Returns:
            ExecutionResult: Result of the request execution

        Raises:
            ExecutionError: If httpx is not available or execution fails

        Examples:
            Simple synchronous execution:

            >>> result = request.execute_sync()
            >>> if result.success:
            ...     print(f"Status: {result.response.status_code}")
            ...     print(f"Response time: {result.response.elapsed_ms:.2f}ms")

            With custom executor:

            >>> from python_postman.execution import RequestExecutor
            >>>
            >>> with RequestExecutor(client_config={"timeout": 10.0}) as executor:
            ...     result = request.execute_sync(executor=executor)
            ...     print(f"Request completed: {result.success}")

            With variables and extensions:

            >>> from python_postman.execution import ExecutionContext, RequestExtensions
            >>>
            >>> context = ExecutionContext(
            ...     environment_variables={"api_key": "secret", "base_url": "https://api.example.com"}
            ... )
            >>> extensions = RequestExtensions(
            ...     header_extensions={"X-Client": "python-postman"}
            ... )
            >>> result = request.execute_sync(
            ...     context=context,
            ...     extensions=extensions
            ... )
        """
        # Import here to avoid circular imports and handle optional dependency
        try:
            from ..execution import RequestExecutor, ExecutionContext
        except ImportError as e:
            raise ImportError(
                "Execution functionality requires httpx. Install with: pip install httpx"
            ) from e

        # Create default executor if not provided
        if executor is None:
            executor = RequestExecutor()

        # Create default context if not provided
        if context is None:
            context = ExecutionContext()

        # Execute the request
        return executor.execute_request_sync(
            request=self,
            context=context,
            substitutions=substitutions,
            extensions=extensions,
        )

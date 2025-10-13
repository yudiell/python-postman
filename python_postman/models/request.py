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

# Import execution types only for type checking to avoid circular imports
if TYPE_CHECKING:
    from ..execution import (
        RequestExecutor,
        ExecutionContext,
        ExecutionResult,
        RequestExtensions,
    )


class Request(Item):
    """
    Represents an HTTP request within a Postman collection.
    """

    def __init__(
        self,
        name: str,
        method: str,
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
        self.method = method
        self.url = url
        self.headers = headers or []
        self.body = body
        self.auth = auth
        self.events = events or []
        self.responses = responses or []

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

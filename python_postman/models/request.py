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
        """
        super().__init__(name, description)
        self.method = method
        self.url = url
        self.headers = headers or []
        self.body = body
        self.auth = auth
        self.events = events or []

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

        return cls(
            name=name,
            method=method,
            url=url,
            description=data.get("description"),
            headers=headers,
            body=body,
            auth=auth,
            events=events,
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

        return result

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

        Example:
            ```python
            # Simple execution
            result = await request.execute()

            # With custom variables
            result = await request.execute(
                substitutions={"api_key": "my-key"},
                extensions=RequestExtensions(
                    header_extensions={"X-Custom": "value"}
                )
            )
            ```
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

        Example:
            ```python
            # Simple execution
            result = request.execute_sync()

            # With custom variables
            result = request.execute_sync(
                substitutions={"api_key": "my-key"},
                extensions=RequestExtensions(
                    header_extensions={"X-Custom": "value"}
                )
            )
            ```
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

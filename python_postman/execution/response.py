"""Response wrapper for HTTP execution results."""

from typing import Any, Dict, Optional
import json


class ExecutionResponse:
    """Wraps httpx response with timing information and convenience methods.

    Examples:
        Basic response access:

        >>> result = await executor.execute_request(request, context)
        >>> if result.success:
        ...     response = result.response
        ...     print(f"Status: {response.status_code}")
        ...     print(f"Headers: {response.headers}")
        ...     print(f"Body: {response.text}")
        ...     print(f"Time: {response.elapsed_ms:.2f}ms")

        JSON response handling:

        >>> if response.headers.get("content-type", "").startswith("application/json"):
        ...     try:
        ...         data = response.json
        ...         print(f"User ID: {data['id']}")
        ...         print(f"Name: {data['name']}")
        ...     except json.JSONDecodeError:
        ...         print("Invalid JSON response")

        Status code checking:

        >>> if response.is_success():
        ...     print("Request successful")
        ... elif response.is_client_error():
        ...     print(f"Client error: {response.status_code}")
        ... elif response.is_server_error():
        ...     print(f"Server error: {response.status_code}")

        Converting to dictionary for scripts:

        >>> response_dict = response.to_dict()
        >>> # This format is used by test scripts
        >>> print(response_dict["status"])
        >>> print(response_dict["json"]["user_id"])
    """

    def __init__(
        self,
        httpx_response: Any,  # httpx.Response type hint avoided to prevent import dependency
        request_start_time: float,
        request_end_time: float,
    ):
        """Initialize with httpx response and timing info.

        Args:
            httpx_response: The httpx.Response object
            request_start_time: Timestamp when request started (time.time())
            request_end_time: Timestamp when request completed (time.time())
        """
        self._response = httpx_response
        self._request_start_time = request_start_time
        self._request_end_time = request_end_time

    @property
    def status_code(self) -> int:
        """HTTP status code."""
        return self._response.status_code

    @property
    def headers(self) -> Dict[str, str]:
        """Response headers as dictionary."""
        # Handle both dict-like objects and iterables of key-value pairs
        headers = self._response.headers
        if hasattr(headers, "items"):
            return dict(headers.items())
        else:
            return dict(headers)

    @property
    def text(self) -> str:
        """Response body as text."""
        return self._response.text

    @property
    def json(self) -> Any:
        """Response body as JSON.

        Returns:
            Parsed JSON data

        Raises:
            json.JSONDecodeError: If response body is not valid JSON
        """
        return self._response.json()

    @property
    def content(self) -> bytes:
        """Response body as bytes."""
        return self._response.content

    @property
    def elapsed_ms(self) -> float:
        """Request duration in milliseconds."""
        return (self._request_end_time - self._request_start_time) * 1000

    @property
    def elapsed_seconds(self) -> float:
        """Request duration in seconds."""
        return self._request_end_time - self._request_start_time

    @property
    def url(self) -> str:
        """Request URL."""
        return str(self._response.url)

    @property
    def request_method(self) -> str:
        """HTTP method used for the request."""
        return self._response.request.method

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary for script access.

        Returns:
            Dictionary containing response data suitable for test scripts
        """
        response_dict = {
            "status": self.status_code,
            "headers": self.headers,
            "body": self.text,
            "url": self.url,
            "method": self.request_method,
            "elapsed_ms": self.elapsed_ms,
            "elapsed_seconds": self.elapsed_seconds,
        }

        # Try to include JSON data if response is JSON
        try:
            response_dict["json"] = self.json
        except (json.JSONDecodeError, ValueError):
            # Not JSON or invalid JSON, skip
            pass

        return response_dict

    def is_success(self) -> bool:
        """Check if response indicates success (2xx status code)."""
        return 200 <= self.status_code < 300

    def is_redirect(self) -> bool:
        """Check if response indicates redirect (3xx status code)."""
        return 300 <= self.status_code < 400

    def is_client_error(self) -> bool:
        """Check if response indicates client error (4xx status code)."""
        return 400 <= self.status_code < 500

    def is_server_error(self) -> bool:
        """Check if response indicates server error (5xx status code)."""
        return 500 <= self.status_code < 600

    def __repr__(self) -> str:
        """String representation of the response."""
        return f"ExecutionResponse(status={self.status_code}, elapsed_ms={self.elapsed_ms:.2f})"

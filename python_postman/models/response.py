"""Response model for Postman collection example responses."""

from typing import List, Optional, Dict, Any
import json
from .header import Header
from .cookie import Cookie, CookieJar


class Response:
    """Represents an HTTP response with all attributes."""

    def __init__(
        self,
        name: str,
        status: str,
        code: int,
        headers: Optional[List[Header]] = None,
        body: Optional[str] = None,
        cookie: Optional[List[Dict[str, Any]]] = None,
        _postman_previewlanguage: Optional[str] = None,
        header: Optional[List[Dict[str, Any]]] = None,
        _time: Optional[int] = None,
        response_time: Optional[int] = None,
    ):
        """
        Initialize a Response.

        Args:
            name: Name of the response
            status: HTTP status text (e.g., "OK", "Not Found")
            code: HTTP status code (e.g., 200, 404)
            headers: List of Header objects
            body: Response body as string
            cookie: List of cookie dictionaries
            _postman_previewlanguage: Language hint for preview (e.g., "json", "xml")
            header: Raw header data (for parsing)
            _time: Response time in milliseconds (deprecated field)
            response_time: Response time in milliseconds
        """
        self.name = name
        self.status = status
        self.code = code
        self.headers = headers or []
        self.body = body
        self.cookie = cookie or []
        self._postman_previewlanguage = _postman_previewlanguage
        self._time = _time
        self.response_time = response_time

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Response":
        """
        Parse response from Postman collection JSON.

        Args:
            data: Dictionary containing response data

        Returns:
            Response instance
        """
        # Parse headers
        headers = []
        headers_data = data.get("header", [])
        if headers_data:
            for header_data in headers_data:
                if isinstance(header_data, dict):
                    headers.append(Header.from_dict(header_data))

        return cls(
            name=data.get("name", ""),
            status=data.get("status", ""),
            code=data.get("code", 0),
            headers=headers,
            body=data.get("body"),
            cookie=data.get("cookie", []),
            _postman_previewlanguage=data.get("_postman_previewlanguage"),
            _time=data.get("_time"),
            response_time=data.get("responseTime"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize response back to Postman collection JSON format.

        Returns:
            Dictionary representation of Response
        """
        result = {
            "name": self.name,
            "status": self.status,
            "code": self.code,
        }

        if self.headers:
            result["header"] = [header.to_dict() for header in self.headers]

        if self.body is not None:
            result["body"] = self.body

        if self.cookie:
            result["cookie"] = self.cookie

        if self._postman_previewlanguage:
            result["_postman_previewlanguage"] = self._postman_previewlanguage

        if self._time is not None:
            result["_time"] = self._time

        if self.response_time is not None:
            result["responseTime"] = self.response_time

        return result

    def get_json(self) -> Optional[Dict[str, Any]]:
        """
        Parse body as JSON if possible.

        Returns:
            Parsed JSON as dictionary, or None if body is not valid JSON
        """
        if not self.body:
            return None

        try:
            return json.loads(self.body)
        except (json.JSONDecodeError, TypeError):
            return None

    def get_content_type(self) -> Optional[str]:
        """
        Get the Content-Type header value.

        Returns:
            Content-Type value or None if not present
        """
        for header in self.headers:
            if header.key.lower() == "content-type":
                return header.value
        return None

    def is_json(self) -> bool:
        """
        Check if response body is JSON format.

        Returns:
            True if body appears to be JSON
        """
        content_type = self.get_content_type()
        if content_type and "json" in content_type.lower():
            return True

        # Also check preview language hint
        if self._postman_previewlanguage == "json":
            return True

        # Try to parse as JSON
        return self.get_json() is not None

    def is_xml(self) -> bool:
        """
        Check if response body is XML format.

        Returns:
            True if body appears to be XML
        """
        content_type = self.get_content_type()
        if content_type and "xml" in content_type.lower():
            return True

        if self._postman_previewlanguage == "xml":
            return True

        # Basic XML detection
        if self.body and self.body.strip().startswith("<?xml"):
            return True

        return False

    def is_html(self) -> bool:
        """
        Check if response body is HTML format.

        Returns:
            True if body appears to be HTML
        """
        content_type = self.get_content_type()
        if content_type and "html" in content_type.lower():
            return True

        if self._postman_previewlanguage == "html":
            return True

        # Basic HTML detection
        if self.body and self.body.strip().lower().startswith("<!doctype html"):
            return True
        if self.body and self.body.strip().lower().startswith("<html"):
            return True

        return False

    def get_cookies(self) -> CookieJar:
        """
        Extract cookies from response.

        Cookies can come from two sources:
        1. Set-Cookie headers
        2. Postman's cookie array (stored in self.cookie)

        Returns:
            CookieJar containing all cookies from the response
        """
        jar = CookieJar()

        # Extract from Set-Cookie headers
        for header in self.headers:
            if header.key.lower() == "set-cookie":
                try:
                    cookie = Cookie.from_header(header.value)
                    jar.add(cookie)
                except (ValueError, AttributeError):
                    # Skip invalid cookies
                    pass

        # Extract from Postman cookie array
        if self.cookie:
            for cookie_data in self.cookie:
                if isinstance(cookie_data, dict):
                    # Validate that required fields exist
                    if "name" not in cookie_data or "value" not in cookie_data:
                        continue
                    try:
                        cookie = Cookie.from_dict(cookie_data)
                        jar.add(cookie)
                    except (ValueError, KeyError, TypeError):
                        # Skip invalid cookies
                        pass

        return jar

    def __repr__(self) -> str:
        return f"Response(name='{self.name}', code={self.code}, status='{self.status}')"


class ExampleResponse(Response):
    """Represents a saved example response in a collection."""

    def __init__(
        self,
        original_request: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize an ExampleResponse.

        Args:
            original_request: The original request that generated this response
            id: Unique identifier for the example
            **kwargs: Additional arguments passed to Response
        """
        super().__init__(**kwargs)
        self.original_request = original_request
        self.id = id

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExampleResponse":
        """
        Parse example response from Postman collection JSON.

        Args:
            data: Dictionary containing example response data

        Returns:
            ExampleResponse instance
        """
        # Parse the response portion
        response_data = data.get("response", {})

        # Parse headers
        headers = []
        headers_data = response_data.get("header", [])
        if headers_data:
            for header_data in headers_data:
                if isinstance(header_data, dict):
                    headers.append(Header.from_dict(header_data))

        return cls(
            name=data.get("name", ""),
            status=response_data.get("status", ""),
            code=response_data.get("code", 0),
            headers=headers,
            body=response_data.get("body"),
            cookie=response_data.get("cookie", []),
            _postman_previewlanguage=response_data.get("_postman_previewlanguage"),
            _time=response_data.get("_time"),
            response_time=response_data.get("responseTime"),
            original_request=data.get("originalRequest"),
            id=data.get("id"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize example response back to Postman collection JSON format.

        Returns:
            Dictionary representation of ExampleResponse
        """
        result = {"name": self.name}

        if self.id:
            result["id"] = self.id

        if self.original_request:
            result["originalRequest"] = self.original_request

        # Build response object
        response_obj = {
            "status": self.status,
            "code": self.code,
        }

        if self.headers:
            response_obj["header"] = [header.to_dict() for header in self.headers]

        if self.body is not None:
            response_obj["body"] = self.body

        if self.cookie:
            response_obj["cookie"] = self.cookie

        if self._postman_previewlanguage:
            response_obj["_postman_previewlanguage"] = self._postman_previewlanguage

        if self._time is not None:
            response_obj["_time"] = self._time

        if self.response_time is not None:
            response_obj["responseTime"] = self.response_time

        result["response"] = response_obj

        return result

    def __repr__(self) -> str:
        return f"ExampleResponse(name='{self.name}', code={self.code}, status='{self.status}')"

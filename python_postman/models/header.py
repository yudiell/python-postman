"""Header model for Postman collection HTTP headers."""

from typing import Optional, List, Dict, Any


class Header:
    """Represents an HTTP header with key-value pair handling."""

    def __init__(
        self,
        key: str,
        value: Optional[str] = None,
        description: Optional[str] = None,
        disabled: bool = False,
        type: Optional[str] = None,
    ):
        """
        Initialize Header.

        Args:
            key: Header key/name (required)
            value: Header value (optional)
            description: Header description (optional)
            disabled: Whether header is disabled (default: False)
            type: Header type (optional, used by Postman for categorization)
        """
        self.key = key
        self.value = value
        self.description = description
        self.disabled = disabled
        self.type = type

    def is_active(self) -> bool:
        """
        Check if header is active (not disabled and has a key).

        Returns:
            True if header is active
        """
        return not self.disabled and bool(self.key)

    def get_effective_value(
        self, variable_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Get the effective header value, resolving variables if context is provided.

        Args:
            variable_context: Dictionary of variables for resolution

        Returns:
            Resolved header value or None if disabled/empty
        """
        if self.disabled or not self.value:
            return None

        if not variable_context:
            return self.value

        # Resolve variable placeholders
        resolved_value = self.value
        for var_name, var_value in variable_context.items():
            placeholder = f"{{{{{var_name}}}}}"
            if placeholder in resolved_value:
                resolved_value = resolved_value.replace(placeholder, str(var_value))

        return resolved_value

    def normalize_key(self) -> str:
        """
        Normalize header key to standard HTTP header format.

        Returns:
            Normalized header key (Title-Case)
        """
        if not self.key:
            return ""

        # Convert to title case with proper handling of hyphens
        return "-".join(word.capitalize() for word in self.key.lower().split("-"))

    def is_standard_header(self) -> bool:
        """
        Check if this is a standard HTTP header.

        Returns:
            True if this is a recognized standard HTTP header
        """
        standard_headers = {
            "accept",
            "accept-charset",
            "accept-encoding",
            "accept-language",
            "accept-ranges",
            "access-control-allow-credentials",
            "access-control-allow-headers",
            "access-control-allow-methods",
            "access-control-allow-origin",
            "access-control-expose-headers",
            "access-control-max-age",
            "access-control-request-headers",
            "access-control-request-method",
            "age",
            "allow",
            "authorization",
            "cache-control",
            "connection",
            "content-disposition",
            "content-encoding",
            "content-language",
            "content-length",
            "content-location",
            "content-range",
            "content-type",
            "cookie",
            "date",
            "etag",
            "expect",
            "expires",
            "from",
            "host",
            "if-match",
            "if-modified-since",
            "if-none-match",
            "if-range",
            "if-unmodified-since",
            "last-modified",
            "location",
            "max-forwards",
            "origin",
            "pragma",
            "proxy-authenticate",
            "proxy-authorization",
            "range",
            "referer",
            "retry-after",
            "server",
            "set-cookie",
            "te",
            "trailer",
            "transfer-encoding",
            "upgrade",
            "user-agent",
            "vary",
            "via",
            "warning",
            "www-authenticate",
            "x-forwarded-for",
            "x-forwarded-host",
            "x-forwarded-proto",
            "x-real-ip",
        }

        return self.key.lower() in standard_headers

    def validate(self) -> bool:
        """
        Validate the header.

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        if not self.key or not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("Header key is required and must be a non-empty string")

        if self.value is not None and not isinstance(self.value, str):
            raise ValueError("Header value must be a string if provided")

        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("Header description must be a string if provided")

        if not isinstance(self.disabled, bool):
            raise ValueError("Header disabled flag must be a boolean")

        if self.type is not None and not isinstance(self.type, str):
            raise ValueError("Header type must be a string if provided")

        # Check for invalid characters in header key (basic validation)
        if any(char in self.key for char in ["\n", "\r", "\0", ":"]):
            raise ValueError("Header key contains invalid characters")

        return True

    @classmethod
    def from_dict(cls, data: dict) -> "Header":
        """
        Create Header from dictionary data.

        Args:
            data: Dictionary containing header data

        Returns:
            Header instance
        """
        return cls(
            key=data.get("key", ""),
            value=data.get("value"),
            description=data.get("description"),
            disabled=data.get("disabled", False),
            type=data.get("type"),
        )

    def to_dict(self) -> dict:
        """
        Convert Header to dictionary.

        Returns:
            Dictionary representation of Header
        """
        result = {"key": self.key, "disabled": self.disabled}

        if self.value is not None:
            result["value"] = self.value
        if self.description is not None:
            result["description"] = self.description
        if self.type is not None:
            result["type"] = self.type

        return result

    def __repr__(self) -> str:
        return (
            f"Header(key='{self.key}', value={self.value!r}, disabled={self.disabled})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Header):
            return False
        return (
            self.key == other.key
            and self.value == other.value
            and self.description == other.description
            and self.disabled == other.disabled
            and self.type == other.type
        )

    def __str__(self) -> str:
        """String representation suitable for HTTP headers."""
        if self.disabled or not self.key:
            return ""
        return f"{self.key}: {self.value or ''}"


class HeaderCollection:
    """Collection of headers with utility methods for manipulation."""

    def __init__(self, headers: Optional[List[Header]] = None):
        """
        Initialize HeaderCollection.

        Args:
            headers: List of Header objects
        """
        self.headers = headers or []

    def add(
        self, key: str, value: Optional[str] = None, description: Optional[str] = None
    ) -> Header:
        """
        Add a new header.

        Args:
            key: Header key
            value: Header value
            description: Header description

        Returns:
            The created Header object
        """
        header = Header(key=key, value=value, description=description)
        self.headers.append(header)
        return header

    def remove(self, key: str) -> bool:
        """
        Remove header by key (case-insensitive).

        Args:
            key: Header key to remove

        Returns:
            True if header was found and removed
        """
        original_length = len(self.headers)
        self.headers = [h for h in self.headers if h.key.lower() != key.lower()]
        return len(self.headers) < original_length

    def get(self, key: str) -> Optional[Header]:
        """
        Get header by key (case-insensitive).

        Args:
            key: Header key to find

        Returns:
            Header if found, None otherwise
        """
        for header in self.headers:
            if header.key.lower() == key.lower():
                return header
        return None

    def get_value(
        self, key: str, variable_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Get header value by key with variable resolution.

        Args:
            key: Header key to find
            variable_context: Dictionary of variables for resolution

        Returns:
            Resolved header value or None if not found
        """
        header = self.get(key)
        if header:
            return header.get_effective_value(variable_context)
        return None

    def set(
        self, key: str, value: Optional[str] = None, description: Optional[str] = None
    ) -> Header:
        """
        Set header value, updating existing or creating new.

        Args:
            key: Header key
            value: Header value
            description: Header description

        Returns:
            The Header object (existing or newly created)
        """
        existing = self.get(key)
        if existing:
            existing.value = value
            if description is not None:
                existing.description = description
            return existing
        else:
            return self.add(key, value, description)

    def get_active_headers(self) -> List[Header]:
        """
        Get list of active (non-disabled) headers.

        Returns:
            List of active Header objects
        """
        return [h for h in self.headers if h.is_active()]

    def to_http_dict(
        self, variable_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        """
        Convert to dictionary suitable for HTTP requests.

        Args:
            variable_context: Dictionary of variables for resolution

        Returns:
            Dictionary with header key-value pairs
        """
        result = {}
        for header in self.get_active_headers():
            value = header.get_effective_value(variable_context)
            if value is not None:
                result[header.key] = value
        return result

    def validate_all(self) -> bool:
        """
        Validate all headers in the collection.

        Returns:
            True if all headers are valid

        Raises:
            ValueError: If any header validation fails
        """
        for header in self.headers:
            header.validate()
        return True

    def __len__(self) -> int:
        return len(self.headers)

    def __iter__(self):
        return iter(self.headers)

    def __getitem__(self, index):
        return self.headers[index]

    def __repr__(self) -> str:
        return f"HeaderCollection({len(self.headers)} headers)"

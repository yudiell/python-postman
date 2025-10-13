"""Cookie model for HTTP cookie management."""

from typing import List, Optional, Dict, Any
from datetime import datetime
import re


class Cookie:
    """Represents an HTTP cookie with standard attributes."""

    def __init__(
        self,
        name: str,
        value: str,
        domain: Optional[str] = None,
        path: Optional[str] = "/",
        expires: Optional[datetime] = None,
        max_age: Optional[int] = None,
        secure: bool = False,
        http_only: bool = False,
        same_site: Optional[str] = None,
        host_only: Optional[bool] = None,
        session: Optional[bool] = None,
    ):
        """
        Initialize a Cookie.

        Args:
            name: Cookie name
            value: Cookie value
            domain: Domain for which the cookie is valid
            path: Path for which the cookie is valid
            expires: Expiration date/time
            max_age: Maximum age in seconds
            secure: Whether cookie should only be sent over HTTPS
            http_only: Whether cookie should be inaccessible to JavaScript
            same_site: SameSite attribute (Strict, Lax, or None)
            host_only: Whether cookie is host-only (Postman-specific)
            session: Whether cookie is a session cookie (Postman-specific)
        """
        self.name = name
        self.value = value
        self.domain = domain
        self.path = path
        self.expires = expires
        self.max_age = max_age
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site
        self.host_only = host_only
        self.session = session

    @classmethod
    def from_header(cls, set_cookie_header: str) -> "Cookie":
        """
        Parse cookie from Set-Cookie header.

        Args:
            set_cookie_header: Set-Cookie header value

        Returns:
            Cookie instance

        Example:
            >>> Cookie.from_header("sessionid=abc123; Domain=example.com; Path=/; Secure; HttpOnly")
        """
        # Check for empty header
        if not set_cookie_header or not set_cookie_header.strip():
            raise ValueError("Invalid Set-Cookie header: empty value")

        # Split by semicolon to get cookie parts
        parts = [part.strip() for part in set_cookie_header.split(";")]

        # First part is name=value
        name_value = parts[0]
        if "=" not in name_value:
            raise ValueError(f"Invalid Set-Cookie header: missing '=' in '{name_value}'")

        name, value = name_value.split("=", 1)
        name = name.strip()
        value = value.strip()

        # Parse attributes
        domain = None
        path = "/"
        expires = None
        max_age = None
        secure = False
        http_only = False
        same_site = None

        for part in parts[1:]:
            part_lower = part.lower()

            if "=" in part:
                attr_name, attr_value = part.split("=", 1)
                attr_name = attr_name.strip().lower()
                attr_value = attr_value.strip()

                if attr_name == "domain":
                    domain = attr_value
                elif attr_name == "path":
                    path = attr_value
                elif attr_name == "expires":
                    # Parse expires date
                    expires = cls._parse_expires(attr_value)
                elif attr_name == "max-age":
                    try:
                        max_age = int(attr_value)
                    except ValueError:
                        pass
                elif attr_name == "samesite":
                    same_site = attr_value
            else:
                # Boolean flags
                if part_lower == "secure":
                    secure = True
                elif part_lower == "httponly":
                    http_only = True

        return cls(
            name=name,
            value=value,
            domain=domain,
            path=path,
            expires=expires,
            max_age=max_age,
            secure=secure,
            http_only=http_only,
            same_site=same_site,
        )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Cookie":
        """
        Parse cookie from dictionary (Postman format).

        Args:
            data: Dictionary containing cookie data

        Returns:
            Cookie instance
        """
        # Parse expires if present
        expires = None
        if "expires" in data:
            expires_value = data["expires"]
            if isinstance(expires_value, str):
                expires = cls._parse_expires(expires_value)
            elif isinstance(expires_value, (int, float)):
                # Unix timestamp
                expires = datetime.fromtimestamp(expires_value)

        return cls(
            name=data.get("name", ""),
            value=data.get("value", ""),
            domain=data.get("domain"),
            path=data.get("path", "/"),
            expires=expires,
            max_age=data.get("maxAge"),
            secure=data.get("secure", False),
            http_only=data.get("httpOnly", False),
            same_site=data.get("sameSite"),
            host_only=data.get("hostOnly"),
            session=data.get("session"),
        )

    @staticmethod
    def _parse_expires(expires_str: str) -> Optional[datetime]:
        """
        Parse expires date string.

        Args:
            expires_str: Date string in various formats

        Returns:
            datetime object or None if parsing fails
        """
        # Common date formats in Set-Cookie headers
        formats = [
            "%a, %d %b %Y %H:%M:%S GMT",  # RFC 1123
            "%A, %d-%b-%y %H:%M:%S GMT",  # RFC 850
            "%a %b %d %H:%M:%S %Y",  # ANSI C asctime()
        ]

        for fmt in formats:
            try:
                return datetime.strptime(expires_str, fmt)
            except ValueError:
                continue

        return None

    def to_header(self) -> str:
        """
        Convert cookie to Set-Cookie header format.

        Returns:
            Set-Cookie header value

        Example:
            >>> cookie.to_header()
            'sessionid=abc123; Domain=example.com; Path=/; Secure; HttpOnly'
        """
        parts = [f"{self.name}={self.value}"]

        if self.domain:
            parts.append(f"Domain={self.domain}")

        if self.path:
            parts.append(f"Path={self.path}")

        if self.expires:
            # Format as RFC 1123
            expires_str = self.expires.strftime("%a, %d %b %Y %H:%M:%S GMT")
            parts.append(f"Expires={expires_str}")

        if self.max_age is not None:
            parts.append(f"Max-Age={self.max_age}")

        if self.secure:
            parts.append("Secure")

        if self.http_only:
            parts.append("HttpOnly")

        if self.same_site:
            parts.append(f"SameSite={self.same_site}")

        return "; ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert cookie to dictionary (Postman format).

        Returns:
            Dictionary representation of cookie
        """
        result = {
            "name": self.name,
            "value": self.value,
        }

        if self.domain:
            result["domain"] = self.domain

        if self.path:
            result["path"] = self.path

        if self.expires:
            # Store as Unix timestamp
            result["expires"] = int(self.expires.timestamp())

        if self.max_age is not None:
            result["maxAge"] = self.max_age

        if self.secure:
            result["secure"] = self.secure

        if self.http_only:
            result["httpOnly"] = self.http_only

        if self.same_site:
            result["sameSite"] = self.same_site

        if self.host_only is not None:
            result["hostOnly"] = self.host_only

        if self.session is not None:
            result["session"] = self.session

        return result

    def is_expired(self) -> bool:
        """
        Check if cookie is expired.

        Returns:
            True if cookie is expired
        """
        if self.expires:
            return datetime.now() > self.expires
        return False

    def matches_domain(self, domain: str) -> bool:
        """
        Check if cookie matches a given domain.

        Args:
            domain: Domain to check

        Returns:
            True if cookie is valid for the domain
        """
        if not self.domain:
            return False

        # Exact match
        if self.domain == domain:
            return True

        # Domain cookie (starts with .)
        if self.domain.startswith("."):
            return domain.endswith(self.domain) or domain == self.domain[1:]

        return False

    def matches_path(self, path: str) -> bool:
        """
        Check if cookie matches a given path.

        Args:
            path: Path to check

        Returns:
            True if cookie is valid for the path
        """
        if not self.path:
            return True

        # Exact match
        if self.path == path:
            return True

        # Path prefix match
        if path.startswith(self.path):
            # Ensure path separator
            if self.path.endswith("/") or path[len(self.path):].startswith("/"):
                return True

        return False

    def __repr__(self) -> str:
        return f"Cookie(name='{self.name}', domain='{self.domain}', path='{self.path}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Cookie):
            return False
        return (
            self.name == other.name
            and self.domain == other.domain
            and self.path == other.path
        )


class CookieJar:
    """Manages a collection of cookies."""

    def __init__(self):
        """Initialize an empty CookieJar."""
        self.cookies: List[Cookie] = []

    def add(self, cookie: Cookie) -> None:
        """
        Add a cookie to the jar.

        If a cookie with the same name, domain, and path exists, it will be replaced.

        Args:
            cookie: Cookie to add
        """
        # Remove existing cookie with same name, domain, and path
        self.cookies = [c for c in self.cookies if c != cookie]

        # Add new cookie
        self.cookies.append(cookie)

    def get(self, name: str, domain: Optional[str] = None, path: Optional[str] = None) -> Optional[Cookie]:
        """
        Get a cookie by name and optionally domain and path.

        Args:
            name: Cookie name
            domain: Optional domain filter
            path: Optional path filter

        Returns:
            Cookie instance or None if not found
        """
        for cookie in self.cookies:
            if cookie.name != name:
                continue

            if domain and cookie.domain != domain:
                continue

            if path and cookie.path != path:
                continue

            return cookie

        return None

    def filter_by_domain(self, domain: str) -> List[Cookie]:
        """
        Get all cookies for a domain.

        Args:
            domain: Domain to filter by

        Returns:
            List of cookies matching the domain
        """
        return [cookie for cookie in self.cookies if cookie.matches_domain(domain)]

    def filter_by_path(self, path: str) -> List[Cookie]:
        """
        Get all cookies for a path.

        Args:
            path: Path to filter by

        Returns:
            List of cookies matching the path
        """
        return [cookie for cookie in self.cookies if cookie.matches_path(path)]

    def filter_for_request(self, domain: str, path: str, secure: bool = False) -> List[Cookie]:
        """
        Get all cookies that should be sent with a request.

        Args:
            domain: Request domain
            path: Request path
            secure: Whether request is over HTTPS

        Returns:
            List of cookies to send with the request
        """
        matching_cookies = []

        for cookie in self.cookies:
            # Skip expired cookies
            if cookie.is_expired():
                continue

            # Skip secure cookies on non-secure requests
            if cookie.secure and not secure:
                continue

            # Check domain and path
            if cookie.matches_domain(domain) and cookie.matches_path(path):
                matching_cookies.append(cookie)

        return matching_cookies

    def remove(self, name: str, domain: Optional[str] = None, path: Optional[str] = None) -> bool:
        """
        Remove a cookie from the jar.

        Args:
            name: Cookie name
            domain: Optional domain filter
            path: Optional path filter

        Returns:
            True if a cookie was removed
        """
        original_count = len(self.cookies)

        self.cookies = [
            c for c in self.cookies
            if not (
                c.name == name
                and (domain is None or c.domain == domain)
                and (path is None or c.path == path)
            )
        ]

        return len(self.cookies) < original_count

    def clear(self) -> None:
        """Remove all cookies from the jar."""
        self.cookies.clear()

    def clear_expired(self) -> int:
        """
        Remove all expired cookies.

        Returns:
            Number of cookies removed
        """
        original_count = len(self.cookies)
        self.cookies = [c for c in self.cookies if not c.is_expired()]
        return original_count - len(self.cookies)

    def __len__(self) -> int:
        return len(self.cookies)

    def __iter__(self):
        return iter(self.cookies)

    def __repr__(self) -> str:
        return f"CookieJar(cookies={len(self.cookies)})"


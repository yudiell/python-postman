"""URL model for Postman collection URLs."""

from typing import Optional, List, Dict, Any, Union
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
import re


class QueryParam:
    """Represents a URL query parameter."""

    def __init__(
        self,
        key: str,
        value: Optional[str] = None,
        description: Optional[str] = None,
        disabled: bool = False,
    ):
        """
        Initialize QueryParam.

        Args:
            key: Parameter key/name (required)
            value: Parameter value (optional)
            description: Parameter description (optional)
            disabled: Whether parameter is disabled (default: False)
        """
        self.key = key
        self.value = value
        self.description = description
        self.disabled = disabled

    def __repr__(self) -> str:
        return f"QueryParam(key='{self.key}', value={self.value!r}, disabled={self.disabled})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, QueryParam):
            return False
        return (
            self.key == other.key
            and self.value == other.value
            and self.description == other.description
            and self.disabled == other.disabled
        )


class Url:
    """Represents a URL with protocol, host, path, and query parameters."""

    def __init__(
        self,
        raw: Optional[str] = None,
        protocol: Optional[str] = None,
        host: Optional[Union[str, List[str]]] = None,
        path: Optional[Union[str, List[str]]] = None,
        port: Optional[str] = None,
        query: Optional[List[QueryParam]] = None,
        hash: Optional[str] = None,
        variable: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize Url.

        Args:
            raw: Raw URL string (optional)
            protocol: URL protocol (e.g., 'https')
            host: Host as string or list of host segments
            path: Path as string or list of path segments
            port: Port number as string
            query: List of QueryParam objects
            hash: URL fragment/hash
            variable: List of path variables
        """
        self.raw = raw
        self.protocol = protocol
        self.host = host if isinstance(host, list) else ([host] if host else [])
        self.path = (
            path if isinstance(path, list) else (path.split("/") if path else [])
        )
        self.port = port
        self.query = query or []
        self.hash = hash
        self.variable = variable or []

        # If raw URL is provided but components aren't, parse the raw URL
        if raw and not any([protocol, host, path]):
            self._parse_raw_url()

    def _parse_raw_url(self) -> None:
        """Parse the raw URL string into components."""
        if not self.raw:
            return

        try:
            parsed = urlparse(self.raw)

            if parsed.scheme:
                self.protocol = parsed.scheme

            if parsed.hostname:
                self.host = [parsed.hostname]

            if parsed.path:
                # Remove empty segments and leading slash
                path_segments = [seg for seg in parsed.path.split("/") if seg]
                self.path = path_segments

            if parsed.port:
                self.port = str(parsed.port)

            if parsed.query:
                query_params = parse_qs(parsed.query, keep_blank_values=True)
                self.query = []
                for key, values in query_params.items():
                    for value in values:
                        self.query.append(QueryParam(key=key, value=value))

            if parsed.fragment:
                self.hash = parsed.fragment

        except Exception:
            # If parsing fails, keep the raw URL as is
            pass

    def to_string(
        self,
        resolve_variables: bool = False,
        variable_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Convert URL to string representation.

        Args:
            resolve_variables: Whether to resolve variable placeholders
            variable_context: Dictionary of variables for resolution

        Returns:
            URL as string
        """
        if self.raw and not resolve_variables:
            return self.raw

        # Build URL components
        scheme = self.protocol or "https"
        netloc = ""

        if self.host:
            host_str = ".".join(str(h) for h in self.host if h)
            if resolve_variables and variable_context:
                host_str = self._resolve_variables(host_str, variable_context)
            netloc = host_str

            if self.port:
                netloc += f":{self.port}"

        path = ""
        if self.path:
            path_segments = [str(p) for p in self.path if p]
            if resolve_variables and variable_context:
                path_segments = [
                    self._resolve_variables(seg, variable_context)
                    for seg in path_segments
                ]
            path = "/" + "/".join(path_segments)

        query = ""
        if self.query:
            active_params = [q for q in self.query if not q.disabled]
            if active_params:
                query_dict = {}
                for param in active_params:
                    key = param.key
                    value = param.value or ""
                    if resolve_variables and variable_context:
                        key = self._resolve_variables(key, variable_context)
                        value = self._resolve_variables(value, variable_context)

                    if key in query_dict:
                        if not isinstance(query_dict[key], list):
                            query_dict[key] = [query_dict[key]]
                        query_dict[key].append(value)
                    else:
                        query_dict[key] = value

                query = urlencode(query_dict, doseq=True)

        fragment = self.hash or ""
        if resolve_variables and variable_context and fragment:
            fragment = self._resolve_variables(fragment, variable_context)

        return urlunparse((scheme, netloc, path, "", query, fragment))

    def get_url_string(
        self,
        resolve_variables: bool = False,
        variable_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Construct URL string from components.

        .. deprecated:: 
            Use :meth:`to_string` instead. This method is maintained for backward compatibility.

        Args:
            resolve_variables: Whether to resolve variable placeholders
            variable_context: Dictionary of variables for resolution

        Returns:
            Constructed URL string
        """
        import warnings
        warnings.warn(
            "get_url_string() is deprecated, use to_string() instead",
            DeprecationWarning,
            stacklevel=2
        )
        return self.to_string(resolve_variables, variable_context)

    def _resolve_variables(self, text: str, variable_context: Dict[str, Any]) -> str:
        """
        Resolve variable placeholders in text using efficient regex-based approach.

        Args:
            text: Text containing variable placeholders
            variable_context: Dictionary of variables for resolution

        Returns:
            Text with resolved variables
        """
        if not text or not variable_context:
            return text

        import re
        
        # Combine both placeholder formats in a single regex
        def replace_placeholder(match):
            # Group 1: {{variable}} format
            # Group 2: :variable format
            var_name = match.group(1) or match.group(2)
            var_name = var_name.strip()
            
            if var_name in variable_context:
                return str(variable_context[var_name])
            return match.group(0)  # Keep placeholder if variable not found

        # Match both {{variable}} and :variable formats
        pattern = r'\{\{([^}]+)\}\}|:([a-zA-Z_][a-zA-Z0-9_]*)'
        return re.sub(pattern, replace_placeholder, text)

    def add_query_param(
        self, key: str, value: Optional[str] = None, description: Optional[str] = None
    ) -> None:
        """
        Add a query parameter.

        Args:
            key: Parameter key
            value: Parameter value
            description: Parameter description
        """
        param = QueryParam(key=key, value=value, description=description)
        self.query.append(param)

    def remove_query_param(self, key: str) -> bool:
        """
        Remove query parameter by key.

        Args:
            key: Parameter key to remove

        Returns:
            True if parameter was found and removed
        """
        original_length = len(self.query)
        self.query = [q for q in self.query if q.key != key]
        return len(self.query) < original_length

    def get_query_param(self, key: str) -> Optional[QueryParam]:
        """
        Get query parameter by key.

        Args:
            key: Parameter key to find

        Returns:
            QueryParam if found, None otherwise
        """
        for param in self.query:
            if param.key == key:
                return param
        return None

    def get_path_variables(self) -> List[str]:
        """
        Extract path variable names from the URL path.

        Returns:
            List of variable names found in the path
        """
        variables = []

        # Check path segments for :variable format
        for segment in self.path:
            if isinstance(segment, str) and segment.startswith(":"):
                variables.append(segment[1:])

        # Check for {{variable}} format in path
        path_str = "/".join(str(p) for p in self.path)
        variable_pattern = r"\{\{([^}]+)\}\}"
        matches = re.findall(variable_pattern, path_str)
        variables.extend(matches)

        return list(set(variables))  # Remove duplicates

    def validate(self) -> bool:
        """
        Validate the URL structure.

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        if not self.raw and not self.host:
            raise ValueError("URL must have either raw URL string or host specified")

        if self.protocol and not isinstance(self.protocol, str):
            raise ValueError("Protocol must be a string")

        if self.port and not isinstance(self.port, str):
            raise ValueError("Port must be a string")

        # Validate query parameters
        for param in self.query:
            if not isinstance(param, QueryParam):
                raise ValueError("All query items must be QueryParam instances")
            if not param.key or not isinstance(param.key, str):
                raise ValueError("Query parameter key is required and must be a string")

        return True

    @classmethod
    def from_string(cls, url_string: str) -> "Url":
        """
        Create Url from URL string.

        Args:
            url_string: URL as string

        Returns:
            Url instance
        """
        return cls(raw=url_string)

    @classmethod
    def from_dict(cls, data: dict) -> "Url":
        """
        Create Url from dictionary data.

        Args:
            data: Dictionary containing URL data

        Returns:
            Url instance
        """
        query_params = []
        if "query" in data and isinstance(data["query"], list):
            for q in data["query"]:
                if isinstance(q, dict):
                    query_params.append(
                        QueryParam(
                            key=q.get("key", ""),
                            value=q.get("value"),
                            description=q.get("description"),
                            disabled=q.get("disabled", False),
                        )
                    )

        return cls(
            raw=data.get("raw"),
            protocol=data.get("protocol"),
            host=data.get("host"),
            path=data.get("path"),
            port=data.get("port"),
            query=query_params,
            hash=data.get("hash"),
            variable=data.get("variable", []),
        )

    def to_dict(self) -> dict:
        """
        Convert Url to dictionary.

        Returns:
            Dictionary representation of Url
        """
        result = {}

        if self.raw:
            result["raw"] = self.raw
        if self.protocol:
            result["protocol"] = self.protocol
        if self.host:
            result["host"] = self.host
        if self.path:
            result["path"] = self.path
        if self.port:
            result["port"] = self.port
        if self.query:
            result["query"] = [
                {
                    "key": q.key,
                    "value": q.value,
                    "description": q.description,
                    "disabled": q.disabled,
                }
                for q in self.query
            ]
        if self.hash:
            result["hash"] = self.hash
        if self.variable:
            result["variable"] = self.variable

        return result

    def __repr__(self) -> str:
        return f"Url(raw='{self.raw}', protocol='{self.protocol}', host={self.host})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Url):
            return False
        return (
            self.raw == other.raw
            and self.protocol == other.protocol
            and self.host == other.host
            and self.path == other.path
            and self.port == other.port
            and self.query == other.query
            and self.hash == other.hash
            and self.variable == other.variable
        )

"""
Query builder for searching and filtering requests in collections.
"""

from typing import List, Callable, Optional, Iterator, TYPE_CHECKING
import re

if TYPE_CHECKING:
    from ..models.collection import Collection
    from ..models.request import Request
    from ..models.folder import Folder
    from ..models.item import Item


class SearchResult:
    """
    Represents a search result with context.
    
    Attributes:
        request: The matched request
        path: List of folder names leading to this request
        full_path: String representation of the path (e.g., "Folder1 > Folder2 > Request")
    """

    def __init__(self, request: "Request", path: List[str]):
        """
        Initialize SearchResult.
        
        Args:
            request: The matched request
            path: List of folder/request names forming the hierarchy path
        """
        self.request = request
        self.path = path
        self.full_path = " > ".join(path)

    def __repr__(self) -> str:
        return f"SearchResult(request='{self.request.name}', path='{self.full_path}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, SearchResult):
            return False
        return self.request == other.request and self.path == other.path


class RequestQuery:
    """
    Builder for complex request queries with fluent API.
    
    Supports method chaining for building complex filters:
    
    Examples:
        >>> # Find all POST requests
        >>> results = collection.search().by_method("POST").execute()
        >>> 
        >>> # Find requests to a specific host with authentication
        >>> results = collection.search() \\
        ...     .by_host("api.example.com") \\
        ...     .by_auth_type("bearer") \\
        ...     .execute()
        >>> 
        >>> # Find requests with test scripts in a specific folder
        >>> results = collection.search() \\
        ...     .has_scripts("test") \\
        ...     .in_folder("Auth Tests") \\
        ...     .execute()
        >>> 
        >>> # Use iterator for large result sets
        >>> for result in collection.search().by_method("GET").execute_iter():
        ...     print(f"{result.full_path}: {result.request.url.to_string()}")
    """

    def __init__(self, collection: "Collection"):
        """
        Initialize RequestQuery.
        
        Args:
            collection: The collection to search within
        """
        self.collection = collection
        self.filters: List[Callable[["Request"], bool]] = []
        self._folder_filter: Optional[str] = None

    def by_method(self, method: str) -> "RequestQuery":
        """
        Filter by HTTP method.
        
        Args:
            method: HTTP method to filter by (case-insensitive)
        
        Returns:
            Self for method chaining
            
        Examples:
            >>> results = collection.search().by_method("POST").execute()
            >>> results = collection.search().by_method("get").execute()
        """
        method_upper = method.upper()
        self.filters.append(lambda r: r.method.upper() == method_upper)
        return self

    def by_url_pattern(self, pattern: str) -> "RequestQuery":
        """
        Filter by URL pattern using regex.
        
        Args:
            pattern: Regular expression pattern to match against URL
        
        Returns:
            Self for method chaining
            
        Examples:
            >>> # Find all requests to /api/users endpoints
            >>> results = collection.search().by_url_pattern(r"/api/users").execute()
            >>> 
            >>> # Find requests with numeric IDs in path
            >>> results = collection.search().by_url_pattern(r"/users/\\d+").execute()
        """
        try:
            regex = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern '{pattern}': {e}") from e
        
        self.filters.append(lambda r: regex.search(r.url.to_string()) is not None)
        return self

    def by_host(self, host: str) -> "RequestQuery":
        """
        Filter by URL host.
        
        Args:
            host: Host name to filter by (exact match)
        
        Returns:
            Self for method chaining
            
        Examples:
            >>> results = collection.search().by_host("api.example.com").execute()
        """
        self.filters.append(lambda r: ".".join(r.url.host) == host if r.url.host else False)
        return self

    def by_auth_type(self, auth_type: str) -> "RequestQuery":
        """
        Filter by authentication type.
        
        Args:
            auth_type: Authentication type to filter by (e.g., "bearer", "basic", "apikey")
        
        Returns:
            Self for method chaining
            
        Examples:
            >>> results = collection.search().by_auth_type("bearer").execute()
            >>> results = collection.search().by_auth_type("basic").execute()
        """
        auth_type_lower = auth_type.lower()
        self.filters.append(
            lambda r: r.auth is not None and r.auth.type.lower() == auth_type_lower
        )
        return self

    def has_scripts(self, script_type: Optional[str] = None) -> "RequestQuery":
        """
        Filter by presence of scripts.
        
        Args:
            script_type: Optional script type to filter by ("prerequest" or "test").
                        If None, matches requests with any scripts.
        
        Returns:
            Self for method chaining
            
        Examples:
            >>> # Find requests with any scripts
            >>> results = collection.search().has_scripts().execute()
            >>> 
            >>> # Find requests with test scripts
            >>> results = collection.search().has_scripts("test").execute()
            >>> 
            >>> # Find requests with pre-request scripts
            >>> results = collection.search().has_scripts("prerequest").execute()
        """
        if script_type:
            script_type_lower = script_type.lower()
            self.filters.append(
                lambda r: any(e.listen.lower() == script_type_lower for e in r.events)
            )
        else:
            self.filters.append(lambda r: bool(r.events))
        return self

    def in_folder(self, folder_name: str) -> "RequestQuery":
        """
        Filter to requests within a specific folder (searches recursively).
        
        Args:
            folder_name: Name of the folder to search within
        
        Returns:
            Self for method chaining
            
        Examples:
            >>> # Find all requests in "Auth" folder
            >>> results = collection.search().in_folder("Auth").execute()
            >>> 
            >>> # Find POST requests in "Users" folder
            >>> results = collection.search() \\
            ...     .by_method("POST") \\
            ...     .in_folder("Users") \\
            ...     .execute()
        """
        self._folder_filter = folder_name
        return self

    def execute(self) -> List[SearchResult]:
        """
        Execute the query and return all results as a list.
        
        Returns:
            List of SearchResult objects matching the query
            
        Examples:
            >>> results = collection.search().by_method("GET").execute()
            >>> print(f"Found {len(results)} GET requests")
            >>> for result in results:
            ...     print(f"  {result.full_path}")
        """
        results = []
        self._search_items(self.collection.items, [], results)
        return results

    def execute_iter(self) -> Iterator[SearchResult]:
        """
        Execute query and return results as an iterator.
        
        This is more memory-efficient for large result sets.
        
        Returns:
            Iterator of SearchResult objects matching the query
            
        Examples:
            >>> for result in collection.search().by_method("POST").execute_iter():
            ...     print(f"Processing: {result.request.name}")
            ...     # Process each result without loading all into memory
        """
        for result in self.execute():
            yield result

    def _search_items(
        self,
        items: List["Item"],
        path: List[str],
        results: List[SearchResult],
    ) -> None:
        """
        Recursively search through items.
        
        Args:
            items: List of items to search
            path: Current path in the hierarchy
            results: List to append matching results to
        """
        from ..models.request import Request
        from ..models.folder import Folder
        
        for item in items:
            if isinstance(item, Request):
                # Check if we're filtering by folder
                if self._folder_filter:
                    # Only include if the folder name is in the path
                    if self._folder_filter not in path:
                        continue
                
                # Apply all filters
                if all(f(item) for f in self.filters):
                    results.append(SearchResult(item, path + [item.name]))
                    
            elif isinstance(item, Folder):
                # Recursively search in subfolders
                self._search_items(
                    item.items,
                    path + [item.name],
                    results
                )

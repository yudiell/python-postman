"""
Authentication inheritance resolution for Postman collections.

This module provides utilities to resolve effective authentication for requests
by traversing the collection hierarchy (Request > Folder > Collection).
"""

from typing import Optional, List, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..models.auth import Auth
    from ..models.request import Request
    from ..models.folder import Folder
    from ..models.collection import Collection


class AuthSource(Enum):
    """Indicates where authentication was resolved from."""
    
    REQUEST = "request"
    FOLDER = "folder"
    COLLECTION = "collection"
    NONE = "none"


class ResolvedAuth:
    """
    Result of authentication resolution.
    
    Contains the resolved authentication configuration, its source in the hierarchy,
    and the path through the collection structure.
    """

    def __init__(
        self,
        auth: Optional["Auth"],
        source: AuthSource,
        path: List[str]
    ):
        """
        Initialize ResolvedAuth.
        
        Args:
            auth: The resolved authentication configuration, or None if no auth found
            source: The level in the hierarchy where auth was found
            path: List of names representing the path through the hierarchy
        """
        self.auth = auth
        self.source = source
        self.path = path

    def __repr__(self) -> str:
        auth_type = self.auth.type if self.auth else None
        path_str = " > ".join(self.path)
        return (
            f"ResolvedAuth(source={self.source.value}, "
            f"auth_type={auth_type}, path='{path_str}')"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, ResolvedAuth):
            return False
        return (
            self.auth == other.auth
            and self.source == other.source
            and self.path == other.path
        )


class AuthResolver:
    """
    Resolves effective authentication considering inheritance hierarchy.
    
    Authentication in Postman collections follows an inheritance pattern:
    Request auth > Folder auth > Collection auth
    
    This resolver walks up the hierarchy to find the effective authentication
    that will be used for a given request.
    """

    @staticmethod
    def resolve_auth(
        request: "Request",
        parent_folder: Optional["Folder"] = None,
        collection: Optional["Collection"] = None
    ) -> ResolvedAuth:
        """
        Resolve effective authentication for a request.
        
        Walks up the hierarchy following the priority:
        1. Request-level auth (highest priority)
        2. Folder-level auth (walks up through parent folders)
        3. Collection-level auth (lowest priority)
        
        Args:
            request: The request to resolve authentication for
            parent_folder: The immediate parent folder of the request (optional)
            collection: The collection containing the request (optional)
            
        Returns:
            ResolvedAuth: Contains the resolved auth, its source, and hierarchy path
            
        Examples:
            >>> from python_postman.introspection import AuthResolver
            >>> 
            >>> # Resolve auth for a request
            >>> resolved = AuthResolver.resolve_auth(request, folder, collection)
            >>> print(f"Auth type: {resolved.auth.type}")
            >>> print(f"Source: {resolved.source.value}")
            >>> print(f"Path: {' > '.join(resolved.path)}")
        """
        path = [request.name]

        # Check request-level auth (highest priority)
        if request.auth:
            return ResolvedAuth(request.auth, AuthSource.REQUEST, path)

        # Check folder hierarchy (walk up the tree)
        current_folder = parent_folder
        while current_folder:
            path.insert(0, current_folder.name)
            if current_folder.auth:
                return ResolvedAuth(current_folder.auth, AuthSource.FOLDER, path)
            # Walk up to parent folder if available
            current_folder = getattr(current_folder, '_parent_folder', None)

        # Check collection-level auth (lowest priority)
        if collection and collection.auth:
            if collection.info and collection.info.name:
                path.insert(0, collection.info.name)
            return ResolvedAuth(collection.auth, AuthSource.COLLECTION, path)

        # No auth found anywhere in the hierarchy
        return ResolvedAuth(None, AuthSource.NONE, path)

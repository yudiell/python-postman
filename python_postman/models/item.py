"""
Abstract base class for collection items (requests and folders).
"""

from abc import ABC, abstractmethod
from typing import Iterator, Optional, TYPE_CHECKING, Dict, Any, List

if TYPE_CHECKING:
    from .request import Request
    from .folder import Folder


class Item(ABC):
    """
    Abstract base class for items in a Postman collection.

    **Important**: This is an abstract base class and should NOT be instantiated directly.
    
    Use concrete classes instead:
    - **Request**: for HTTP requests
    - **Folder**: for organizing requests into folders
    
    Or use factory methods for convenient creation:
    - **Item.create_request()**: Create a new Request
    - **Item.create_folder()**: Create a new Folder
    
    Examples:
        Creating a request using the concrete class:
        
        >>> from python_postman.models import Request, Url
        >>> request = Request(
        ...     name="Get Users",
        ...     method="GET",
        ...     url=Url.from_string("https://api.example.com/users")
        ... )
        
        Creating a request using the factory method:
        
        >>> request = Item.create_request(
        ...     name="Get Users",
        ...     method="GET",
        ...     url="https://api.example.com/users"
        ... )
        
        Creating a folder:
        
        >>> folder = Item.create_folder(
        ...     name="User Endpoints",
        ...     description="All user-related API endpoints"
        ... )
    
    Items can be either Request objects or Folder objects that contain other items.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize an Item.
        
        **Note**: This constructor should not be called directly. Use concrete classes
        (Request or Folder) or factory methods (Item.create_request() or Item.create_folder()).

        Args:
            name: The name of the item
            description: Optional description of the item. This field provides human-readable
                        documentation for the item. For folders, describe the purpose of the
                        grouping. For requests, describe what the endpoint does, authentication
                        requirements, and expected responses. Supports Markdown formatting.
            
        Raises:
            TypeError: If attempting to instantiate Item directly
            
        Note:
            The description field is used for documentation and can be leveraged to generate
            API documentation, provide context to team members, or audit your collection.
            See the Description Field Usage Guide for best practices and examples.
        """
        # Prevent direct instantiation of the abstract Item class
        if self.__class__ == Item:
            raise TypeError(
                "Cannot instantiate abstract class 'Item' directly. "
                "Use concrete classes 'Request' or 'Folder' instead, "
                "or use factory methods:\n"
                "  - Item.create_request(name, method, url, ...)\n"
                "  - Item.create_folder(name, description, ...)"
            )
        
        self.name = name
        self.description = description

    @abstractmethod
    def get_requests(self) -> Iterator["Request"]:
        """
        Get all requests contained within this item.

        For Request objects, this returns the request itself.
        For Folder objects, this recursively returns all requests in the folder.

        Returns:
            Iterator of Request objects
        """
        pass

    @staticmethod
    def create_request(
        name: str,
        method: str,
        url: str,
        description: Optional[str] = None,
        headers: Optional[List[Any]] = None,
        body: Optional[Any] = None,
        auth: Optional[Any] = None,
        events: Optional[List[Any]] = None,
        responses: Optional[List[Any]] = None,
    ) -> "Request":
        """
        Factory method to create a Request.
        
        This is a convenient way to create requests without importing the Request class.
        
        Args:
            name: Request name
            method: HTTP method (GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS)
            url: Request URL as a string
            description: Optional description of the request
            headers: Optional list of Header objects
            body: Optional Body object
            auth: Optional Auth object
            events: Optional list of Event objects (pre-request scripts, tests)
            responses: Optional list of ExampleResponse objects
        
        Returns:
            Request instance
            
        Examples:
            Create a simple GET request:
            
            >>> request = Item.create_request(
            ...     name="Get Users",
            ...     method="GET",
            ...     url="https://api.example.com/users"
            ... )
            
            Create a POST request with description:
            
            >>> request = Item.create_request(
            ...     name="Create User",
            ...     method="POST",
            ...     url="https://api.example.com/users",
            ...     description="Creates a new user in the system"
            ... )
        """
        from .request import Request
        from .url import Url
        
        return Request(
            name=name,
            method=method,
            url=Url.from_string(url),
            description=description,
            headers=headers,
            body=body,
            auth=auth,
            events=events,
            responses=responses,
        )

    @staticmethod
    def create_folder(
        name: str,
        description: Optional[str] = None,
        items: Optional[List["Item"]] = None,
        auth: Optional[Any] = None,
        events: Optional[List[Any]] = None,
        variables: Optional[List[Any]] = None,
    ) -> "Folder":
        """
        Factory method to create a Folder.
        
        This is a convenient way to create folders without importing the Folder class.
        
        Args:
            name: Folder name
            description: Optional folder description
            items: Optional list of items (Request or Folder objects) contained in this folder
            auth: Optional folder-level Auth object
            events: Optional list of folder-level Event objects
            variables: Optional list of folder-level Variable objects
        
        Returns:
            Folder instance
            
        Examples:
            Create an empty folder:
            
            >>> folder = Item.create_folder(
            ...     name="User Endpoints",
            ...     description="All user-related API endpoints"
            ... )
            
            Create a folder with requests:
            
            >>> get_request = Item.create_request(
            ...     name="Get Users",
            ...     method="GET",
            ...     url="https://api.example.com/users"
            ... )
            >>> post_request = Item.create_request(
            ...     name="Create User",
            ...     method="POST",
            ...     url="https://api.example.com/users"
            ... )
            >>> folder = Item.create_folder(
            ...     name="User Endpoints",
            ...     items=[get_request, post_request]
            ... )
        """
        from .folder import Folder
        
        return Folder(
            name=name,
            items=items or [],
            description=description,
            auth=auth,
            events=events,
            variables=variables,
        )

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', description='{self.description}')"

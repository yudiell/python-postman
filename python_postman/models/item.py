"""
Abstract base class for collection items (requests and folders).
"""

from abc import ABC, abstractmethod
from typing import Iterator, Optional


class Item(ABC):
    """
    Abstract base class for items in a Postman collection.

    Items can be either Request objects or Folder objects that contain other items.
    """

    def __init__(self, name: str, description: Optional[str] = None):
        """
        Initialize an Item.

        Args:
            name: The name of the item
            description: Optional description of the item
        """
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

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}', description='{self.description}')"

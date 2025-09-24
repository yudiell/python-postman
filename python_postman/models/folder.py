"""
Folder class representing folders that contain other items.
"""

from typing import List, Optional, Iterator
from .item import Item
from .auth import Auth
from .event import Event
from .variable import Variable


class Folder(Item):
    """
    Represents a folder that can contain requests and other folders.
    """

    def __init__(
        self,
        name: str,
        items: List[Item],
        description: Optional[str] = None,
        auth: Optional[Auth] = None,
        events: Optional[List[Event]] = None,
        variables: Optional[List[Variable]] = None,
    ):
        """
        Initialize a Folder.

        Args:
            name: Name of the folder
            items: List of items contained in this folder
            description: Optional description
            auth: Optional folder-level authentication
            events: Optional list of folder-level events
            variables: Optional list of folder-level variables
        """
        super().__init__(name, description)
        self.items = items or []
        self.auth = auth
        self.events = events or []
        self.variables = variables or []

    def get_requests(self) -> Iterator["Request"]:
        """
        Get all requests in this folder recursively.

        Returns:
            Iterator of all Request objects in this folder and subfolders
        """
        for item in self.items:
            yield from item.get_requests()

    def get_subfolders(self) -> List["Folder"]:
        """
        Get all direct subfolders of this folder.

        Returns:
            List of Folder objects that are direct children of this folder
        """
        return [item for item in self.items if isinstance(item, Folder)]

    @classmethod
    def from_dict(cls, data: dict) -> "Folder":
        """
        Create Folder from dictionary data.

        Args:
            data: Dictionary containing folder data

        Returns:
            Folder instance
        """
        # Import here to avoid circular imports
        from .request import Request

        name = data.get("name", "")

        # Parse items
        items = []
        items_data = data.get("item", [])
        for item_data in items_data:
            if "request" in item_data:
                # This is a request item
                items.append(Request.from_dict(item_data))
            else:
                # This is a folder item
                items.append(cls.from_dict(item_data))

        # Parse variables
        variables = []
        variables_data = data.get("variable", [])
        for var_data in variables_data:
            variables.append(Variable.from_dict(var_data))

        # Parse auth
        auth = None
        auth_data = data.get("auth")
        if auth_data:
            auth = Auth.from_dict(auth_data)

        # Parse events
        events = []
        events_data = data.get("event", [])
        for event_data in events_data:
            events.append(Event.from_dict(event_data))

        return cls(
            name=name,
            items=items,
            description=data.get("description"),
            auth=auth,
            events=events,
            variables=variables,
        )

    def to_dict(self) -> dict:
        """
        Convert Folder to dictionary.

        Returns:
            Dictionary representation of Folder
        """
        result = {"name": self.name, "item": [item.to_dict() for item in self.items]}

        if self.description:
            result["description"] = self.description

        if self.variables:
            result["variable"] = [var.to_dict() for var in self.variables]

        if self.auth:
            result["auth"] = self.auth.to_dict()

        if self.events:
            result["event"] = [event.to_dict() for event in self.events]

        return result

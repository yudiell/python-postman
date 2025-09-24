"""CollectionInfo model for Postman collection metadata."""

from typing import Optional


class CollectionInfo:
    """Represents collection metadata including name, description, and schema version."""

    def __init__(
        self, name: str, description: Optional[str] = None, schema: Optional[str] = None
    ):
        """
        Initialize CollectionInfo.

        Args:
            name: Collection name (required)
            description: Collection description (optional)
            schema: Postman schema version (optional)
        """
        self.name = name
        self.description = description
        self.schema = schema

    def validate(self) -> bool:
        """
        Validate that required fields are present.

        Returns:
            True if validation passes

        Raises:
            ValueError: If required fields are missing or invalid
        """
        if not self.name or not isinstance(self.name, str) or not self.name.strip():
            raise ValueError(
                "Collection name is required and must be a non-empty string"
            )

        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("Collection description must be a string if provided")

        if self.schema is not None and not isinstance(self.schema, str):
            raise ValueError("Collection schema must be a string if provided")

        return True

    @classmethod
    def from_dict(cls, data: dict) -> "CollectionInfo":
        """
        Create CollectionInfo from dictionary data.

        Args:
            data: Dictionary containing collection info data

        Returns:
            CollectionInfo instance

        Raises:
            TypeError: If data is not a dictionary
            ValueError: If required fields are missing or invalid
        """
        if not isinstance(data, dict):
            raise TypeError(f"Expected dictionary, got {type(data).__name__}")

        return cls(
            name=data.get("name"),
            description=data.get("description"),
            schema=data.get("schema"),
        )

    def to_dict(self) -> dict:
        """
        Convert CollectionInfo to dictionary.

        Returns:
            Dictionary representation of CollectionInfo
        """
        result = {"name": self.name}
        if self.description is not None:
            result["description"] = self.description
        if self.schema is not None:
            result["schema"] = self.schema
        return result

    def __repr__(self) -> str:
        return f"CollectionInfo(name='{self.name}', description='{self.description}', schema='{self.schema}')"

    def __eq__(self, other) -> bool:
        if not isinstance(other, CollectionInfo):
            return False
        return (
            self.name == other.name
            and self.description == other.description
            and self.schema == other.schema
        )

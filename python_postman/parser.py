"""
Main entry point for parsing Postman collections.
"""

from typing import Dict, Any, Union
from pathlib import Path

from .models.collection import Collection
from .exceptions import CollectionValidationError
from .utils import parse_json_safely, load_json_file


class PythonPostman:
    """
    Main entry point class for loading and parsing Postman collections.
    """

    @classmethod
    def from_file(cls, file_path: Union[str, Path]) -> Collection:
        """
        Load a Postman collection from a JSON file.

        Args:
            file_path: Path to the collection.json file

        Returns:
            Parsed Collection object

        Raises:
            CollectionFileError: If file cannot be found or read
            CollectionParseError: If JSON parsing fails
            CollectionValidationError: If collection structure is invalid
        """
        collection_dict = load_json_file(file_path)
        return cls.from_dict(collection_dict)

    @classmethod
    def from_json(cls, json_string: str) -> Collection:
        """
        Parse a Postman collection from a JSON string.

        Args:
            json_string: JSON string containing the collection

        Returns:
            Parsed Collection object

        Raises:
            CollectionParseError: If JSON parsing fails
            CollectionValidationError: If collection structure is invalid
        """
        collection_dict = parse_json_safely(json_string)
        return cls.from_dict(collection_dict)

    @classmethod
    def from_dict(cls, collection_dict: Dict[str, Any]) -> Collection:
        """
        Create a Collection object from a dictionary.

        Args:
            collection_dict: Dictionary containing collection data

        Returns:
            Parsed Collection object

        Raises:
            CollectionValidationError: If collection structure is invalid
        """
        try:
            # Create collection from dictionary data
            collection = Collection.from_dict(collection_dict)

            # Validate the created collection
            validation_result = collection.validate()

            if not validation_result.is_valid:
                error_details = {
                    "validation_errors": validation_result.errors,
                    "error_count": len(validation_result.errors),
                }
                raise CollectionValidationError(
                    f"Collection validation failed with {len(validation_result.errors)} errors: {'; '.join(validation_result.errors[:3])}{'...' if len(validation_result.errors) > 3 else ''}",
                    details=error_details,
                )

            return collection

        except (KeyError, TypeError, ValueError) as e:
            # Handle errors during collection creation
            raise CollectionValidationError(
                f"Failed to create collection from data: {str(e)}",
                details={"creation_error": str(e), "error_type": type(e).__name__},
            ) from e

    @classmethod
    def create_collection(
        cls,
        name: str,
        description: str = "",
        schema: str = "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    ) -> Collection:
        """
        Create a new empty collection with basic metadata.

        Args:
            name: Name of the collection
            description: Optional description of the collection
            schema: Postman schema version URL

        Returns:
            New empty Collection object
        """
        from .models.collection_info import CollectionInfo

        info = CollectionInfo(name=name, description=description, schema=schema)
        return Collection(info=info)

    @classmethod
    def validate_collection_dict(cls, collection_dict: Dict[str, Any]) -> bool:
        """
        Validate a collection dictionary without creating a full Collection object.

        Args:
            collection_dict: Dictionary to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            collection = Collection.from_dict(collection_dict)
            validation_result = collection.validate()
            return validation_result.is_valid
        except Exception:
            return False

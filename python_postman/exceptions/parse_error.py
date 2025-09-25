"""
Exception for JSON parsing errors.
"""

from .base import PostmanCollectionError


class CollectionParseError(PostmanCollectionError):
    """
    Raised when JSON parsing fails during collection loading.

    This exception is raised when the provided JSON content cannot be parsed
    or when the JSON structure doesn't match expected format.
    """

    pass

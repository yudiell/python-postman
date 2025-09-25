"""
Exception for collection validation errors.
"""

from .base import PostmanCollectionError


class CollectionValidationError(PostmanCollectionError):
    """
    Raised when collection structure validation fails.

    This exception is raised when a collection doesn't conform to the expected
    Postman collection schema or when required fields are missing.
    """

    pass

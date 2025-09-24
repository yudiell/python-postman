"""
Exception for file operation errors.
"""

from .base import PostmanCollectionError


class CollectionFileError(PostmanCollectionError):
    """
    Raised when file operations fail during collection loading.

    This exception is raised when files cannot be found, read, or accessed
    during the collection loading process.
    """

    pass

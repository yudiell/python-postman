"""
Python Postman Collection Parser

A Python library for parsing and working with Postman collection.json files.

This library provides a clean, object-oriented interface for reading Postman collections
and accessing their components programmatically. It supports full collection parsing
including requests, folders, variables, authentication, and scripts.

Example:
    >>> from python_postman import PythonPostman
    >>> collection = PythonPostman.from_file("collection.json")
    >>> print(f"Collection: {collection.info.name}")
    >>> for request in collection.get_all_requests():
    ...     print(f"Request: {request.method} {request.name}")
"""

# Main API classes
from .parser import PythonPostman
from .models.collection import Collection, ValidationResult

# Core model classes
from .models.request import Request
from .models.folder import Folder
from .models.variable import Variable
from .models.auth import Auth, AuthType, AuthParameter
from .models.event import Event
from .models.url import Url, QueryParam
from .models.header import Header, HeaderCollection
from .models.body import Body, BodyMode, FormParameter
from .models.collection_info import CollectionInfo
from .models.item import Item

# Exception classes
from .exceptions import (
    PostmanCollectionError,
    CollectionParseError,
    CollectionValidationError,
    CollectionFileError,
)

# Utility functions
from .utils import parse_json_safely, load_json_file

__version__ = "0.1.0"
__author__ = "Python Postman Contributors"
__email__ = "python-postman@example.com"
__license__ = "MIT"
__description__ = (
    "A Python library for parsing and working with Postman collection.json files"
)

# Public API - these are the main classes/functions users should import
__all__ = [
    # Main entry point
    "PythonPostman",
    # Core model classes
    "Collection",
    "Request",
    "Folder",
    "Variable",
    "Auth",
    "AuthType",
    "AuthParameter",
    "Event",
    "Url",
    "QueryParam",
    "Header",
    "HeaderCollection",
    "Body",
    "BodyMode",
    "FormParameter",
    "CollectionInfo",
    "Item",
    # Validation
    "ValidationResult",
    # Exception classes
    "PostmanCollectionError",
    "CollectionParseError",
    "CollectionValidationError",
    "CollectionFileError",
    # Utility functions
    "parse_json_safely",
    "load_json_file",
]

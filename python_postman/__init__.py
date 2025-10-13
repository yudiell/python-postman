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
    >>> for request in collection.get_requests():
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
from .models.cookie import Cookie, CookieJar
from .models.response import Response, ExampleResponse

# Type definitions for enhanced type safety
from .types import (
    HttpMethod,
    HttpMethodLiteral,
    HttpMethodType,
    AuthTypeEnum,
    AuthTypeLiteral,
    AuthTypeType,
)

# Exception classes
from .exceptions import (
    PostmanCollectionError,
    CollectionParseError,
    CollectionValidationError,
    CollectionFileError,
)

# Utility functions
from .utils import parse_json_safely, load_json_file

# Introspection utilities
from .introspection import AuthResolver, AuthSource, ResolvedAuth

# Search and filtering
from .search import SearchResult, RequestQuery

# Statistics
from .statistics import CollectionStatistics

# Optional execution functionality (requires httpx)
try:
    from .execution import (
        RequestExecutor,
        ExecutionContext,
        ExecutionResponse,
        RequestExtensions,
        ExecutionResult,
        ScriptResults,
        ScriptAssertion,
        CollectionExecutionResult,
        FolderExecutionResult,
        VariableResolver,
        AuthHandler,
        ScriptRunner,
        ExecutionError,
        RequestExecutionError,
        VariableResolutionError,
        ScriptExecutionError,
        AuthenticationError,
        TimeoutError,
    )

    _EXECUTION_AVAILABLE = True
except ImportError:
    _EXECUTION_AVAILABLE = False

__version__ = "0.8.0"
__author__ = "Python Postman Contributors"
__email__ = "python-postman@example.com"
__license__ = "MIT"
__description__ = (
    "A Python library for parsing and working with Postman collection.json files"
)


def is_execution_available() -> bool:
    """
    Check if execution functionality is available.

    Returns:
        bool: True if httpx is installed and execution classes are available, False otherwise.
    """
    return _EXECUTION_AVAILABLE


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
    "Cookie",
    "CookieJar",
    "Response",
    "ExampleResponse",
    # Type definitions
    "HttpMethod",
    "HttpMethodLiteral",
    "HttpMethodType",
    "AuthTypeEnum",
    "AuthTypeLiteral",
    "AuthTypeType",
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
    # Introspection utilities
    "AuthResolver",
    "AuthSource",
    "ResolvedAuth",
    # Search and filtering
    "SearchResult",
    "RequestQuery",
    # Statistics
    "CollectionStatistics",
    # Execution availability check
    "is_execution_available",
]

# Add execution classes to __all__ if available
if _EXECUTION_AVAILABLE:
    __all__.extend(
        [
            # Core execution classes
            "RequestExecutor",
            "ExecutionContext",
            "ExecutionResponse",
            "RequestExtensions",
            # Result classes
            "ExecutionResult",
            "ScriptResults",
            "ScriptAssertion",
            "CollectionExecutionResult",
            "FolderExecutionResult",
            # Utility classes
            "VariableResolver",
            "AuthHandler",
            "ScriptRunner",
            # Exception classes
            "ExecutionError",
            "RequestExecutionError",
            "VariableResolutionError",
            "ScriptExecutionError",
            "AuthenticationError",
            "TimeoutError",
        ]
    )

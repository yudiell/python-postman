"""HTTP method type definitions for enhanced type safety."""

from typing import Literal, Union
from enum import Enum


class HttpMethod(str, Enum):
    """
    Enumeration of standard HTTP methods.
    
    This enum provides runtime validation and IDE autocomplete support
    for HTTP methods used in requests.
    """
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"
    TRACE = "TRACE"
    CONNECT = "CONNECT"


# Literal type for static type checking
HttpMethodLiteral = Literal[
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "TRACE",
    "CONNECT",
]

# Union type for flexibility - accepts both literal types and strings
HttpMethodType = Union[HttpMethodLiteral, str]

"""Authentication type definitions for enhanced type safety."""

from typing import Literal, Union
from enum import Enum


class AuthTypeEnum(str, Enum):
    """
    Enumeration of authentication types supported by Postman collections.
    
    This enum provides runtime validation and IDE autocomplete support
    for authentication types.
    """
    BASIC = "basic"
    BEARER = "bearer"
    DIGEST = "digest"
    HAWK = "hawk"
    NOAUTH = "noauth"
    OAUTH1 = "oauth1"
    OAUTH2 = "oauth2"
    NTLM = "ntlm"
    APIKEY = "apikey"
    AWSV4 = "awsv4"


# Literal type for static type checking
AuthTypeLiteral = Literal[
    "basic",
    "bearer",
    "digest",
    "hawk",
    "noauth",
    "oauth1",
    "oauth2",
    "ntlm",
    "apikey",
    "awsv4",
]

# Union type for flexibility - accepts both literal types and strings
AuthTypeType = Union[AuthTypeLiteral, str]

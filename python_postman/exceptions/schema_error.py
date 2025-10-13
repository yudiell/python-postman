"""
Schema version error exception.
"""

from .base import PostmanCollectionError


class SchemaVersionError(PostmanCollectionError):
    """
    Exception raised when a collection uses an unsupported schema version.
    
    This error is raised when:
    - The schema version is not recognized
    - The schema version is not supported by the library
    - The schema URL format is invalid
    """

    def __init__(self, message: str, schema_url: str = None, supported_versions: list = None):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            schema_url: The schema URL that caused the error
            supported_versions: List of supported schema versions
        """
        details = {}
        if schema_url:
            details["schema_url"] = schema_url
        if supported_versions:
            details["supported_versions"] = supported_versions
        
        super().__init__(message, details)
        self.schema_url = schema_url
        self.supported_versions = supported_versions

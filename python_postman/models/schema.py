"""
Schema version detection and validation for Postman collections.
"""

from typing import Optional, Tuple
from enum import Enum


class SchemaVersion(Enum):
    """
    Supported Postman collection schema versions.
    
    Attributes:
        V2_0_0: Postman Collection Format v2.0.0
        V2_1_0: Postman Collection Format v2.1.0
        UNKNOWN: Unknown or unsupported schema version
    """
    V2_0_0 = "v2.0.0"
    V2_1_0 = "v2.1.0"
    UNKNOWN = "unknown"

    def __str__(self) -> str:
        return self.value


class SchemaValidator:
    """
    Validates and manages Postman collection schema versions.
    
    This class provides utilities for detecting schema versions from URLs,
    validating version compatibility, and providing clear error messages
    for unsupported versions.
    """

    # Mapping of schema URLs to SchemaVersion enum values
    SUPPORTED_VERSIONS = {
        "https://schema.getpostman.com/json/collection/v2.0.0/collection.json": SchemaVersion.V2_0_0,
        "https://schema.getpostman.com/json/collection/v2.1.0/collection.json": SchemaVersion.V2_1_0,
    }

    @classmethod
    def detect_version(cls, schema_url: Optional[str]) -> SchemaVersion:
        """
        Detect schema version from a schema URL.
        
        Args:
            schema_url: The schema URL from the collection's info.schema field
            
        Returns:
            SchemaVersion enum value (V2_0_0, V2_1_0, or UNKNOWN)
            
        Examples:
            >>> SchemaValidator.detect_version(
            ...     "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            ... )
            <SchemaVersion.V2_1_0: 'v2.1.0'>
            
            >>> SchemaValidator.detect_version("invalid-url")
            <SchemaVersion.UNKNOWN: 'unknown'>
        """
        if not schema_url:
            return SchemaVersion.UNKNOWN
        
        # Exact match lookup
        if schema_url in cls.SUPPORTED_VERSIONS:
            return cls.SUPPORTED_VERSIONS[schema_url]
        
        # Fallback: try to detect version from URL pattern
        schema_lower = schema_url.lower()
        if "v2.1.0" in schema_lower or "v2_1_0" in schema_lower:
            return SchemaVersion.V2_1_0
        elif "v2.0.0" in schema_lower or "v2_0_0" in schema_lower:
            return SchemaVersion.V2_0_0
        
        return SchemaVersion.UNKNOWN

    @classmethod
    def validate_version(cls, schema_url: Optional[str]) -> Tuple[bool, Optional[str]]:
        """
        Validate if a schema version is supported.
        
        Args:
            schema_url: The schema URL from the collection's info.schema field
            
        Returns:
            Tuple of (is_valid, error_message):
                - is_valid: True if the schema version is supported, False otherwise
                - error_message: None if valid, descriptive error message if invalid
                
        Examples:
            >>> is_valid, error = SchemaValidator.validate_version(
            ...     "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            ... )
            >>> print(is_valid)
            True
            >>> print(error)
            None
            
            >>> is_valid, error = SchemaValidator.validate_version("invalid-schema")
            >>> print(is_valid)
            False
            >>> print(error)
            Unsupported schema version: 'invalid-schema'. Supported versions: v2.0.0, v2.1.0
        """
        if not schema_url:
            return False, (
                "No schema version specified. "
                f"Supported versions: {', '.join(v.value for v in [SchemaVersion.V2_0_0, SchemaVersion.V2_1_0])}"
            )
        
        version = cls.detect_version(schema_url)
        
        if version == SchemaVersion.UNKNOWN:
            supported_list = ", ".join(v.value for v in [SchemaVersion.V2_0_0, SchemaVersion.V2_1_0])
            return False, (
                f"Unsupported schema version: '{schema_url}'. "
                f"Supported versions: {supported_list}"
            )
        
        return True, None

    @classmethod
    def get_supported_versions(cls) -> list:
        """
        Get a list of all supported schema versions.
        
        Returns:
            List of SchemaVersion enum values (excluding UNKNOWN)
        """
        return [SchemaVersion.V2_0_0, SchemaVersion.V2_1_0]

    @classmethod
    def is_supported(cls, schema_url: Optional[str]) -> bool:
        """
        Check if a schema version is supported.
        
        Args:
            schema_url: The schema URL to check
            
        Returns:
            True if supported, False otherwise
        """
        is_valid, _ = cls.validate_version(schema_url)
        return is_valid

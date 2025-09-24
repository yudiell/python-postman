"""
Validation utilities and result classes.
"""

from typing import List, Optional


class ValidationResult:
    """
    Contains the result of collection validation.
    """

    def __init__(
        self,
        is_valid: bool,
        errors: Optional[List[str]] = None,
        warnings: Optional[List[str]] = None,
    ):
        """
        Initialize a ValidationResult.

        Args:
            is_valid: Whether the validation passed
            errors: List of validation errors
            warnings: List of validation warnings
        """
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def __str__(self) -> str:
        status = "Valid" if self.is_valid else "Invalid"
        return f"ValidationResult(status={status}, errors={len(self.errors)}, warnings={len(self.warnings)})"

    def __repr__(self) -> str:
        return f"ValidationResult(is_valid={self.is_valid}, errors={self.errors}, warnings={self.warnings})"

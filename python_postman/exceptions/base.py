"""
Base exception class for all Postman collection related errors.
"""


class PostmanCollectionError(Exception):
    """
    Base exception class for all Postman collection parsing and processing errors.

    This serves as the parent class for all specific error types in the library.
    """

    def __init__(self, message: str, details: dict = None):
        """
        Initialize the exception.

        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (Details: {self.details})"
        return self.message

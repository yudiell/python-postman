"""Variable model for Postman collection variables."""

from typing import Optional, Any, Dict
from enum import Enum


class VariableType(Enum):
    """Enumeration of variable types."""

    STRING = "string"
    BOOLEAN = "boolean"
    NUMBER = "number"
    ANY = "any"


class VariableScope(Enum):
    """Enumeration of variable scopes."""

    COLLECTION = "collection"
    FOLDER = "folder"
    REQUEST = "request"


class Variable:
    """Represents a variable with key, value, type, and description."""

    def __init__(
        self,
        key: str,
        value: Any = None,
        type: Optional[str] = None,
        description: Optional[str] = None,
        disabled: bool = False,
    ):
        """
        Initialize Variable.

        Args:
            key: Variable key/name (required)
            value: Variable value (optional)
            type: Variable type (optional)
            description: Variable description (optional)
            disabled: Whether variable is disabled (default: False)
        """
        self.key = key
        self.value = value
        self.type = type
        self.description = description
        self.disabled = disabled
        self._scope: Optional[VariableScope] = None

    @property
    def scope(self) -> Optional[VariableScope]:
        """Get the variable scope."""
        return self._scope

    def set_scope(self, scope: VariableScope) -> None:
        """Set the variable scope."""
        self._scope = scope

    def resolve_value(self, context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Resolve the variable value, potentially using context for nested variables.

        Args:
            context: Dictionary of variables for resolution

        Returns:
            Resolved variable value
        """
        if self.disabled:
            return None

        if self.value is None:
            return None

        # If value is a string and contains variable references, resolve them
        if isinstance(self.value, str) and context:
            resolved_value = self.value
            for var_key, var_value in context.items():
                if var_key != self.key:  # Avoid self-reference
                    placeholder = f"{{{{{var_key}}}}}"
                    if placeholder in resolved_value:
                        resolved_value = resolved_value.replace(
                            placeholder, str(var_value)
                        )
            return resolved_value

        return self.value

    def get_type(self) -> VariableType:
        """
        Get the variable type, inferring from value if not explicitly set.

        Returns:
            VariableType enum value
        """
        if self.type:
            try:
                return VariableType(self.type.lower())
            except ValueError:
                pass

        # Infer type from value
        if self.value is None:
            return VariableType.ANY
        elif isinstance(self.value, bool):
            return VariableType.BOOLEAN
        elif isinstance(self.value, (int, float)):
            return VariableType.NUMBER
        elif isinstance(self.value, str):
            return VariableType.STRING
        else:
            return VariableType.ANY

    def validate(self) -> bool:
        """
        Validate the variable.

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        if not self.key or not isinstance(self.key, str) or not self.key.strip():
            raise ValueError("Variable key is required and must be a non-empty string")

        if self.type is not None and not isinstance(self.type, str):
            raise ValueError("Variable type must be a string if provided")

        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("Variable description must be a string if provided")

        if not isinstance(self.disabled, bool):
            raise ValueError("Variable disabled flag must be a boolean")

        return True

    @classmethod
    def from_dict(cls, data: dict) -> "Variable":
        """
        Create Variable from dictionary data.

        Args:
            data: Dictionary containing variable data

        Returns:
            Variable instance
        """
        return cls(
            key=data.get("key"),
            value=data.get("value"),
            type=data.get("type"),
            description=data.get("description"),
            disabled=data.get("disabled", False),
        )

    def to_dict(self) -> dict:
        """
        Convert Variable to dictionary.

        Returns:
            Dictionary representation of Variable
        """
        result = {"key": self.key, "disabled": self.disabled}

        if self.value is not None:
            result["value"] = self.value
        if self.type is not None:
            result["type"] = self.type
        if self.description is not None:
            result["description"] = self.description

        return result

    def __repr__(self) -> str:
        return f"Variable(key='{self.key}', value={self.value!r}, type='{self.type}', disabled={self.disabled})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Variable):
            return False
        return (
            self.key == other.key
            and self.value == other.value
            and self.type == other.type
            and self.description == other.description
            and self.disabled == other.disabled
        )

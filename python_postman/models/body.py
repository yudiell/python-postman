"""Body model for Postman collection HTTP request bodies."""

from typing import Optional, List, Dict, Any, Union
from enum import Enum
import json


class BodyMode(Enum):
    """Enumeration of body modes."""

    RAW = "raw"
    URLENCODED = "urlencoded"
    FORMDATA = "formdata"
    FILE = "file"
    BINARY = "binary"
    GRAPHQL = "graphql"


class FormParameter:
    """Represents a form parameter for form-data or urlencoded bodies."""

    def __init__(
        self,
        key: str,
        value: Optional[str] = None,
        description: Optional[str] = None,
        disabled: bool = False,
        type: str = "text",
        src: Optional[str] = None,
    ):
        """
        Initialize FormParameter.

        Args:
            key: Parameter key/name (required)
            value: Parameter value (optional)
            description: Parameter description (optional)
            disabled: Whether parameter is disabled (default: False)
            type: Parameter type ('text' or 'file')
            src: Source file path for file type parameters
        """
        self.key = key
        self.value = value
        self.description = description
        self.disabled = disabled
        self.type = type
        self.src = src

    def is_file(self) -> bool:
        """
        Check if this parameter represents a file.

        Returns:
            True if parameter type is 'file'
        """
        return self.type == "file"

    def is_active(self) -> bool:
        """
        Check if parameter is active (not disabled and has a key).

        Returns:
            True if parameter is active
        """
        return not self.disabled and bool(self.key)

    def get_effective_value(
        self, variable_context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Get the effective parameter value, resolving variables if context is provided.

        Args:
            variable_context: Dictionary of variables for resolution

        Returns:
            Resolved parameter value or None if disabled/empty
        """
        if self.disabled or not self.value:
            return None

        if not variable_context:
            return self.value

        # Resolve variable placeholders
        resolved_value = self.value
        for var_name, var_value in variable_context.items():
            placeholder = f"{{{{{var_name}}}}}"
            if placeholder in resolved_value:
                resolved_value = resolved_value.replace(placeholder, str(var_value))

        return resolved_value

    def validate(self) -> bool:
        """
        Validate the form parameter.

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        if not self.key or not isinstance(self.key, str) or not self.key.strip():
            raise ValueError(
                "Form parameter key is required and must be a non-empty string"
            )

        if self.value is not None and not isinstance(self.value, str):
            raise ValueError("Form parameter value must be a string if provided")

        if self.description is not None and not isinstance(self.description, str):
            raise ValueError("Form parameter description must be a string if provided")

        if not isinstance(self.disabled, bool):
            raise ValueError("Form parameter disabled flag must be a boolean")

        if self.type not in ["text", "file"]:
            raise ValueError("Form parameter type must be 'text' or 'file'")

        if self.src is not None and not isinstance(self.src, str):
            raise ValueError("Form parameter src must be a string if provided")

        return True

    @classmethod
    def from_dict(cls, data: dict) -> "FormParameter":
        """
        Create FormParameter from dictionary data.

        Args:
            data: Dictionary containing form parameter data

        Returns:
            FormParameter instance
        """
        return cls(
            key=data.get("key", ""),
            value=data.get("value"),
            description=data.get("description"),
            disabled=data.get("disabled", False),
            type=data.get("type", "text"),
            src=data.get("src"),
        )

    def to_dict(self) -> dict:
        """
        Convert FormParameter to dictionary.

        Returns:
            Dictionary representation of FormParameter
        """
        result = {"key": self.key, "disabled": self.disabled, "type": self.type}

        if self.value is not None:
            result["value"] = self.value
        if self.description is not None:
            result["description"] = self.description
        if self.src is not None:
            result["src"] = self.src

        return result

    def __repr__(self) -> str:
        return f"FormParameter(key='{self.key}', value={self.value!r}, type='{self.type}', disabled={self.disabled})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, FormParameter):
            return False
        return (
            self.key == other.key
            and self.value == other.value
            and self.description == other.description
            and self.disabled == other.disabled
            and self.type == other.type
            and self.src == other.src
        )


class Body:
    """Represents HTTP request body supporting different content types."""

    def __init__(
        self,
        mode: Optional[str] = None,
        raw: Optional[str] = None,
        urlencoded: Optional[List[FormParameter]] = None,
        formdata: Optional[List[FormParameter]] = None,
        file: Optional[Dict[str, str]] = None,
        disabled: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Body.

        Args:
            mode: Body mode (raw, urlencoded, formdata, file, binary, graphql)
            raw: Raw body content for raw mode
            urlencoded: List of FormParameter for urlencoded mode
            formdata: List of FormParameter for formdata mode
            file: File information for file mode
            disabled: Whether body is disabled
            options: Additional options (e.g., raw language settings)
        """
        self.mode = mode
        self.raw = raw
        self.urlencoded = urlencoded or []
        self.formdata = formdata or []
        self.file = file or {}
        self.disabled = disabled
        self.options = options or {}

    def get_mode(self) -> Optional[BodyMode]:
        """
        Get the body mode as enum.

        Returns:
            BodyMode enum value or None if mode is not set
        """
        if not self.mode:
            return None

        try:
            return BodyMode(self.mode.lower())
        except ValueError:
            return None

    def is_active(self) -> bool:
        """
        Check if body is active (not disabled and has content).

        Returns:
            True if body is active
        """
        if self.disabled:
            return False

        mode = self.get_mode()
        if not mode:
            return False

        if mode == BodyMode.RAW:
            return bool(self.raw)
        elif mode == BodyMode.URLENCODED:
            return any(param.is_active() for param in self.urlencoded)
        elif mode == BodyMode.FORMDATA:
            return any(param.is_active() for param in self.formdata)
        elif mode == BodyMode.FILE:
            return bool(self.file.get("src"))
        elif mode in [BodyMode.BINARY, BodyMode.GRAPHQL]:
            return bool(self.raw)

        return False

    def get_content_type(self) -> Optional[str]:
        """
        Get the appropriate Content-Type header for this body.

        Returns:
            Content-Type string or None
        """
        mode = self.get_mode()
        if not mode:
            return None

        if mode == BodyMode.RAW:
            # Check options for raw language/type
            raw_options = self.options.get("raw", {})
            language = raw_options.get("language")

            if language == "json":
                return "application/json"
            elif language == "xml":
                return "application/xml"
            elif language == "html":
                return "text/html"
            elif language == "text":
                return "text/plain"
            else:
                return "text/plain"
        elif mode == BodyMode.URLENCODED:
            return "application/x-www-form-urlencoded"
        elif mode == BodyMode.FORMDATA:
            return "multipart/form-data"
        elif mode == BodyMode.GRAPHQL:
            return "application/json"

        return None

    def get_content(
        self, variable_context: Optional[Dict[str, Any]] = None
    ) -> Optional[Union[str, bytes, Dict[str, Any]]]:
        """
        Get the body content in appropriate format.

        Args:
            variable_context: Dictionary of variables for resolution

        Returns:
            Body content in appropriate format or None if disabled/empty
        """
        if not self.is_active():
            return None

        mode = self.get_mode()
        if not mode:
            return None

        if mode == BodyMode.RAW:
            content = self.raw
            if content and variable_context:
                # Resolve variables in raw content
                for var_name, var_value in variable_context.items():
                    placeholder = f"{{{{{var_name}}}}}"
                    if placeholder in content:
                        content = content.replace(placeholder, str(var_value))
            return content

        elif mode == BodyMode.URLENCODED:
            # Return as dictionary for URL encoding
            result = {}
            for param in self.urlencoded:
                if param.is_active():
                    value = param.get_effective_value(variable_context)
                    if value is not None:
                        result[param.key] = value
            return result

        elif mode == BodyMode.FORMDATA:
            # Return as list of tuples for multipart form data
            result = []
            for param in self.formdata:
                if param.is_active():
                    if param.is_file():
                        # File parameter - use src if available, otherwise value
                        file_value = param.src or param.value or ""
                        result.append((param.key, file_value, "file"))
                    else:
                        # Text parameter
                        value = param.get_effective_value(variable_context)
                        if value is not None:
                            result.append((param.key, value, "text"))
            return result

        elif mode == BodyMode.GRAPHQL:
            # GraphQL body is typically JSON with query/variables
            if self.raw:
                try:
                    # Try to parse as JSON to validate structure
                    graphql_data = json.loads(self.raw)
                    if variable_context:
                        # Resolve variables in the JSON string
                        content = self.raw
                        for var_name, var_value in variable_context.items():
                            placeholder = f"{{{{{var_name}}}}}"
                            if placeholder in content:
                                content = content.replace(placeholder, str(var_value))
                        return json.loads(content)
                    return graphql_data
                except json.JSONDecodeError:
                    # Return as raw string if not valid JSON
                    return self.raw
            return None

        elif mode == BodyMode.FILE:
            # Return file path
            return self.file.get("src")

        return None

    def add_form_parameter(
        self, key: str, value: Optional[str] = None, param_type: str = "text"
    ) -> FormParameter:
        """
        Add a form parameter to formdata or urlencoded based on current mode.

        Args:
            key: Parameter key
            value: Parameter value
            param_type: Parameter type ('text' or 'file')

        Returns:
            The created FormParameter object
        """
        param = FormParameter(key=key, value=value, type=param_type)

        mode = self.get_mode()
        if mode == BodyMode.FORMDATA:
            self.formdata.append(param)
        elif mode == BodyMode.URLENCODED:
            self.urlencoded.append(param)
        else:
            # Default to formdata if no mode set
            if not self.mode:
                self.mode = BodyMode.FORMDATA.value
            self.formdata.append(param)

        return param

    def remove_form_parameter(self, key: str) -> bool:
        """
        Remove form parameter by key.

        Args:
            key: Parameter key to remove

        Returns:
            True if parameter was found and removed
        """
        mode = self.get_mode()

        if mode == BodyMode.FORMDATA:
            original_length = len(self.formdata)
            self.formdata = [p for p in self.formdata if p.key != key]
            return len(self.formdata) < original_length
        elif mode == BodyMode.URLENCODED:
            original_length = len(self.urlencoded)
            self.urlencoded = [p for p in self.urlencoded if p.key != key]
            return len(self.urlencoded) < original_length

        return False

    def get_form_parameter(self, key: str) -> Optional[FormParameter]:
        """
        Get form parameter by key.

        Args:
            key: Parameter key to find

        Returns:
            FormParameter if found, None otherwise
        """
        mode = self.get_mode()

        if mode == BodyMode.FORMDATA:
            for param in self.formdata:
                if param.key == key:
                    return param
        elif mode == BodyMode.URLENCODED:
            for param in self.urlencoded:
                if param.key == key:
                    return param

        return None

    def validate(self) -> bool:
        """
        Validate the body structure.

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        if self.mode is not None and not isinstance(self.mode, str):
            raise ValueError("Body mode must be a string if provided")

        if self.raw is not None and not isinstance(self.raw, str):
            raise ValueError("Body raw content must be a string if provided")

        if not isinstance(self.disabled, bool):
            raise ValueError("Body disabled flag must be a boolean")

        if not isinstance(self.options, dict):
            raise ValueError("Body options must be a dictionary")

        # Validate form parameters
        for param in self.urlencoded:
            if not isinstance(param, FormParameter):
                raise ValueError("All urlencoded items must be FormParameter instances")
            param.validate()

        for param in self.formdata:
            if not isinstance(param, FormParameter):
                raise ValueError("All formdata items must be FormParameter instances")
            param.validate()

        # Validate GraphQL content if mode is GraphQL
        if self.get_mode() == BodyMode.GRAPHQL and self.raw:
            try:
                json.loads(self.raw)
            except json.JSONDecodeError:
                # Allow non-JSON content for GraphQL (could be just a query string)
                pass

        return True

    @classmethod
    def from_dict(cls, data: dict) -> "Body":
        """
        Create Body from dictionary data.

        Args:
            data: Dictionary containing body data

        Returns:
            Body instance
        """
        urlencoded_params = []
        if "urlencoded" in data and isinstance(data["urlencoded"], list):
            for param_data in data["urlencoded"]:
                if isinstance(param_data, dict):
                    urlencoded_params.append(FormParameter.from_dict(param_data))

        formdata_params = []
        if "formdata" in data and isinstance(data["formdata"], list):
            for param_data in data["formdata"]:
                if isinstance(param_data, dict):
                    formdata_params.append(FormParameter.from_dict(param_data))

        return cls(
            mode=data.get("mode"),
            raw=data.get("raw"),
            urlencoded=urlencoded_params,
            formdata=formdata_params,
            file=data.get("file", {}),
            disabled=data.get("disabled", False),
            options=data.get("options", {}),
        )

    def to_dict(self) -> dict:
        """
        Convert Body to dictionary.

        Returns:
            Dictionary representation of Body
        """
        result = {"disabled": self.disabled, "options": self.options}

        if self.mode is not None:
            result["mode"] = self.mode
        if self.raw is not None:
            result["raw"] = self.raw
        if self.urlencoded:
            result["urlencoded"] = [param.to_dict() for param in self.urlencoded]
        if self.formdata:
            result["formdata"] = [param.to_dict() for param in self.formdata]
        if self.file:
            result["file"] = self.file

        return result

    def __repr__(self) -> str:
        return f"Body(mode='{self.mode}', disabled={self.disabled})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Body):
            return False
        return (
            self.mode == other.mode
            and self.raw == other.raw
            and self.urlencoded == other.urlencoded
            and self.formdata == other.formdata
            and self.file == other.file
            and self.disabled == other.disabled
            and self.options == other.options
        )

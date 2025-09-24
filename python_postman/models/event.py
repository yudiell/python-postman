"""Event model for Postman collection events (pre-request scripts and tests)."""

from typing import Optional, List, Union
from enum import Enum


class EventType(Enum):
    """Enumeration of event types."""

    PREREQUEST = "prerequest"
    TEST = "test"


class Event:
    """Represents an event with script content and event type."""

    def __init__(
        self,
        listen: str,
        script: Optional[Union[str, List[str], dict]] = None,
        disabled: bool = False,
    ):
        """
        Initialize Event.

        Args:
            listen: Event type to listen for (e.g., "prerequest", "test")
            script: Script content (string, list of strings, or script object)
            disabled: Whether the event is disabled (default: False)
        """
        self.listen = listen
        self.script = script
        self.disabled = disabled

    def get_event_type(self) -> EventType:
        """
        Get the event type as enum.

        Returns:
            EventType enum value, defaults to TEST for unknown types
        """
        try:
            return EventType(self.listen.lower())
        except (ValueError, AttributeError):
            return EventType.TEST

    def is_prerequest(self) -> bool:
        """Check if this is a pre-request event."""
        return self.get_event_type() == EventType.PREREQUEST

    def is_test(self) -> bool:
        """Check if this is a test event."""
        return self.get_event_type() == EventType.TEST

    def get_script_content(self) -> Optional[str]:
        """
        Get the script content as a string.

        Returns:
            Script content as string, or None if no script
        """
        if self.script is None:
            return None

        if isinstance(self.script, str):
            return self.script

        if isinstance(self.script, list):
            # Join list of script lines
            return "\n".join(str(line) for line in self.script)

        if isinstance(self.script, dict):
            # Extract script from script object
            if "exec" in self.script:
                exec_content = self.script["exec"]
                if isinstance(exec_content, str):
                    return exec_content
                elif isinstance(exec_content, list):
                    return "\n".join(str(line) for line in exec_content)
            elif "src" in self.script:
                # Script from external source
                return f"// Script from: {self.script['src']}"

        return str(self.script)

    def get_script_lines(self) -> List[str]:
        """
        Get the script content as a list of lines.

        Returns:
            List of script lines, empty list if no script
        """
        content = self.get_script_content()
        if content is None:
            return []

        return content.split("\n")

    def get_script_type(self) -> Optional[str]:
        """
        Get the script type if available.

        Returns:
            Script type string or None
        """
        if isinstance(self.script, dict):
            return self.script.get("type")
        return None

    def get_script_id(self) -> Optional[str]:
        """
        Get the script ID if available.

        Returns:
            Script ID string or None
        """
        if isinstance(self.script, dict):
            return self.script.get("id")
        return None

    def get_script_name(self) -> Optional[str]:
        """
        Get the script name if available.

        Returns:
            Script name string or None
        """
        if isinstance(self.script, dict):
            return self.script.get("name")
        return None

    def has_script(self) -> bool:
        """
        Check if the event has script content.

        Returns:
            True if event has script content, False otherwise
        """
        if self.disabled:
            return False

        content = self.get_script_content()
        return content is not None and content.strip() != ""

    def validate(self) -> bool:
        """
        Validate the event.

        Returns:
            True if validation passes

        Raises:
            ValueError: If validation fails
        """
        if not self.listen or not isinstance(self.listen, str):
            raise ValueError("Event listen type is required and must be a string")

        if not isinstance(self.disabled, bool):
            raise ValueError("Event disabled flag must be a boolean")

        # Validate script if present
        if self.script is not None:
            if not isinstance(self.script, (str, list, dict)):
                raise ValueError("Event script must be a string, list, or dict")

            if isinstance(self.script, dict):
                # Validate script object structure
                if "exec" not in self.script and "src" not in self.script:
                    raise ValueError(
                        "Script object must contain 'exec' or 'src' property"
                    )

        return True

    @classmethod
    def from_dict(cls, data: dict) -> "Event":
        """
        Create Event from dictionary data.

        Args:
            data: Dictionary containing event data

        Returns:
            Event instance
        """
        return cls(
            listen=data.get("listen"),
            script=data.get("script"),
            disabled=data.get("disabled", False),
        )

    def to_dict(self) -> dict:
        """
        Convert Event to dictionary.

        Returns:
            Dictionary representation of Event
        """
        result = {"listen": self.listen, "disabled": self.disabled}

        if self.script is not None:
            result["script"] = self.script

        return result

    def __repr__(self) -> str:
        script_repr = repr(self.script)
        if len(script_repr) > 50:
            script_repr = f"{script_repr[:47]}..."
        return f"Event(listen='{self.listen}', script={script_repr}, disabled={self.disabled})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, Event):
            return False
        return (
            self.listen == other.listen
            and self.script == other.script
            and self.disabled == other.disabled
        )

"""Unit tests for Event model."""

import pytest
from python_postman.models.event import Event, EventType


class TestEvent:
    """Test cases for Event class."""

    def test_init_minimal(self):
        """Test Event initialization with minimal parameters."""
        event = Event(listen="test")
        assert event.listen == "test"
        assert event.script is None
        assert event.disabled is False

    def test_init_complete(self):
        """Test Event initialization with all parameters."""
        script = "console.log('test');"
        event = Event(listen="prerequest", script=script, disabled=True)
        assert event.listen == "prerequest"
        assert event.script == script
        assert event.disabled is True

    def test_get_event_type_prerequest(self):
        """Test getting prerequest event type."""
        event = Event(listen="prerequest")
        assert event.get_event_type() == EventType.PREREQUEST

        event = Event(listen="PREREQUEST")
        assert event.get_event_type() == EventType.PREREQUEST

    def test_get_event_type_test(self):
        """Test getting test event type."""
        event = Event(listen="test")
        assert event.get_event_type() == EventType.TEST

        event = Event(listen="TEST")
        assert event.get_event_type() == EventType.TEST

    def test_get_event_type_invalid(self):
        """Test getting invalid event type defaults to TEST."""
        event = Event(listen="invalid")
        assert event.get_event_type() == EventType.TEST

        event = Event(listen=None)
        assert event.get_event_type() == EventType.TEST

    def test_is_prerequest(self):
        """Test prerequest event type checking."""
        event = Event(listen="prerequest")
        assert event.is_prerequest() is True
        assert event.is_test() is False

    def test_is_test(self):
        """Test test event type checking."""
        event = Event(listen="test")
        assert event.is_test() is True
        assert event.is_prerequest() is False

    def test_get_script_content_none(self):
        """Test getting script content when None."""
        event = Event(listen="test")
        assert event.get_script_content() is None

    def test_get_script_content_string(self):
        """Test getting script content as string."""
        script = "console.log('test');"
        event = Event(listen="test", script=script)
        assert event.get_script_content() == script

    def test_get_script_content_list(self):
        """Test getting script content from list."""
        script_lines = ["console.log('line 1');", "console.log('line 2');"]
        event = Event(listen="test", script=script_lines)
        expected = "console.log('line 1');\nconsole.log('line 2');"
        assert event.get_script_content() == expected

    def test_get_script_content_dict_exec_string(self):
        """Test getting script content from dict with exec string."""
        script_dict = {"exec": "console.log('test');", "type": "text/javascript"}
        event = Event(listen="test", script=script_dict)
        assert event.get_script_content() == "console.log('test');"

    def test_get_script_content_dict_exec_list(self):
        """Test getting script content from dict with exec list."""
        script_dict = {"exec": ["console.log('line 1');", "console.log('line 2');"]}
        event = Event(listen="test", script=script_dict)
        expected = "console.log('line 1');\nconsole.log('line 2');"
        assert event.get_script_content() == expected

    def test_get_script_content_dict_src(self):
        """Test getting script content from dict with src."""
        script_dict = {"src": "external-script.js"}
        event = Event(listen="test", script=script_dict)
        expected = "// Script from: external-script.js"
        assert event.get_script_content() == expected

    def test_get_script_content_dict_fallback(self):
        """Test getting script content from dict fallback."""
        script_dict = {"other": "value"}
        event = Event(listen="test", script=script_dict)
        assert event.get_script_content() == str(script_dict)

    def test_get_script_lines_none(self):
        """Test getting script lines when None."""
        event = Event(listen="test")
        assert event.get_script_lines() == []

    def test_get_script_lines_string(self):
        """Test getting script lines from string."""
        script = "line 1\nline 2\nline 3"
        event = Event(listen="test", script=script)
        expected = ["line 1", "line 2", "line 3"]
        assert event.get_script_lines() == expected

    def test_get_script_lines_single_line(self):
        """Test getting script lines from single line."""
        script = "console.log('test');"
        event = Event(listen="test", script=script)
        expected = ["console.log('test');"]
        assert event.get_script_lines() == expected

    def test_get_script_type_dict(self):
        """Test getting script type from dict."""
        script_dict = {"exec": "test", "type": "text/javascript"}
        event = Event(listen="test", script=script_dict)
        assert event.get_script_type() == "text/javascript"

    def test_get_script_type_non_dict(self):
        """Test getting script type from non-dict."""
        event = Event(listen="test", script="test")
        assert event.get_script_type() is None

    def test_get_script_type_missing(self):
        """Test getting script type when missing."""
        script_dict = {"exec": "test"}
        event = Event(listen="test", script=script_dict)
        assert event.get_script_type() is None

    def test_get_script_id_dict(self):
        """Test getting script ID from dict."""
        script_dict = {"exec": "test", "id": "script-123"}
        event = Event(listen="test", script=script_dict)
        assert event.get_script_id() == "script-123"

    def test_get_script_id_non_dict(self):
        """Test getting script ID from non-dict."""
        event = Event(listen="test", script="test")
        assert event.get_script_id() is None

    def test_get_script_id_missing(self):
        """Test getting script ID when missing."""
        script_dict = {"exec": "test"}
        event = Event(listen="test", script=script_dict)
        assert event.get_script_id() is None

    def test_get_script_name_dict(self):
        """Test getting script name from dict."""
        script_dict = {"exec": "test", "name": "My Script"}
        event = Event(listen="test", script=script_dict)
        assert event.get_script_name() == "My Script"

    def test_get_script_name_non_dict(self):
        """Test getting script name from non-dict."""
        event = Event(listen="test", script="test")
        assert event.get_script_name() is None

    def test_get_script_name_missing(self):
        """Test getting script name when missing."""
        script_dict = {"exec": "test"}
        event = Event(listen="test", script=script_dict)
        assert event.get_script_name() is None

    def test_has_script_true(self):
        """Test has_script returns True for valid script."""
        event = Event(listen="test", script="console.log('test');")
        assert event.has_script() is True

    def test_has_script_false_none(self):
        """Test has_script returns False for None script."""
        event = Event(listen="test")
        assert event.has_script() is False

    def test_has_script_false_empty(self):
        """Test has_script returns False for empty script."""
        event = Event(listen="test", script="")
        assert event.has_script() is False

        event = Event(listen="test", script="   ")
        assert event.has_script() is False

    def test_has_script_false_disabled(self):
        """Test has_script returns False for disabled event."""
        event = Event(listen="test", script="console.log('test');", disabled=True)
        assert event.has_script() is False

    def test_has_script_list(self):
        """Test has_script with list script."""
        event = Event(listen="test", script=["console.log('test');"])
        assert event.has_script() is True

        event = Event(listen="test", script=[])
        assert event.has_script() is False

    def test_has_script_dict(self):
        """Test has_script with dict script."""
        script_dict = {"exec": "console.log('test');"}
        event = Event(listen="test", script=script_dict)
        assert event.has_script() is True

        script_dict = {"exec": ""}
        event = Event(listen="test", script=script_dict)
        assert event.has_script() is False

    def test_validate_success(self):
        """Test successful validation."""
        event = Event(listen="test", script="console.log('test');")
        assert event.validate() is True

    def test_validate_success_minimal(self):
        """Test successful validation with minimal data."""
        event = Event(listen="test")
        assert event.validate() is True

    def test_validate_empty_listen_fails(self):
        """Test validation fails with empty listen."""
        event = Event(listen="")
        with pytest.raises(ValueError, match="Event listen type is required"):
            event.validate()

    def test_validate_none_listen_fails(self):
        """Test validation fails with None listen."""
        event = Event(listen=None)
        with pytest.raises(ValueError, match="Event listen type is required"):
            event.validate()

    def test_validate_non_string_listen_fails(self):
        """Test validation fails with non-string listen."""
        event = Event(listen=123)
        with pytest.raises(ValueError, match="Event listen type is required"):
            event.validate()

    def test_validate_non_boolean_disabled_fails(self):
        """Test validation fails with non-boolean disabled."""
        event = Event(listen="test", disabled="true")
        with pytest.raises(ValueError, match="Event disabled flag must be a boolean"):
            event.validate()

    def test_validate_invalid_script_type_fails(self):
        """Test validation fails with invalid script type."""
        event = Event(listen="test", script=123)
        with pytest.raises(
            ValueError, match="Event script must be a string, list, or dict"
        ):
            event.validate()

    def test_validate_invalid_script_dict_fails(self):
        """Test validation fails with invalid script dict."""
        event = Event(listen="test", script={"other": "value"})
        with pytest.raises(
            ValueError, match="Script object must contain 'exec' or 'src'"
        ):
            event.validate()

    def test_validate_valid_script_dict_exec(self):
        """Test validation succeeds with valid script dict containing exec."""
        event = Event(listen="test", script={"exec": "console.log('test');"})
        assert event.validate() is True

    def test_validate_valid_script_dict_src(self):
        """Test validation succeeds with valid script dict containing src."""
        event = Event(listen="test", script={"src": "script.js"})
        assert event.validate() is True

    def test_from_dict_minimal(self):
        """Test creating Event from minimal dictionary."""
        data = {"listen": "test"}
        event = Event.from_dict(data)
        assert event.listen == "test"
        assert event.script is None
        assert event.disabled is False

    def test_from_dict_complete(self):
        """Test creating Event from complete dictionary."""
        data = {
            "listen": "prerequest",
            "script": "console.log('test');",
            "disabled": True,
        }
        event = Event.from_dict(data)
        assert event.listen == "prerequest"
        assert event.script == "console.log('test');"
        assert event.disabled is True

    def test_from_dict_script_dict(self):
        """Test creating Event from dictionary with script dict."""
        data = {
            "listen": "test",
            "script": {
                "exec": ["console.log('line 1');", "console.log('line 2');"],
                "type": "text/javascript",
            },
        }
        event = Event.from_dict(data)
        assert event.listen == "test"
        assert event.script == data["script"]
        assert event.disabled is False

    def test_from_dict_missing_listen(self):
        """Test creating Event from dictionary without listen."""
        data = {"script": "console.log('test');"}
        event = Event.from_dict(data)
        assert event.listen is None
        assert event.script == "console.log('test');"

    def test_to_dict_minimal(self):
        """Test converting Event to dictionary with minimal data."""
        event = Event(listen="test")
        result = event.to_dict()
        expected = {"listen": "test", "disabled": False}
        assert result == expected

    def test_to_dict_complete(self):
        """Test converting Event to dictionary with complete data."""
        script = "console.log('test');"
        event = Event(listen="prerequest", script=script, disabled=True)
        result = event.to_dict()
        expected = {"listen": "prerequest", "script": script, "disabled": True}
        assert result == expected

    def test_to_dict_script_dict(self):
        """Test converting Event to dictionary with script dict."""
        script_dict = {"exec": "console.log('test');", "type": "text/javascript"}
        event = Event(listen="test", script=script_dict)
        result = event.to_dict()
        expected = {"listen": "test", "script": script_dict, "disabled": False}
        assert result == expected

    def test_repr_short_script(self):
        """Test string representation with short script."""
        event = Event(listen="test", script="short", disabled=False)
        expected = "Event(listen='test', script='short', disabled=False)"
        assert repr(event) == expected

    def test_repr_long_script(self):
        """Test string representation with long script."""
        long_script = "a" * 60
        event = Event(listen="test", script=long_script, disabled=False)
        result = repr(event)
        assert result.startswith("Event(listen='test', script='")
        assert result.endswith("..., disabled=False)")
        assert len(result) < len(
            f"Event(listen='test', script='{long_script}', disabled=False)"
        )

    def test_repr_none_script(self):
        """Test string representation with None script."""
        event = Event(listen="test")
        expected = "Event(listen='test', script=None, disabled=False)"
        assert repr(event) == expected

    def test_equality_same_objects(self):
        """Test equality between identical Event objects."""
        script = "console.log('test');"
        event1 = Event(listen="test", script=script, disabled=True)
        event2 = Event(listen="test", script=script, disabled=True)
        assert event1 == event2

    def test_equality_different_listen(self):
        """Test inequality with different listen types."""
        event1 = Event(listen="test", script="script")
        event2 = Event(listen="prerequest", script="script")
        assert event1 != event2

    def test_equality_different_script(self):
        """Test inequality with different scripts."""
        event1 = Event(listen="test", script="script1")
        event2 = Event(listen="test", script="script2")
        assert event1 != event2

    def test_equality_different_disabled(self):
        """Test inequality with different disabled flags."""
        event1 = Event(listen="test", script="script", disabled=True)
        event2 = Event(listen="test", script="script", disabled=False)
        assert event1 != event2

    def test_equality_different_types(self):
        """Test inequality with different object types."""
        event = Event(listen="test")
        assert event != "not an Event object"


class TestEventType:
    """Test cases for EventType enum."""

    def test_enum_values(self):
        """Test EventType enum values."""
        assert EventType.PREREQUEST.value == "prerequest"
        assert EventType.TEST.value == "test"

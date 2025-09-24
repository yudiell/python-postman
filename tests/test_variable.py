"""Unit tests for Variable model."""

import pytest
from python_postman.models.variable import Variable, VariableType, VariableScope


class TestVariable:
    """Test cases for Variable class."""

    def test_init_minimal(self):
        """Test Variable initialization with minimal parameters."""
        var = Variable(key="test_key")
        assert var.key == "test_key"
        assert var.value is None
        assert var.type is None
        assert var.description is None
        assert var.disabled is False
        assert var.scope is None

    def test_init_complete(self):
        """Test Variable initialization with all parameters."""
        var = Variable(
            key="test_key",
            value="test_value",
            type="string",
            description="Test variable",
            disabled=True,
        )
        assert var.key == "test_key"
        assert var.value == "test_value"
        assert var.type == "string"
        assert var.description == "Test variable"
        assert var.disabled is True

    def test_scope_property(self):
        """Test scope property getter and setter."""
        var = Variable(key="test")
        assert var.scope is None

        var.set_scope(VariableScope.COLLECTION)
        assert var.scope == VariableScope.COLLECTION

        var.set_scope(VariableScope.FOLDER)
        assert var.scope == VariableScope.FOLDER

    def test_resolve_value_simple(self):
        """Test simple value resolution without context."""
        var = Variable(key="test", value="simple_value")
        assert var.resolve_value() == "simple_value"

    def test_resolve_value_disabled(self):
        """Test value resolution for disabled variable."""
        var = Variable(key="test", value="value", disabled=True)
        assert var.resolve_value() is None

    def test_resolve_value_none(self):
        """Test value resolution for None value."""
        var = Variable(key="test", value=None)
        assert var.resolve_value() is None

    def test_resolve_value_with_context(self):
        """Test value resolution with variable substitution."""
        var = Variable(key="greeting", value="Hello {{name}}!")
        context = {"name": "World", "greeting": "Hello {{name}}!"}
        result = var.resolve_value(context)
        assert result == "Hello World!"

    def test_resolve_value_multiple_substitutions(self):
        """Test value resolution with multiple variable substitutions."""
        var = Variable(key="message", value="{{greeting}} {{name}} from {{location}}")
        context = {
            "greeting": "Hello",
            "name": "John",
            "location": "NYC",
            "message": "{{greeting}} {{name}} from {{location}}",
        }
        result = var.resolve_value(context)
        assert result == "Hello John from NYC"

    def test_resolve_value_no_self_reference(self):
        """Test that variable doesn't resolve itself to avoid infinite loops."""
        var = Variable(key="test", value="{{test}} suffix")
        context = {"test": "{{test}} suffix"}
        result = var.resolve_value(context)
        assert result == "{{test}} suffix"  # Should not substitute itself

    def test_get_type_explicit(self):
        """Test getting explicitly set variable type."""
        var = Variable(key="test", type="string")
        assert var.get_type() == VariableType.STRING

        var = Variable(key="test", type="BOOLEAN")
        assert var.get_type() == VariableType.BOOLEAN

    def test_get_type_inferred_string(self):
        """Test type inference for string values."""
        var = Variable(key="test", value="string_value")
        assert var.get_type() == VariableType.STRING

    def test_get_type_inferred_boolean(self):
        """Test type inference for boolean values."""
        var = Variable(key="test", value=True)
        assert var.get_type() == VariableType.BOOLEAN

        var = Variable(key="test", value=False)
        assert var.get_type() == VariableType.BOOLEAN

    def test_get_type_inferred_number(self):
        """Test type inference for numeric values."""
        var = Variable(key="test", value=42)
        assert var.get_type() == VariableType.NUMBER

        var = Variable(key="test", value=3.14)
        assert var.get_type() == VariableType.NUMBER

    def test_get_type_inferred_any(self):
        """Test type inference for complex values."""
        var = Variable(key="test", value=None)
        assert var.get_type() == VariableType.ANY

        var = Variable(key="test", value={"key": "value"})
        assert var.get_type() == VariableType.ANY

    def test_get_type_invalid_explicit(self):
        """Test handling of invalid explicit type."""
        var = Variable(key="test", type="invalid_type")
        assert var.get_type() == VariableType.ANY  # Falls back to inference

    def test_validate_success(self):
        """Test successful validation."""
        var = Variable(key="valid_key", value="value")
        assert var.validate() is True

    def test_validate_empty_key_fails(self):
        """Test validation fails with empty key."""
        var = Variable(key="")
        with pytest.raises(ValueError, match="Variable key is required"):
            var.validate()

    def test_validate_none_key_fails(self):
        """Test validation fails with None key."""
        var = Variable(key=None)
        with pytest.raises(ValueError, match="Variable key is required"):
            var.validate()

    def test_validate_whitespace_key_fails(self):
        """Test validation fails with whitespace-only key."""
        var = Variable(key="   ")
        with pytest.raises(ValueError, match="Variable key is required"):
            var.validate()

    def test_validate_non_string_key_fails(self):
        """Test validation fails with non-string key."""
        var = Variable(key=123)
        with pytest.raises(ValueError, match="Variable key is required"):
            var.validate()

    def test_validate_non_string_type_fails(self):
        """Test validation fails with non-string type."""
        var = Variable(key="test", type=123)
        with pytest.raises(ValueError, match="Variable type must be a string"):
            var.validate()

    def test_validate_non_string_description_fails(self):
        """Test validation fails with non-string description."""
        var = Variable(key="test", description=123)
        with pytest.raises(ValueError, match="Variable description must be a string"):
            var.validate()

    def test_validate_non_boolean_disabled_fails(self):
        """Test validation fails with non-boolean disabled flag."""
        var = Variable(key="test", disabled="true")
        with pytest.raises(
            ValueError, match="Variable disabled flag must be a boolean"
        ):
            var.validate()

    def test_from_dict_minimal(self):
        """Test creating Variable from minimal dictionary."""
        data = {"key": "test_key"}
        var = Variable.from_dict(data)
        assert var.key == "test_key"
        assert var.value is None
        assert var.type is None
        assert var.description is None
        assert var.disabled is False

    def test_from_dict_complete(self):
        """Test creating Variable from complete dictionary."""
        data = {
            "key": "test_key",
            "value": "test_value",
            "type": "string",
            "description": "Test variable",
            "disabled": True,
        }
        var = Variable.from_dict(data)
        assert var.key == "test_key"
        assert var.value == "test_value"
        assert var.type == "string"
        assert var.description == "Test variable"
        assert var.disabled is True

    def test_from_dict_missing_key(self):
        """Test creating Variable from dictionary without key."""
        data = {"value": "test_value"}
        var = Variable.from_dict(data)
        assert var.key is None
        assert var.value == "test_value"

    def test_to_dict_minimal(self):
        """Test converting Variable to dictionary with minimal data."""
        var = Variable(key="test_key")
        result = var.to_dict()
        expected = {"key": "test_key", "disabled": False}
        assert result == expected

    def test_to_dict_complete(self):
        """Test converting Variable to dictionary with complete data."""
        var = Variable(
            key="test_key",
            value="test_value",
            type="string",
            description="Test variable",
            disabled=True,
        )
        result = var.to_dict()
        expected = {
            "key": "test_key",
            "value": "test_value",
            "type": "string",
            "description": "Test variable",
            "disabled": True,
        }
        assert result == expected

    def test_repr(self):
        """Test string representation."""
        var = Variable(key="test", value="value", type="string", disabled=False)
        expected = "Variable(key='test', value='value', type='string', disabled=False)"
        assert repr(var) == expected

    def test_equality_same_objects(self):
        """Test equality between identical Variable objects."""
        var1 = Variable(key="test", value="value", type="string", description="desc")
        var2 = Variable(key="test", value="value", type="string", description="desc")
        assert var1 == var2

    def test_equality_different_objects(self):
        """Test inequality between different Variable objects."""
        var1 = Variable(key="test1", value="value")
        var2 = Variable(key="test2", value="value")
        assert var1 != var2

    def test_equality_different_types(self):
        """Test inequality with different object types."""
        var = Variable(key="test")
        assert var != "not a Variable object"


class TestVariableType:
    """Test cases for VariableType enum."""

    def test_enum_values(self):
        """Test VariableType enum values."""
        assert VariableType.STRING.value == "string"
        assert VariableType.BOOLEAN.value == "boolean"
        assert VariableType.NUMBER.value == "number"
        assert VariableType.ANY.value == "any"


class TestVariableScope:
    """Test cases for VariableScope enum."""

    def test_enum_values(self):
        """Test VariableScope enum values."""
        assert VariableScope.COLLECTION.value == "collection"
        assert VariableScope.FOLDER.value == "folder"
        assert VariableScope.REQUEST.value == "request"

"""Tests for ExecutionContext variable management."""

import pytest
from python_postman.execution.context import ExecutionContext
from python_postman.execution.exceptions import VariableResolutionError


class TestExecutionContext:
    """Test ExecutionContext variable management functionality."""

    def test_init_empty_context(self):
        """Test creating empty execution context."""
        context = ExecutionContext()

        assert context.environment_variables == {}
        assert context.collection_variables == {}
        assert context.folder_variables == {}
        assert context.request_variables == {}

    def test_init_with_variables(self):
        """Test creating context with initial variables."""
        env_vars = {"env_var": "env_value"}
        collection_vars = {"collection_var": "collection_value"}
        folder_vars = {"folder_var": "folder_value"}
        request_vars = {"request_var": "request_value"}

        context = ExecutionContext(
            environment_variables=env_vars,
            collection_variables=collection_vars,
            folder_variables=folder_vars,
            request_variables=request_vars,
        )

        assert context.environment_variables == env_vars
        assert context.collection_variables == collection_vars
        assert context.folder_variables == folder_vars
        assert context.request_variables == request_vars

    def test_get_variable_precedence(self):
        """Test variable precedence: request > folder > collection > environment."""
        context = ExecutionContext(
            environment_variables={"var": "env_value"},
            collection_variables={"var": "collection_value"},
            folder_variables={"var": "folder_value"},
            request_variables={"var": "request_value"},
        )

        # Request scope should have highest precedence
        assert context.get_variable("var") == "request_value"

    def test_get_variable_fallback_chain(self):
        """Test variable fallback through scopes."""
        context = ExecutionContext(
            environment_variables={"env_only": "env_value"},
            collection_variables={"collection_only": "collection_value"},
            folder_variables={"folder_only": "folder_value"},
            request_variables={"request_only": "request_value"},
        )

        assert context.get_variable("request_only") == "request_value"
        assert context.get_variable("folder_only") == "folder_value"
        assert context.get_variable("collection_only") == "collection_value"
        assert context.get_variable("env_only") == "env_value"
        assert context.get_variable("nonexistent") is None

    def test_set_variable_different_scopes(self):
        """Test setting variables in different scopes."""
        context = ExecutionContext()

        context.set_variable("test_var", "request_value", "request")
        context.set_variable("test_var", "folder_value", "folder")
        context.set_variable("test_var", "collection_value", "collection")
        context.set_variable("test_var", "env_value", "environment")

        # Request scope should win
        assert context.get_variable("test_var") == "request_value"

        # Check individual scopes
        assert context.request_variables["test_var"] == "request_value"
        assert context.folder_variables["test_var"] == "folder_value"
        assert context.collection_variables["test_var"] == "collection_value"
        assert context.environment_variables["test_var"] == "env_value"

    def test_set_variable_invalid_scope(self):
        """Test setting variable with invalid scope raises error."""
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Invalid scope: invalid"):
            context.set_variable("test_var", "value", "invalid")

    def test_resolve_variables_simple(self):
        """Test simple variable resolution."""
        context = ExecutionContext(collection_variables={"name": "John", "age": "30"})

        result = context.resolve_variables("Hello {{name}}, you are {{age}} years old")
        assert result == "Hello John, you are 30 years old"

    def test_resolve_variables_nested(self):
        """Test nested variable resolution."""
        context = ExecutionContext(
            collection_variables={
                "base_url": "https://api.example.com",
                "version": "v1",
                "endpoint": "{{base_url}}/{{version}}/users",
            }
        )

        result = context.resolve_variables("{{endpoint}}")
        assert result == "https://api.example.com/v1/users"

    def test_resolve_variables_missing_variable(self):
        """Test resolution fails for missing variables."""
        context = ExecutionContext()

        with pytest.raises(
            VariableResolutionError, match="Variable 'missing' not found"
        ):
            context.resolve_variables("Hello {{missing}}")

    def test_resolve_variables_circular_reference(self):
        """Test circular reference detection."""
        context = ExecutionContext(
            collection_variables={"var1": "{{var2}}", "var2": "{{var1}}"}
        )

        with pytest.raises(VariableResolutionError, match="Maximum recursion depth"):
            context.resolve_variables("{{var1}}")

    def test_resolve_variables_max_depth(self):
        """Test custom max depth for recursion."""
        context = ExecutionContext(
            collection_variables={
                "var1": "{{var2}}",
                "var2": "{{var3}}",
                "var3": "final_value",
            }
        )

        # Should work with sufficient depth
        result = context.resolve_variables("{{var1}}", max_depth=5)
        assert result == "final_value"

        # Should fail with insufficient depth
        with pytest.raises(VariableResolutionError):
            context.resolve_variables("{{var1}}", max_depth=1)

    def test_resolve_variables_no_variables(self):
        """Test resolving text with no variables."""
        context = ExecutionContext()

        result = context.resolve_variables("Plain text with no variables")
        assert result == "Plain text with no variables"

    def test_resolve_variables_non_string_input(self):
        """Test resolving non-string input."""
        context = ExecutionContext()

        result = context.resolve_variables(123)
        assert result == "123"

    def test_resolve_variables_whitespace_in_variable_names(self):
        """Test variable names with whitespace are handled correctly."""
        context = ExecutionContext(collection_variables={"var with spaces": "value"})

        result = context.resolve_variables("{{ var with spaces }}")
        assert result == "value"

    def test_create_child_context(self):
        """Test creating child context."""
        parent = ExecutionContext(
            environment_variables={"env_var": "env_value"},
            collection_variables={"collection_var": "collection_value"},
            folder_variables={"folder_var": "folder_value"},
        )

        child = parent.create_child_context({"request_var": "request_value"})

        # Child should have all parent variables
        assert child.get_variable("env_var") == "env_value"
        assert child.get_variable("collection_var") == "collection_value"
        assert child.get_variable("folder_var") == "folder_value"
        assert child.get_variable("request_var") == "request_value"

        # Modifying child shouldn't affect parent
        child.set_variable("new_var", "new_value", "collection")
        assert parent.get_variable("new_var") is None
        assert child.get_variable("new_var") == "new_value"

    def test_has_variable(self):
        """Test checking if variable exists."""
        context = ExecutionContext(collection_variables={"existing_var": "value"})

        assert context.has_variable("existing_var") is True
        assert context.has_variable("nonexistent_var") is False

    def test_get_all_variables(self):
        """Test getting all variables with proper precedence."""
        context = ExecutionContext(
            environment_variables={"var1": "env", "var2": "env"},
            collection_variables={"var2": "collection", "var3": "collection"},
            folder_variables={"var3": "folder", "var4": "folder"},
            request_variables={"var4": "request", "var5": "request"},
        )

        all_vars = context.get_all_variables()

        # Check precedence is maintained
        assert all_vars["var1"] == "env"  # Only in environment
        assert all_vars["var2"] == "collection"  # Collection overrides environment
        assert all_vars["var3"] == "folder"  # Folder overrides collection
        assert all_vars["var4"] == "request"  # Request overrides folder
        assert all_vars["var5"] == "request"  # Only in request

        assert len(all_vars) == 5

    def test_clear_scope(self):
        """Test clearing variables in specific scope."""
        context = ExecutionContext(
            environment_variables={"env_var": "env_value"},
            collection_variables={"collection_var": "collection_value"},
            folder_variables={"folder_var": "folder_value"},
            request_variables={"request_var": "request_value"},
        )

        # Clear collection scope
        context.clear_scope("collection")

        assert context.get_variable("env_var") == "env_value"
        assert context.get_variable("collection_var") is None
        assert context.get_variable("folder_var") == "folder_value"
        assert context.get_variable("request_var") == "request_value"

    def test_clear_scope_invalid(self):
        """Test clearing invalid scope raises error."""
        context = ExecutionContext()

        with pytest.raises(ValueError, match="Invalid scope: invalid"):
            context.clear_scope("invalid")

    def test_repr(self):
        """Test string representation."""
        context = ExecutionContext(
            environment_variables={"var1": "value1"},
            collection_variables={"var2": "value2", "var3": "value3"},
        )

        repr_str = repr(context)
        assert "ExecutionContext" in repr_str
        assert "total_variables=3" in repr_str

    def test_variable_resolution_with_different_types(self):
        """Test variable resolution with different value types."""
        context = ExecutionContext(
            collection_variables={
                "string_var": "hello",
                "int_var": 42,
                "float_var": 3.14,
                "bool_var": True,
                "none_var": None,
            }
        )

        assert context.resolve_variables("{{string_var}}") == "hello"
        assert context.resolve_variables("{{int_var}}") == "42"
        assert context.resolve_variables("{{float_var}}") == "3.14"
        assert context.resolve_variables("{{bool_var}}") == "True"
        assert context.resolve_variables("{{none_var}}") == "None"

    def test_multiple_variables_in_single_string(self):
        """Test resolving multiple variables in a single string."""
        context = ExecutionContext(
            collection_variables={
                "protocol": "https",
                "host": "api.example.com",
                "port": "443",
                "path": "/v1/users",
            }
        )

        result = context.resolve_variables("{{protocol}}://{{host}}:{{port}}{{path}}")
        assert result == "https://api.example.com:443/v1/users"

    def test_partial_variable_matches(self):
        """Test that partial variable patterns are not resolved."""
        context = ExecutionContext(collection_variables={"var": "value"})

        # These should not be resolved as they're not complete variable patterns
        assert context.resolve_variables("{var}") == "{var}"
        assert context.resolve_variables("{{var") == "{{var"
        assert context.resolve_variables("var}}") == "var}}"
        assert context.resolve_variables("{{{var}}}") == "{value}"

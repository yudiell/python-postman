"""Tests for Body model."""

import pytest
import json
from python_postman.models.body import Body, FormParameter, BodyMode


class TestFormParameter:
    """Test FormParameter class."""

    def test_init_basic(self):
        """Test basic FormParameter initialization."""
        param = FormParameter(key="username", value="john")
        assert param.key == "username"
        assert param.value == "john"
        assert param.description is None
        assert param.disabled is False
        assert param.type == "text"
        assert param.src is None

    def test_init_full(self):
        """Test FormParameter initialization with all parameters."""
        param = FormParameter(
            key="avatar",
            value="file.jpg",
            description="User avatar",
            disabled=True,
            type="file",
            src="/path/to/file.jpg",
        )
        assert param.key == "avatar"
        assert param.value == "file.jpg"
        assert param.description == "User avatar"
        assert param.disabled is True
        assert param.type == "file"
        assert param.src == "/path/to/file.jpg"

    def test_is_file_true(self):
        """Test is_file for file type parameter."""
        param = FormParameter(key="upload", type="file")
        assert param.is_file() is True

    def test_is_file_false(self):
        """Test is_file for text type parameter."""
        param = FormParameter(key="username", type="text")
        assert param.is_file() is False

    def test_is_active_enabled(self):
        """Test is_active for enabled parameter."""
        param = FormParameter(key="username", value="john")
        assert param.is_active() is True

    def test_is_active_disabled(self):
        """Test is_active for disabled parameter."""
        param = FormParameter(key="username", value="john", disabled=True)
        assert param.is_active() is False

    def test_is_active_empty_key(self):
        """Test is_active for parameter with empty key."""
        param = FormParameter(key="", value="john")
        assert param.is_active() is False

    def test_get_effective_value_basic(self):
        """Test getting effective value without variables."""
        param = FormParameter(key="username", value="john")
        assert param.get_effective_value() == "john"

    def test_get_effective_value_disabled(self):
        """Test getting effective value for disabled parameter."""
        param = FormParameter(key="username", value="john", disabled=True)
        assert param.get_effective_value() is None

    def test_get_effective_value_empty(self):
        """Test getting effective value for parameter with no value."""
        param = FormParameter(key="username")
        assert param.get_effective_value() is None

    def test_get_effective_value_with_variables(self):
        """Test getting effective value with variable resolution."""
        param = FormParameter(key="token", value="Bearer {{apiKey}}")
        variables = {"apiKey": "secret123"}

        result = param.get_effective_value(variables)
        assert result == "Bearer secret123"

    def test_validate_success(self):
        """Test successful form parameter validation."""
        param = FormParameter(key="username", value="john")
        assert param.validate() is True

    def test_validate_failure_empty_key(self):
        """Test validation failure with empty key."""
        param = FormParameter(key="")
        with pytest.raises(ValueError, match="Form parameter key is required"):
            param.validate()

    def test_validate_failure_invalid_value_type(self):
        """Test validation failure with invalid value type."""
        param = FormParameter(key="username", value=123)
        with pytest.raises(ValueError, match="Form parameter value must be a string"):
            param.validate()

    def test_validate_failure_invalid_type(self):
        """Test validation failure with invalid type."""
        param = FormParameter(key="username", type="invalid")
        with pytest.raises(
            ValueError, match="Form parameter type must be 'text' or 'file'"
        ):
            param.validate()

    def test_from_dict_basic(self):
        """Test creating FormParameter from dictionary."""
        data = {
            "key": "username",
            "value": "john",
            "description": "User name",
            "disabled": False,
            "type": "text",
        }

        param = FormParameter.from_dict(data)
        assert param.key == "username"
        assert param.value == "john"
        assert param.description == "User name"
        assert param.disabled is False
        assert param.type == "text"

    def test_to_dict_full(self):
        """Test converting FormParameter to dictionary."""
        param = FormParameter(
            key="avatar",
            value="file.jpg",
            description="User avatar",
            disabled=True,
            type="file",
            src="/path/to/file.jpg",
        )

        result = param.to_dict()
        expected = {
            "key": "avatar",
            "value": "file.jpg",
            "description": "User avatar",
            "disabled": True,
            "type": "file",
            "src": "/path/to/file.jpg",
        }
        assert result == expected

    def test_equality(self):
        """Test FormParameter equality."""
        param1 = FormParameter(key="username", value="john")
        param2 = FormParameter(key="username", value="john")
        param3 = FormParameter(key="username", value="jane")

        assert param1 == param2
        assert param1 != param3
        assert param1 != "not a param"

    def test_repr(self):
        """Test FormParameter repr."""
        param = FormParameter(key="username", value="john")
        result = repr(param)
        assert "FormParameter" in result
        assert "username" in result


class TestBody:
    """Test Body class."""

    def test_init_empty(self):
        """Test empty Body initialization."""
        body = Body()
        assert body.mode is None
        assert body.raw is None
        assert body.urlencoded == []
        assert body.formdata == []
        assert body.file == {}
        assert body.disabled is False
        assert body.options == {}

    def test_init_raw_body(self):
        """Test Body initialization with raw content."""
        body = Body(
            mode="raw", raw='{"name": "test"}', options={"raw": {"language": "json"}}
        )
        assert body.mode == "raw"
        assert body.raw == '{"name": "test"}'
        assert body.options["raw"]["language"] == "json"

    def test_init_form_body(self):
        """Test Body initialization with form data."""
        params = [
            FormParameter("username", "john"),
            FormParameter("password", "secret"),
        ]
        body = Body(mode="formdata", formdata=params)

        assert body.mode == "formdata"
        assert len(body.formdata) == 2
        assert body.formdata[0].key == "username"

    def test_get_mode_valid(self):
        """Test getting valid body mode."""
        body = Body(mode="raw")
        assert body.get_mode() == BodyMode.RAW

    def test_get_mode_invalid(self):
        """Test getting invalid body mode."""
        body = Body(mode="invalid")
        assert body.get_mode() is None

    def test_get_mode_none(self):
        """Test getting mode when none set."""
        body = Body()
        assert body.get_mode() is None

    def test_is_active_raw_with_content(self):
        """Test is_active for raw body with content."""
        body = Body(mode="raw", raw="test content")
        assert body.is_active() is True

    def test_is_active_raw_empty(self):
        """Test is_active for raw body without content."""
        body = Body(mode="raw")
        assert body.is_active() is False

    def test_is_active_disabled(self):
        """Test is_active for disabled body."""
        body = Body(mode="raw", raw="test", disabled=True)
        assert body.is_active() is False

    def test_is_active_formdata_with_params(self):
        """Test is_active for formdata with active parameters."""
        params = [FormParameter("key", "value")]
        body = Body(mode="formdata", formdata=params)
        assert body.is_active() is True

    def test_is_active_formdata_disabled_params(self):
        """Test is_active for formdata with only disabled parameters."""
        params = [FormParameter("key", "value", disabled=True)]
        body = Body(mode="formdata", formdata=params)
        assert body.is_active() is False

    def test_get_content_type_raw_json(self):
        """Test content type for raw JSON body."""
        body = Body(mode="raw", options={"raw": {"language": "json"}})
        assert body.get_content_type() == "application/json"

    def test_get_content_type_raw_xml(self):
        """Test content type for raw XML body."""
        body = Body(mode="raw", options={"raw": {"language": "xml"}})
        assert body.get_content_type() == "application/xml"

    def test_get_content_type_urlencoded(self):
        """Test content type for urlencoded body."""
        body = Body(mode="urlencoded")
        assert body.get_content_type() == "application/x-www-form-urlencoded"

    def test_get_content_type_formdata(self):
        """Test content type for formdata body."""
        body = Body(mode="formdata")
        assert body.get_content_type() == "multipart/form-data"

    def test_get_content_type_graphql(self):
        """Test content type for GraphQL body."""
        body = Body(mode="graphql")
        assert body.get_content_type() == "application/json"

    def test_get_content_raw(self):
        """Test getting raw content."""
        body = Body(mode="raw", raw="test content")
        assert body.get_content() == "test content"

    def test_get_content_raw_with_variables(self):
        """Test getting raw content with variable resolution."""
        body = Body(mode="raw", raw="Hello {{name}}")
        variables = {"name": "World"}

        result = body.get_content(variables)
        assert result == "Hello World"

    def test_get_content_urlencoded(self):
        """Test getting urlencoded content."""
        params = [
            FormParameter("username", "john"),
            FormParameter("password", "secret"),
            FormParameter("disabled", "value", disabled=True),
        ]
        body = Body(mode="urlencoded", urlencoded=params)

        result = body.get_content()
        expected = {"username": "john", "password": "secret"}
        assert result == expected

    def test_get_content_formdata(self):
        """Test getting formdata content."""
        params = [
            FormParameter("username", "john", type="text"),
            FormParameter("avatar", "file.jpg", type="file"),
            FormParameter("disabled", "value", disabled=True),
        ]
        body = Body(mode="formdata", formdata=params)

        result = body.get_content()
        expected = [("username", "john", "text"), ("avatar", "file.jpg", "file")]
        assert result == expected

    def test_get_content_graphql_valid_json(self):
        """Test getting GraphQL content with valid JSON."""
        graphql_query = '{"query": "{ user { name } }", "variables": {}}'
        body = Body(mode="graphql", raw=graphql_query)

        result = body.get_content()
        expected = {"query": "{ user { name } }", "variables": {}}
        assert result == expected

    def test_get_content_graphql_invalid_json(self):
        """Test getting GraphQL content with invalid JSON."""
        body = Body(mode="graphql", raw="{ user { name } }")

        result = body.get_content()
        assert result == "{ user { name } }"

    def test_get_content_file(self):
        """Test getting file content."""
        body = Body(mode="file", file={"src": "/path/to/file.txt"})

        result = body.get_content()
        assert result == "/path/to/file.txt"

    def test_get_content_disabled(self):
        """Test getting content for disabled body."""
        body = Body(mode="raw", raw="test", disabled=True)
        assert body.get_content() is None

    def test_add_form_parameter_formdata(self):
        """Test adding form parameter to formdata body."""
        body = Body(mode="formdata")
        param = body.add_form_parameter("username", "john")

        assert len(body.formdata) == 1
        assert param.key == "username"
        assert param.value == "john"

    def test_add_form_parameter_urlencoded(self):
        """Test adding form parameter to urlencoded body."""
        body = Body(mode="urlencoded")
        param = body.add_form_parameter("username", "john")

        assert len(body.urlencoded) == 1
        assert param.key == "username"
        assert param.value == "john"

    def test_add_form_parameter_no_mode(self):
        """Test adding form parameter when no mode is set."""
        body = Body()
        param = body.add_form_parameter("username", "john")

        assert body.mode == "formdata"
        assert len(body.formdata) == 1
        assert param.key == "username"

    def test_remove_form_parameter_formdata(self):
        """Test removing form parameter from formdata."""
        params = [FormParameter("keep", "value"), FormParameter("remove", "value")]
        body = Body(mode="formdata", formdata=params)

        result = body.remove_form_parameter("remove")
        assert result is True
        assert len(body.formdata) == 1
        assert body.formdata[0].key == "keep"

    def test_remove_form_parameter_not_found(self):
        """Test removing non-existent form parameter."""
        body = Body(mode="formdata", formdata=[FormParameter("keep", "value")])

        result = body.remove_form_parameter("missing")
        assert result is False
        assert len(body.formdata) == 1

    def test_get_form_parameter_found(self):
        """Test getting existing form parameter."""
        param = FormParameter("username", "john")
        body = Body(mode="formdata", formdata=[param])

        found = body.get_form_parameter("username")
        assert found == param

    def test_get_form_parameter_not_found(self):
        """Test getting non-existent form parameter."""
        body = Body(mode="formdata", formdata=[FormParameter("username", "john")])

        found = body.get_form_parameter("missing")
        assert found is None

    def test_validate_success(self):
        """Test successful body validation."""
        body = Body(mode="raw", raw="test content")
        assert body.validate() is True

    def test_validate_failure_invalid_mode_type(self):
        """Test validation failure with invalid mode type."""
        body = Body(mode=123)
        with pytest.raises(ValueError, match="Body mode must be a string"):
            body.validate()

    def test_validate_failure_invalid_raw_type(self):
        """Test validation failure with invalid raw type."""
        body = Body(raw=123)
        with pytest.raises(ValueError, match="Body raw content must be a string"):
            body.validate()

    def test_validate_failure_invalid_disabled_type(self):
        """Test validation failure with invalid disabled type."""
        body = Body(disabled="false")
        with pytest.raises(ValueError, match="Body disabled flag must be a boolean"):
            body.validate()

    def test_validate_failure_invalid_options_type(self):
        """Test validation failure with invalid options type."""
        body = Body(options="not a dict")
        with pytest.raises(ValueError, match="Body options must be a dictionary"):
            body.validate()

    def test_validate_failure_invalid_form_param(self):
        """Test validation failure with invalid form parameter."""
        body = Body(mode="formdata", formdata=["not a FormParameter"])
        with pytest.raises(
            ValueError, match="All formdata items must be FormParameter instances"
        ):
            body.validate()

    def test_from_dict_raw(self):
        """Test creating Body from dictionary with raw content."""
        data = {
            "mode": "raw",
            "raw": "test content",
            "options": {"raw": {"language": "json"}},
            "disabled": False,
        }

        body = Body.from_dict(data)
        assert body.mode == "raw"
        assert body.raw == "test content"
        assert body.options["raw"]["language"] == "json"
        assert body.disabled is False

    def test_from_dict_formdata(self):
        """Test creating Body from dictionary with formdata."""
        data = {
            "mode": "formdata",
            "formdata": [
                {"key": "username", "value": "john", "type": "text"},
                {"key": "avatar", "type": "file", "src": "/path/file.jpg"},
            ],
        }

        body = Body.from_dict(data)
        assert body.mode == "formdata"
        assert len(body.formdata) == 2
        assert body.formdata[0].key == "username"
        assert body.formdata[1].type == "file"

    def test_to_dict_raw(self):
        """Test converting raw Body to dictionary."""
        body = Body(
            mode="raw",
            raw="test content",
            options={"raw": {"language": "json"}},
            disabled=False,
        )

        result = body.to_dict()
        expected = {
            "mode": "raw",
            "raw": "test content",
            "options": {"raw": {"language": "json"}},
            "disabled": False,
        }
        assert result == expected

    def test_to_dict_formdata(self):
        """Test converting formdata Body to dictionary."""
        params = [FormParameter("username", "john")]
        body = Body(mode="formdata", formdata=params)

        result = body.to_dict()
        assert result["mode"] == "formdata"
        assert len(result["formdata"]) == 1
        assert result["formdata"][0]["key"] == "username"

    def test_equality(self):
        """Test Body equality."""
        body1 = Body(mode="raw", raw="test")
        body2 = Body(mode="raw", raw="test")
        body3 = Body(mode="raw", raw="different")

        assert body1 == body2
        assert body1 != body3
        assert body1 != "not a body"

    def test_repr(self):
        """Test Body repr."""
        body = Body(mode="raw", disabled=False)
        result = repr(body)
        assert "Body" in result
        assert "raw" in result
        assert "False" in result

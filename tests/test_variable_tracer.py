"""Tests for variable scope introspection and tracing."""

import pytest
from python_postman.models import (
    Collection,
    CollectionInfo,
    Variable,
    VariableScope,
    Request,
    Folder,
    Url,
    Header,
    Body,
    Auth,
    AuthParameter,
    Event,
)
from python_postman.introspection import VariableTracer, VariableReference
from python_postman.execution.context import ExecutionContext


class TestVariableReference:
    """Tests for VariableReference class."""

    def test_variable_reference_creation(self):
        """Test creating a VariableReference."""
        ref = VariableReference(
            variable_name="api_key",
            scope=VariableScope.COLLECTION,
            value="secret123",
            location="collection 'My Collection'",
        )

        assert ref.variable_name == "api_key"
        assert ref.scope == VariableScope.COLLECTION
        assert ref.value == "secret123"
        assert ref.location == "collection 'My Collection'"

    def test_variable_reference_repr(self):
        """Test string representation of VariableReference."""
        ref = VariableReference(
            variable_name="base_url",
            scope=VariableScope.FOLDER,
            value="https://api.example.com",
            location="folder 'API Tests'",
        )

        repr_str = repr(ref)
        assert "base_url" in repr_str
        assert "folder" in repr_str
        assert "https://api.example.com" in repr_str

    def test_variable_reference_equality(self):
        """Test equality comparison of VariableReference objects."""
        ref1 = VariableReference("var1", VariableScope.COLLECTION, "value1", "loc1")
        ref2 = VariableReference("var1", VariableScope.COLLECTION, "value1", "loc1")
        ref3 = VariableReference("var2", VariableScope.COLLECTION, "value1", "loc1")

        assert ref1 == ref2
        assert ref1 != ref3
        assert ref1 != "not a reference"


class TestVariableTracer:
    """Tests for VariableTracer class."""

    def test_tracer_initialization(self):
        """Test creating a VariableTracer."""
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            )
        )

        tracer = VariableTracer(collection)
        assert tracer.collection == collection

    def test_trace_variable_in_collection(self):
        """Test tracing a variable defined at collection level."""
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            variables=[
                Variable(key="api_key", value="collection_key"),
                Variable(key="base_url", value="https://api.example.com"),
            ],
        )

        tracer = VariableTracer(collection)
        references = tracer.trace_variable("api_key")

        assert len(references) == 1
        assert references[0].variable_name == "api_key"
        assert references[0].scope == VariableScope.COLLECTION
        assert references[0].value == "collection_key"
        assert "Test Collection" in references[0].location

    def test_trace_variable_with_context(self):
        """Test tracing a variable with execution context."""
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            variables=[Variable(key="api_key", value="collection_key")],
        )

        context = ExecutionContext(
            collection_variables={"api_key": "context_collection_key"},
            environment_variables={"api_key": "env_key"},
            request_variables={"api_key": "request_key"},
        )

        tracer = VariableTracer(collection)
        references = tracer.trace_variable("api_key", context)

        # Should find references in context (ordered by precedence)
        assert len(references) >= 3
        # Request scope should be first (highest precedence)
        assert references[0].scope == VariableScope.REQUEST
        assert references[0].value == "request_key"

    def test_trace_variable_not_found(self):
        """Test tracing a variable that doesn't exist."""
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            variables=[Variable(key="api_key", value="secret")],
        )

        tracer = VariableTracer(collection)
        references = tracer.trace_variable("nonexistent_var")

        assert len(references) == 0

    def test_find_shadowed_variables(self):
        """Test finding variables defined in multiple scopes."""
        # Create a folder with a variable that shadows a collection variable
        folder = Folder(
            name="API Tests",
            items=[],
            variables=[Variable(key="api_key", value="folder_key")],
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[folder],
            variables=[
                Variable(key="api_key", value="collection_key"),
                Variable(key="base_url", value="https://api.example.com"),
            ],
        )

        tracer = VariableTracer(collection)
        shadowed = tracer.find_shadowed_variables()

        # api_key should be shadowed (defined in both collection and folder)
        assert "api_key" in shadowed
        assert len(shadowed["api_key"]) == 2

        # base_url should not be shadowed (only in collection)
        assert "base_url" not in shadowed

    def test_find_shadowed_variables_nested_folders(self):
        """Test finding shadowed variables in nested folder structure."""
        inner_folder = Folder(
            name="Inner Folder",
            items=[],
            variables=[Variable(key="timeout", value="10")],
        )

        outer_folder = Folder(
            name="Outer Folder",
            items=[inner_folder],
            variables=[Variable(key="timeout", value="30")],
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[outer_folder],
            variables=[Variable(key="timeout", value="60")],
        )

        tracer = VariableTracer(collection)
        shadowed = tracer.find_shadowed_variables()

        # timeout should be defined in 3 places
        assert "timeout" in shadowed
        assert len(shadowed["timeout"]) == 3

    def test_find_undefined_references(self):
        """Test finding undefined variable references."""
        request = Request(
            name="Get User",
            method="GET",
            url=Url.from_string("{{base_url}}/users/{{user_id}}"),
            headers=[Header(key="Authorization", value="Bearer {{api_key}}")],
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[request],
            variables=[
                Variable(key="base_url", value="https://api.example.com"),
                # api_key and user_id are NOT defined
            ],
        )

        tracer = VariableTracer(collection)
        undefined = tracer.find_undefined_references()

        # Should find api_key and user_id as undefined
        assert "api_key" in undefined
        assert "user_id" in undefined
        assert "base_url" not in undefined

    def test_find_undefined_references_in_body(self):
        """Test finding undefined references in request body."""
        request = Request(
            name="Create User",
            method="POST",
            url=Url.from_string("https://api.example.com/users"),
            body=Body(mode="raw", raw='{"name": "{{user_name}}", "email": "{{user_email}}"}'),
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[request],
            variables=[Variable(key="user_name", value="John")],
        )

        tracer = VariableTracer(collection)
        undefined = tracer.find_undefined_references()

        # user_email is undefined, user_name is defined
        assert "user_email" in undefined
        assert "user_name" not in undefined

    def test_find_undefined_references_path_parameters(self):
        """Test finding undefined path parameter references."""
        request = Request(
            name="Get Dataset",
            method="GET",
            url=Url.from_string("https://api.example.com/:datasetId/data/:recordId"),
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[request],
            variables=[Variable(key="datasetId", value="abc123")],
        )

        tracer = VariableTracer(collection)
        undefined = tracer.find_undefined_references()

        # recordId is undefined, datasetId is defined
        assert "recordId" in undefined
        assert "datasetId" not in undefined

    def test_find_variable_usage(self):
        """Test finding all usage locations of a variable."""
        request1 = Request(
            name="Get User",
            method="GET",
            url=Url.from_string("{{base_url}}/users"),
            headers=[Header(key="Authorization", value="Bearer {{api_key}}")],
        )

        request2 = Request(
            name="Create User",
            method="POST",
            url=Url.from_string("{{base_url}}/users"),
            body=Body(mode="raw", raw='{"api_key": "{{api_key}}"}'),
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[request1, request2],
            variables=[
                Variable(key="base_url", value="https://api.example.com"),
                Variable(key="api_key", value="secret"),
            ],
        )

        tracer = VariableTracer(collection)

        # Find usage of base_url
        base_url_usage = tracer.find_variable_usage("base_url")
        assert len(base_url_usage) == 2  # Used in both request URLs
        assert any("Get User" in loc and "URL" in loc for loc in base_url_usage)
        assert any("Create User" in loc and "URL" in loc for loc in base_url_usage)

        # Find usage of api_key
        api_key_usage = tracer.find_variable_usage("api_key")
        assert len(api_key_usage) == 2  # Used in header and body
        assert any("Authorization" in loc for loc in api_key_usage)
        assert any("Body" in loc for loc in api_key_usage)

    def test_find_variable_usage_in_auth(self):
        """Test finding variable usage in authentication."""
        request = Request(
            name="Authenticated Request",
            method="GET",
            url=Url.from_string("https://api.example.com/data"),
            auth=Auth(
                type="bearer",
                parameters=[AuthParameter(key="token", value="{{auth_token}}")],
            ),
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[request],
            variables=[Variable(key="auth_token", value="secret_token")],
        )

        tracer = VariableTracer(collection)
        usage = tracer.find_variable_usage("auth_token")

        assert len(usage) == 1
        assert "Auth parameter" in usage[0]
        assert "token" in usage[0]

    def test_find_variable_usage_in_scripts(self):
        """Test finding variable usage in pre-request and test scripts."""
        request = Request(
            name="Request with Scripts",
            method="GET",
            url=Url.from_string("https://api.example.com/data"),
            events=[
                Event(
                    listen="prerequest",
                    script={
                        "type": "text/javascript",
                        "exec": [
                            'pm.environment.set("timestamp", Date.now());',
                            'const apiKey = pm.variables.get("{{api_key}}");',
                        ],
                    },
                ),
                Event(
                    listen="test",
                    script={
                        "type": "text/javascript",
                        "exec": [
                            'pm.test("Status is 200", function() {',
                            "  pm.response.to.have.status(200);",
                            '  const key = "{{api_key}}";',
                            "});",
                        ],
                    },
                ),
            ],
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[request],
            variables=[Variable(key="api_key", value="secret")],
        )

        tracer = VariableTracer(collection)
        usage = tracer.find_variable_usage("api_key")

        # Should find usage in both prerequest and test scripts
        assert len(usage) == 2
        assert any("prerequest script" in loc for loc in usage)
        assert any("test script" in loc for loc in usage)

    def test_find_variable_usage_not_used(self):
        """Test finding usage of a variable that is not used."""
        request = Request(
            name="Simple Request",
            method="GET",
            url=Url.from_string("https://api.example.com/data"),
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[request],
            variables=[Variable(key="unused_var", value="value")],
        )

        tracer = VariableTracer(collection)
        usage = tracer.find_variable_usage("unused_var")

        assert len(usage) == 0

    def test_extract_variable_names_postman_style(self):
        """Test extracting Postman-style variable names."""
        collection = Collection(
            info=CollectionInfo(
                name="Test",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            )
        )
        tracer = VariableTracer(collection)

        text = "{{base_url}}/api/{{version}}/users/{{user_id}}"
        variables = tracer._extract_variable_names(text)

        assert variables == {"base_url", "version", "user_id"}

    def test_extract_variable_names_path_parameters(self):
        """Test extracting path parameter variable names."""
        collection = Collection(
            info=CollectionInfo(
                name="Test",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            )
        )
        tracer = VariableTracer(collection)

        text = "https://api.example.com/:datasetId/records/:recordId"
        variables = tracer._extract_variable_names(text)

        assert variables == {"datasetId", "recordId"}

    def test_extract_variable_names_mixed(self):
        """Test extracting both Postman-style and path parameter variables."""
        collection = Collection(
            info=CollectionInfo(
                name="Test",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            )
        )
        tracer = VariableTracer(collection)

        text = "{{base_url}}/:datasetId/data?key={{api_key}}"
        variables = tracer._extract_variable_names(text)

        assert variables == {"base_url", "datasetId", "api_key"}

    def test_trace_variable_in_nested_folders(self):
        """Test tracing variables through nested folder structure."""
        inner_folder = Folder(
            name="Inner",
            items=[],
            variables=[Variable(key="level", value="inner")],
        )

        middle_folder = Folder(
            name="Middle",
            items=[inner_folder],
            variables=[Variable(key="level", value="middle")],
        )

        outer_folder = Folder(
            name="Outer",
            items=[middle_folder],
            variables=[Variable(key="level", value="outer")],
        )

        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            ),
            items=[outer_folder],
            variables=[Variable(key="level", value="collection")],
        )

        tracer = VariableTracer(collection)
        references = tracer.trace_variable("level")

        # Should find all 4 definitions
        assert len(references) == 4

        # Verify locations
        locations = [ref.location for ref in references]
        assert any("collection" in loc for loc in locations)
        assert any("Outer" in loc for loc in locations)
        assert any("Middle" in loc for loc in locations)
        assert any("Inner" in loc for loc in locations)

    def test_empty_collection(self):
        """Test tracer with empty collection."""
        collection = Collection(
            info=CollectionInfo(
                name="Empty Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            )
        )

        tracer = VariableTracer(collection)

        assert tracer.trace_variable("any_var") == []
        assert tracer.find_shadowed_variables() == {}
        assert tracer.find_undefined_references() == []
        assert tracer.find_variable_usage("any_var") == []

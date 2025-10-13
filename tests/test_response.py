"""
Tests for the Response and ExampleResponse classes.
"""

import pytest
from python_postman.models.response import Response, ExampleResponse
from python_postman.models.header import Header


class TestResponse:
    """Tests for the Response class."""

    def test_response_initialization_minimal(self):
        """Test Response initialization with minimal parameters."""
        response = Response(name="Success Response", status="OK", code=200)

        assert response.name == "Success Response"
        assert response.status == "OK"
        assert response.code == 200
        assert response.headers == []
        assert response.body is None
        assert response.cookie == []
        assert response._postman_previewlanguage is None
        assert response._time is None
        assert response.response_time is None

    def test_response_initialization_full(self):
        """Test Response initialization with all parameters."""
        headers = [
            Header("Content-Type", "application/json"),
            Header("Cache-Control", "no-cache"),
        ]
        body = '{"message": "Success", "data": {"id": 1}}'
        cookies = [{"name": "session", "value": "abc123"}]

        response = Response(
            name="Success Response",
            status="OK",
            code=200,
            headers=headers,
            body=body,
            cookie=cookies,
            _postman_previewlanguage="json",
            _time=150,
            response_time=150,
        )

        assert response.name == "Success Response"
        assert response.status == "OK"
        assert response.code == 200
        assert response.headers == headers
        assert response.body == body
        assert response.cookie == cookies
        assert response._postman_previewlanguage == "json"
        assert response._time == 150
        assert response.response_time == 150

    def test_response_from_dict_minimal(self):
        """Test Response.from_dict with minimal data."""
        data = {"name": "Test Response", "status": "OK", "code": 200}

        response = Response.from_dict(data)

        assert response.name == "Test Response"
        assert response.status == "OK"
        assert response.code == 200
        assert response.headers == []
        assert response.body is None

    def test_response_from_dict_full(self):
        """Test Response.from_dict with complete data."""
        data = {
            "name": "Success Response",
            "status": "OK",
            "code": 200,
            "header": [
                {"key": "Content-Type", "value": "application/json"},
                {"key": "Cache-Control", "value": "no-cache"},
            ],
            "body": '{"message": "Success"}',
            "cookie": [{"name": "session", "value": "abc123"}],
            "_postman_previewlanguage": "json",
            "_time": 150,
            "responseTime": 150,
        }

        response = Response.from_dict(data)

        assert response.name == "Success Response"
        assert response.status == "OK"
        assert response.code == 200
        assert len(response.headers) == 2
        assert response.headers[0].key == "Content-Type"
        assert response.headers[0].value == "application/json"
        assert response.body == '{"message": "Success"}'
        assert response.cookie == [{"name": "session", "value": "abc123"}]
        assert response._postman_previewlanguage == "json"
        assert response._time == 150
        assert response.response_time == 150

    def test_response_to_dict_minimal(self):
        """Test Response.to_dict with minimal data."""
        response = Response(name="Test Response", status="OK", code=200)

        result = response.to_dict()

        assert result == {"name": "Test Response", "status": "OK", "code": 200}

    def test_response_to_dict_full(self):
        """Test Response.to_dict with complete data."""
        headers = [Header("Content-Type", "application/json")]
        response = Response(
            name="Success Response",
            status="OK",
            code=200,
            headers=headers,
            body='{"message": "Success"}',
            cookie=[{"name": "session", "value": "abc123"}],
            _postman_previewlanguage="json",
            _time=150,
            response_time=150,
        )

        result = response.to_dict()

        assert result["name"] == "Success Response"
        assert result["status"] == "OK"
        assert result["code"] == 200
        assert len(result["header"]) == 1
        assert result["body"] == '{"message": "Success"}'
        assert result["cookie"] == [{"name": "session", "value": "abc123"}]
        assert result["_postman_previewlanguage"] == "json"
        assert result["_time"] == 150
        assert result["responseTime"] == 150

    def test_response_get_json_valid(self):
        """Test get_json with valid JSON body."""
        response = Response(
            name="JSON Response",
            status="OK",
            code=200,
            body='{"message": "Success", "count": 42}',
        )

        json_data = response.get_json()

        assert json_data is not None
        assert json_data["message"] == "Success"
        assert json_data["count"] == 42

    def test_response_get_json_invalid(self):
        """Test get_json with invalid JSON body."""
        response = Response(
            name="Text Response", status="OK", code=200, body="Not JSON"
        )

        json_data = response.get_json()

        assert json_data is None

    def test_response_get_json_empty(self):
        """Test get_json with empty body."""
        response = Response(name="Empty Response", status="OK", code=200, body=None)

        json_data = response.get_json()

        assert json_data is None

    def test_response_get_content_type(self):
        """Test get_content_type method."""
        headers = [
            Header("Content-Type", "application/json"),
            Header("Cache-Control", "no-cache"),
        ]
        response = Response(
            name="Test Response", status="OK", code=200, headers=headers
        )

        content_type = response.get_content_type()

        assert content_type == "application/json"

    def test_response_get_content_type_missing(self):
        """Test get_content_type when header is missing."""
        response = Response(name="Test Response", status="OK", code=200)

        content_type = response.get_content_type()

        assert content_type is None

    def test_response_is_json_by_content_type(self):
        """Test is_json detection by Content-Type header."""
        headers = [Header("Content-Type", "application/json")]
        response = Response(
            name="JSON Response", status="OK", code=200, headers=headers
        )

        assert response.is_json() is True

    def test_response_is_json_by_preview_language(self):
        """Test is_json detection by preview language."""
        response = Response(
            name="JSON Response",
            status="OK",
            code=200,
            _postman_previewlanguage="json",
        )

        assert response.is_json() is True

    def test_response_is_json_by_parsing(self):
        """Test is_json detection by parsing body."""
        response = Response(
            name="JSON Response", status="OK", code=200, body='{"valid": "json"}'
        )

        assert response.is_json() is True

    def test_response_is_json_false(self):
        """Test is_json returns False for non-JSON."""
        response = Response(
            name="Text Response", status="OK", code=200, body="Plain text"
        )

        assert response.is_json() is False

    def test_response_is_xml_by_content_type(self):
        """Test is_xml detection by Content-Type header."""
        headers = [Header("Content-Type", "application/xml")]
        response = Response(
            name="XML Response", status="OK", code=200, headers=headers
        )

        assert response.is_xml() is True

    def test_response_is_xml_by_preview_language(self):
        """Test is_xml detection by preview language."""
        response = Response(
            name="XML Response",
            status="OK",
            code=200,
            _postman_previewlanguage="xml",
        )

        assert response.is_xml() is True

    def test_response_is_xml_by_content(self):
        """Test is_xml detection by XML declaration."""
        response = Response(
            name="XML Response",
            status="OK",
            code=200,
            body='<?xml version="1.0"?><root></root>',
        )

        assert response.is_xml() is True

    def test_response_is_xml_false(self):
        """Test is_xml returns False for non-XML."""
        response = Response(
            name="JSON Response", status="OK", code=200, body='{"valid": "json"}'
        )

        assert response.is_xml() is False

    def test_response_is_html_by_content_type(self):
        """Test is_html detection by Content-Type header."""
        headers = [Header("Content-Type", "text/html")]
        response = Response(
            name="HTML Response", status="OK", code=200, headers=headers
        )

        assert response.is_html() is True

    def test_response_is_html_by_preview_language(self):
        """Test is_html detection by preview language."""
        response = Response(
            name="HTML Response",
            status="OK",
            code=200,
            _postman_previewlanguage="html",
        )

        assert response.is_html() is True

    def test_response_is_html_by_doctype(self):
        """Test is_html detection by DOCTYPE."""
        response = Response(
            name="HTML Response",
            status="OK",
            code=200,
            body="<!DOCTYPE html><html></html>",
        )

        assert response.is_html() is True

    def test_response_is_html_by_html_tag(self):
        """Test is_html detection by <html> tag."""
        response = Response(
            name="HTML Response", status="OK", code=200, body="<html><body></body></html>"
        )

        assert response.is_html() is True

    def test_response_is_html_false(self):
        """Test is_html returns False for non-HTML."""
        response = Response(
            name="JSON Response", status="OK", code=200, body='{"valid": "json"}'
        )

        assert response.is_html() is False

    def test_response_repr(self):
        """Test Response __repr__ method."""
        response = Response(name="Test Response", status="OK", code=200)

        assert repr(response) == "Response(name='Test Response', code=200, status='OK')"


class TestExampleResponse:
    """Tests for the ExampleResponse class."""

    def test_example_response_initialization_minimal(self):
        """Test ExampleResponse initialization with minimal parameters."""
        response = ExampleResponse(name="Example", status="OK", code=200)

        assert response.name == "Example"
        assert response.status == "OK"
        assert response.code == 200
        assert response.original_request is None
        assert response.id is None

    def test_example_response_initialization_full(self):
        """Test ExampleResponse initialization with all parameters."""
        original_request = {"method": "GET", "url": "https://api.example.com"}
        headers = [Header("Content-Type", "application/json")]

        response = ExampleResponse(
            name="Success Example",
            status="OK",
            code=200,
            headers=headers,
            body='{"result": "success"}',
            original_request=original_request,
            id="example-123",
        )

        assert response.name == "Success Example"
        assert response.status == "OK"
        assert response.code == 200
        assert response.headers == headers
        assert response.body == '{"result": "success"}'
        assert response.original_request == original_request
        assert response.id == "example-123"

    def test_example_response_from_dict_minimal(self):
        """Test ExampleResponse.from_dict with minimal data."""
        data = {"name": "Example", "response": {"status": "OK", "code": 200}}

        response = ExampleResponse.from_dict(data)

        assert response.name == "Example"
        assert response.status == "OK"
        assert response.code == 200

    def test_example_response_from_dict_full(self):
        """Test ExampleResponse.from_dict with complete data."""
        data = {
            "name": "Success Example",
            "id": "example-123",
            "originalRequest": {"method": "GET", "url": "https://api.example.com"},
            "response": {
                "status": "OK",
                "code": 200,
                "header": [{"key": "Content-Type", "value": "application/json"}],
                "body": '{"result": "success"}',
                "cookie": [],
                "_postman_previewlanguage": "json",
                "responseTime": 100,
            },
        }

        response = ExampleResponse.from_dict(data)

        assert response.name == "Success Example"
        assert response.id == "example-123"
        assert response.original_request == {
            "method": "GET",
            "url": "https://api.example.com",
        }
        assert response.status == "OK"
        assert response.code == 200
        assert len(response.headers) == 1
        assert response.body == '{"result": "success"}'
        assert response._postman_previewlanguage == "json"
        assert response.response_time == 100

    def test_example_response_to_dict_minimal(self):
        """Test ExampleResponse.to_dict with minimal data."""
        response = ExampleResponse(name="Example", status="OK", code=200)

        result = response.to_dict()

        assert result["name"] == "Example"
        assert result["response"]["status"] == "OK"
        assert result["response"]["code"] == 200

    def test_example_response_to_dict_full(self):
        """Test ExampleResponse.to_dict with complete data."""
        original_request = {"method": "GET", "url": "https://api.example.com"}
        headers = [Header("Content-Type", "application/json")]

        response = ExampleResponse(
            name="Success Example",
            status="OK",
            code=200,
            headers=headers,
            body='{"result": "success"}',
            original_request=original_request,
            id="example-123",
            _postman_previewlanguage="json",
            response_time=100,
        )

        result = response.to_dict()

        assert result["name"] == "Success Example"
        assert result["id"] == "example-123"
        assert result["originalRequest"] == original_request
        assert result["response"]["status"] == "OK"
        assert result["response"]["code"] == 200
        assert len(result["response"]["header"]) == 1
        assert result["response"]["body"] == '{"result": "success"}'
        assert result["response"]["_postman_previewlanguage"] == "json"
        assert result["response"]["responseTime"] == 100

    def test_example_response_inherits_response_methods(self):
        """Test that ExampleResponse inherits Response methods."""
        response = ExampleResponse(
            name="JSON Example",
            status="OK",
            code=200,
            body='{"message": "test"}',
            _postman_previewlanguage="json",
        )

        # Test inherited methods
        assert response.is_json() is True
        assert response.get_json() == {"message": "test"}
        assert response.is_xml() is False
        assert response.is_html() is False

    def test_example_response_repr(self):
        """Test ExampleResponse __repr__ method."""
        response = ExampleResponse(name="Test Example", status="OK", code=200)

        assert (
            repr(response) == "ExampleResponse(name='Test Example', code=200, status='OK')"
        )

    def test_example_response_roundtrip(self):
        """Test that ExampleResponse can be serialized and deserialized."""
        original = ExampleResponse(
            name="Roundtrip Test",
            status="Created",
            code=201,
            headers=[Header("Location", "/api/users/123")],
            body='{"id": 123}',
            original_request={"method": "POST"},
            id="test-id",
        )

        # Serialize to dict
        data = original.to_dict()

        # Deserialize from dict
        restored = ExampleResponse.from_dict(data)

        assert restored.name == original.name
        assert restored.status == original.status
        assert restored.code == original.code
        assert len(restored.headers) == len(original.headers)
        assert restored.body == original.body
        assert restored.original_request == original.original_request
        assert restored.id == original.id

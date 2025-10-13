"""
Tests for Request integration with example responses.
"""

import pytest
from python_postman.models.request import Request
from python_postman.models.response import ExampleResponse
from python_postman.models.url import Url
from python_postman.models.header import Header


class TestRequestResponseIntegration:
    """Tests for Request class integration with example responses."""

    def test_request_initialization_with_responses(self):
        """Test Request initialization with responses parameter."""
        url = Url("https://api.example.com/users")
        responses = [
            ExampleResponse(name="Success", status="OK", code=200),
            ExampleResponse(name="Not Found", status="Not Found", code=404),
        ]

        request = Request(
            name="Get User", method="GET", url=url, responses=responses
        )

        assert len(request.responses) == 2
        assert request.responses[0].name == "Success"
        assert request.responses[1].name == "Not Found"

    def test_request_initialization_without_responses(self):
        """Test Request initialization defaults to empty responses list."""
        url = Url("https://api.example.com/users")
        request = Request(name="Get User", method="GET", url=url)

        assert request.responses == []

    def test_request_add_response(self):
        """Test adding a response to a request."""
        url = Url("https://api.example.com/users")
        request = Request(name="Get User", method="GET", url=url)

        response = ExampleResponse(name="Success", status="OK", code=200)
        request.add_response(response)

        assert len(request.responses) == 1
        assert request.responses[0] is response

    def test_request_add_multiple_responses(self):
        """Test adding multiple responses to a request."""
        url = Url("https://api.example.com/users")
        request = Request(name="Get User", method="GET", url=url)

        response1 = ExampleResponse(name="Success", status="OK", code=200)
        response2 = ExampleResponse(name="Not Found", status="Not Found", code=404)
        response3 = ExampleResponse(
            name="Server Error", status="Internal Server Error", code=500
        )

        request.add_response(response1)
        request.add_response(response2)
        request.add_response(response3)

        assert len(request.responses) == 3
        assert request.responses[0].name == "Success"
        assert request.responses[1].name == "Not Found"
        assert request.responses[2].name == "Server Error"

    def test_request_get_response_by_name_found(self):
        """Test getting a response by name when it exists."""
        url = Url("https://api.example.com/users")
        responses = [
            ExampleResponse(name="Success", status="OK", code=200),
            ExampleResponse(name="Not Found", status="Not Found", code=404),
        ]
        request = Request(
            name="Get User", method="GET", url=url, responses=responses
        )

        response = request.get_response_by_name("Not Found")

        assert response is not None
        assert response.name == "Not Found"
        assert response.code == 404

    def test_request_get_response_by_name_not_found(self):
        """Test getting a response by name when it doesn't exist."""
        url = Url("https://api.example.com/users")
        responses = [ExampleResponse(name="Success", status="OK", code=200)]
        request = Request(
            name="Get User", method="GET", url=url, responses=responses
        )

        response = request.get_response_by_name("Not Found")

        assert response is None

    def test_request_get_response_by_name_empty_list(self):
        """Test getting a response by name when responses list is empty."""
        url = Url("https://api.example.com/users")
        request = Request(name="Get User", method="GET", url=url)

        response = request.get_response_by_name("Success")

        assert response is None

    def test_request_from_dict_with_responses(self):
        """Test Request.from_dict parsing responses."""
        data = {
            "name": "Get User",
            "request": {
                "method": "GET",
                "url": "https://api.example.com/users/1",
                "header": [],
            },
            "response": [
                {
                    "name": "Success",
                    "response": {
                        "status": "OK",
                        "code": 200,
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ],
                        "body": '{"id": 1, "name": "John"}',
                    },
                },
                {
                    "name": "Not Found",
                    "response": {
                        "status": "Not Found",
                        "code": 404,
                        "header": [],
                        "body": '{"error": "User not found"}',
                    },
                },
            ],
        }

        request = Request.from_dict(data)

        assert request.name == "Get User"
        assert len(request.responses) == 2
        assert request.responses[0].name == "Success"
        assert request.responses[0].code == 200
        assert request.responses[1].name == "Not Found"
        assert request.responses[1].code == 404

    def test_request_from_dict_without_responses(self):
        """Test Request.from_dict when no responses are present."""
        data = {
            "name": "Get User",
            "request": {
                "method": "GET",
                "url": "https://api.example.com/users/1",
                "header": [],
            },
        }

        request = Request.from_dict(data)

        assert request.name == "Get User"
        assert request.responses == []

    def test_request_to_dict_with_responses(self):
        """Test Request.to_dict serializing responses."""
        url = Url("https://api.example.com/users")
        responses = [
            ExampleResponse(
                name="Success",
                status="OK",
                code=200,
                body='{"id": 1}',
                headers=[Header("Content-Type", "application/json")],
            ),
            ExampleResponse(
                name="Error", status="Bad Request", code=400, body='{"error": "Invalid"}'
            ),
        ]
        request = Request(
            name="Get User", method="GET", url=url, responses=responses
        )

        result = request.to_dict()

        assert "response" in result
        assert len(result["response"]) == 2
        assert result["response"][0]["name"] == "Success"
        assert result["response"][0]["response"]["code"] == 200
        assert result["response"][1]["name"] == "Error"
        assert result["response"][1]["response"]["code"] == 400

    def test_request_to_dict_without_responses(self):
        """Test Request.to_dict when no responses are present."""
        url = Url("https://api.example.com/users")
        request = Request(name="Get User", method="GET", url=url)

        result = request.to_dict()

        assert "response" not in result

    def test_request_roundtrip_with_responses(self):
        """Test that Request with responses can be serialized and deserialized."""
        url = Url("https://api.example.com/users")
        original_responses = [
            ExampleResponse(
                name="Success",
                status="OK",
                code=200,
                body='{"id": 1, "name": "John"}',
                headers=[Header("Content-Type", "application/json")],
                original_request={"method": "GET", "url": "https://api.example.com/users/1"},
                id="resp-123",
            )
        ]
        original_request = Request(
            name="Get User",
            method="GET",
            url=url,
            description="Fetch user by ID",
            responses=original_responses,
        )

        # Serialize
        data = original_request.to_dict()

        # Deserialize
        restored_request = Request.from_dict(data)

        assert restored_request.name == original_request.name
        assert restored_request.method == original_request.method
        assert len(restored_request.responses) == len(original_request.responses)
        assert restored_request.responses[0].name == original_responses[0].name
        assert restored_request.responses[0].code == original_responses[0].code
        assert restored_request.responses[0].body == original_responses[0].body
        assert restored_request.responses[0].id == original_responses[0].id

    def test_request_responses_support_multiple_formats(self):
        """Test that responses support multiple body formats."""
        url = Url("https://api.example.com/data")
        responses = [
            ExampleResponse(
                name="JSON Response",
                status="OK",
                code=200,
                body='{"format": "json"}',
                _postman_previewlanguage="json",
            ),
            ExampleResponse(
                name="XML Response",
                status="OK",
                code=200,
                body='<?xml version="1.0"?><root><format>xml</format></root>',
                _postman_previewlanguage="xml",
            ),
            ExampleResponse(
                name="HTML Response",
                status="OK",
                code=200,
                body="<!DOCTYPE html><html><body>HTML</body></html>",
                _postman_previewlanguage="html",
            ),
            ExampleResponse(
                name="Plain Text Response",
                status="OK",
                code=200,
                body="Plain text content",
                _postman_previewlanguage="text",
            ),
        ]
        request = Request(
            name="Multi-format Request", method="GET", url=url, responses=responses
        )

        # Verify all formats are stored
        assert len(request.responses) == 4

        # Verify format detection works
        json_resp = request.get_response_by_name("JSON Response")
        assert json_resp.is_json() is True

        xml_resp = request.get_response_by_name("XML Response")
        assert xml_resp.is_xml() is True

        html_resp = request.get_response_by_name("HTML Response")
        assert html_resp.is_html() is True

        text_resp = request.get_response_by_name("Plain Text Response")
        assert text_resp.body == "Plain text content"

    def test_request_responses_maintain_backward_compatibility(self):
        """Test that existing Request API remains backward compatible."""
        # Old code that doesn't use responses should still work
        url = Url("https://api.example.com/users")
        request = Request(
            name="Get User",
            method="GET",
            url=url,
            description="Fetch user",
            headers=[Header("Accept", "application/json")],
        )

        # All existing attributes should work
        assert request.name == "Get User"
        assert request.method == "GET"
        assert request.url == url
        assert request.description == "Fetch user"
        assert len(request.headers) == 1
        assert request.responses == []  # New attribute defaults to empty list

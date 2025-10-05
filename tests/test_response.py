"""Tests for ExecutionResponse wrapper."""

import json
import pytest
from unittest.mock import Mock, MagicMock
from python_postman.execution.response import ExecutionResponse


class TestExecutionResponse:
    """Test cases for ExecutionResponse class."""

    def create_mock_httpx_response(
        self,
        status_code: int = 200,
        headers: dict = None,
        text: str = "test response",
        json_data: dict = None,
        content: bytes = None,
        url: str = "https://api.example.com/test",
        method: str = "GET",
    ):
        """Create a mock httpx response for testing."""
        mock_response = Mock()
        mock_response.status_code = status_code
        mock_response.headers = headers or {"Content-Type": "application/json"}
        mock_response.text = text
        mock_response.content = content or text.encode("utf-8")
        mock_response.url = url

        # Mock request object
        mock_request = Mock()
        mock_request.method = method
        mock_response.request = mock_request

        # Mock json() method
        if json_data is not None:
            mock_response.json.return_value = json_data
        else:
            mock_response.json.side_effect = json.JSONDecodeError("No JSON", "", 0)

        return mock_response

    def test_initialization(self):
        """Test ExecutionResponse initialization."""
        mock_response = self.create_mock_httpx_response()
        start_time = 1000.0
        end_time = 1001.5

        response = ExecutionResponse(mock_response, start_time, end_time)

        assert response._response == mock_response
        assert response._request_start_time == start_time
        assert response._request_end_time == end_time

    def test_status_code_property(self):
        """Test status_code property."""
        mock_response = self.create_mock_httpx_response(status_code=404)
        response = ExecutionResponse(mock_response, 1000.0, 1001.0)

        assert response.status_code == 404

    def test_headers_property(self):
        """Test headers property."""
        headers = {"Content-Type": "application/json", "X-Custom": "value"}
        mock_response = self.create_mock_httpx_response(headers=headers)
        response = ExecutionResponse(mock_response, 1000.0, 1001.0)

        assert response.headers == headers

    def test_text_property(self):
        """Test text property."""
        text_content = "Hello, World!"
        mock_response = self.create_mock_httpx_response(text=text_content)
        response = ExecutionResponse(mock_response, 1000.0, 1001.0)

        assert response.text == text_content

    def test_json_property_valid_json(self):
        """Test json property with valid JSON response."""
        json_data = {"message": "success", "data": [1, 2, 3]}
        mock_response = self.create_mock_httpx_response(json_data=json_data)
        response = ExecutionResponse(mock_response, 1000.0, 1001.0)

        assert response.json == json_data

    def test_json_property_invalid_json(self):
        """Test json property with invalid JSON response."""
        mock_response = self.create_mock_httpx_response(text="not json")
        response = ExecutionResponse(mock_response, 1000.0, 1001.0)

        with pytest.raises(json.JSONDecodeError):
            _ = response.json

    def test_content_property(self):
        """Test content property."""
        content = b"binary content"
        mock_response = self.create_mock_httpx_response(content=content)
        response = ExecutionResponse(mock_response, 1000.0, 1001.0)

        assert response.content == content

    def test_elapsed_ms_property(self):
        """Test elapsed_ms property."""
        start_time = 1000.0
        end_time = 1001.5  # 1.5 seconds difference
        mock_response = self.create_mock_httpx_response()
        response = ExecutionResponse(mock_response, start_time, end_time)

        assert response.elapsed_ms == 1500.0  # 1.5 seconds = 1500 ms

    def test_elapsed_seconds_property(self):
        """Test elapsed_seconds property."""
        start_time = 1000.0
        end_time = 1002.25  # 2.25 seconds difference
        mock_response = self.create_mock_httpx_response()
        response = ExecutionResponse(mock_response, start_time, end_time)

        assert response.elapsed_seconds == 2.25

    def test_url_property(self):
        """Test url property."""
        url = "https://api.example.com/users/123"
        mock_response = self.create_mock_httpx_response(url=url)
        response = ExecutionResponse(mock_response, 1000.0, 1001.0)

        assert response.url == url

    def test_request_method_property(self):
        """Test request_method property."""
        method = "POST"
        mock_response = self.create_mock_httpx_response(method=method)
        response = ExecutionResponse(mock_response, 1000.0, 1001.0)

        assert response.request_method == method

    def test_to_dict_with_json_response(self):
        """Test to_dict method with JSON response."""
        json_data = {"id": 1, "name": "test"}
        headers = {"Content-Type": "application/json"}
        mock_response = self.create_mock_httpx_response(
            status_code=200,
            headers=headers,
            text='{"id": 1, "name": "test"}',
            json_data=json_data,
            url="https://api.example.com/test",
            method="GET",
        )

        start_time = 1000.0
        end_time = 1001.5
        response = ExecutionResponse(mock_response, start_time, end_time)

        result = response.to_dict()

        expected = {
            "status": 200,
            "headers": headers,
            "body": '{"id": 1, "name": "test"}',
            "url": "https://api.example.com/test",
            "method": "GET",
            "elapsed_ms": 1500.0,
            "elapsed_seconds": 1.5,
            "json": json_data,
        }

        assert result == expected

    def test_to_dict_with_non_json_response(self):
        """Test to_dict method with non-JSON response."""
        headers = {"Content-Type": "text/plain"}
        mock_response = self.create_mock_httpx_response(
            status_code=200,
            headers=headers,
            text="plain text response",
            url="https://api.example.com/text",
            method="POST",
        )

        start_time = 1000.0
        end_time = 1000.75
        response = ExecutionResponse(mock_response, start_time, end_time)

        result = response.to_dict()

        expected = {
            "status": 200,
            "headers": headers,
            "body": "plain text response",
            "url": "https://api.example.com/text",
            "method": "POST",
            "elapsed_ms": 750.0,
            "elapsed_seconds": 0.75,
        }

        assert result == expected
        assert "json" not in result

    def test_is_success(self):
        """Test is_success method for various status codes."""
        # Success cases (2xx)
        for status in [200, 201, 204, 299]:
            mock_response = self.create_mock_httpx_response(status_code=status)
            response = ExecutionResponse(mock_response, 1000.0, 1001.0)
            assert response.is_success(), f"Status {status} should be success"

        # Non-success cases
        for status in [199, 300, 400, 500]:
            mock_response = self.create_mock_httpx_response(status_code=status)
            response = ExecutionResponse(mock_response, 1000.0, 1001.0)
            assert not response.is_success(), f"Status {status} should not be success"

    def test_is_redirect(self):
        """Test is_redirect method for various status codes."""
        # Redirect cases (3xx)
        for status in [300, 301, 302, 304, 399]:
            mock_response = self.create_mock_httpx_response(status_code=status)
            response = ExecutionResponse(mock_response, 1000.0, 1001.0)
            assert response.is_redirect(), f"Status {status} should be redirect"

        # Non-redirect cases
        for status in [200, 299, 400, 500]:
            mock_response = self.create_mock_httpx_response(status_code=status)
            response = ExecutionResponse(mock_response, 1000.0, 1001.0)
            assert not response.is_redirect(), f"Status {status} should not be redirect"

    def test_is_client_error(self):
        """Test is_client_error method for various status codes."""
        # Client error cases (4xx)
        for status in [400, 401, 404, 422, 499]:
            mock_response = self.create_mock_httpx_response(status_code=status)
            response = ExecutionResponse(mock_response, 1000.0, 1001.0)
            assert response.is_client_error(), f"Status {status} should be client error"

        # Non-client error cases
        for status in [200, 300, 399, 500]:
            mock_response = self.create_mock_httpx_response(status_code=status)
            response = ExecutionResponse(mock_response, 1000.0, 1001.0)
            assert (
                not response.is_client_error()
            ), f"Status {status} should not be client error"

    def test_is_server_error(self):
        """Test is_server_error method for various status codes."""
        # Server error cases (5xx)
        for status in [500, 501, 502, 503, 599]:
            mock_response = self.create_mock_httpx_response(status_code=status)
            response = ExecutionResponse(mock_response, 1000.0, 1001.0)
            assert response.is_server_error(), f"Status {status} should be server error"

        # Non-server error cases
        for status in [200, 300, 400, 499]:
            mock_response = self.create_mock_httpx_response(status_code=status)
            response = ExecutionResponse(mock_response, 1000.0, 1001.0)
            assert (
                not response.is_server_error()
            ), f"Status {status} should not be server error"

    def test_repr(self):
        """Test string representation of ExecutionResponse."""
        mock_response = self.create_mock_httpx_response(status_code=201)
        start_time = 1000.0
        end_time = 1001.234
        response = ExecutionResponse(mock_response, start_time, end_time)

        repr_str = repr(response)
        assert "ExecutionResponse" in repr_str
        assert "status=201" in repr_str
        assert "elapsed_ms=1234.00" in repr_str

    def test_timing_precision(self):
        """Test timing calculations with high precision."""
        mock_response = self.create_mock_httpx_response()
        start_time = 1000.123456
        end_time = 1000.987654
        response = ExecutionResponse(mock_response, start_time, end_time)

        expected_seconds = end_time - start_time
        expected_ms = expected_seconds * 1000

        assert abs(response.elapsed_seconds - expected_seconds) < 1e-10
        assert abs(response.elapsed_ms - expected_ms) < 1e-7

    def test_headers_dict_conversion(self):
        """Test that headers are properly converted to dict."""
        # Mock httpx headers object that might not be a plain dict
        mock_headers = MagicMock()
        headers_data = [("Content-Type", "application/json"), ("X-Test", "value")]
        mock_headers.__iter__ = lambda self: iter(headers_data)
        mock_headers.items = lambda: headers_data

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = mock_headers
        mock_response.text = "test"
        mock_response.content = b"test"
        mock_response.url = "https://example.com"
        mock_response.request = Mock()
        mock_response.request.method = "GET"
        mock_response.json.side_effect = json.JSONDecodeError("No JSON", "", 0)

        response = ExecutionResponse(mock_response, 1000.0, 1001.0)

        # Should convert to dict properly
        headers_dict = response.headers
        assert isinstance(headers_dict, dict)
        assert headers_dict == {"Content-Type": "application/json", "X-Test": "value"}

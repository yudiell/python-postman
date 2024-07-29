import pytest
from unittest.mock import Mock, patch
import json

# Update this import to match your actual module structure
from src.python_postman.modules.http import Request, CollectionRequest


@pytest.fixture
def mock_collection_request():
    mock_request = Mock(spec=CollectionRequest)
    mock_request.url = Mock()
    mock_request.url.base_url = "http://example.com"
    mock_request.headers = Mock()
    mock_request.headers.as_dict = {}
    return mock_request


@pytest.fixture
def request_instance(mock_collection_request):
    return Request(request=mock_collection_request)


def test_set_headers_with_no_existing_headers(request_instance):
    request_instance._request.headers = None
    headers = {"Content-Type": "application/json"}

    request_instance.set_headers(headers)

    assert "Content-Type" in request_instance.headers
    assert request_instance.headers["Content-Type"] == "application/json"


def test_set_headers_with_existing_headers(request_instance):
    existing_headers = {"Authorization": "Bearer token"}
    request_instance._request.headers.as_dict = existing_headers
    request_instance.headers.update(existing_headers)
    new_headers = {"Content-Type": "application/json"}

    request_instance.set_headers(new_headers)

    assert "Authorization" in request_instance.headers
    assert "Content-Type" in request_instance.headers
    assert request_instance.headers["Authorization"] == "Bearer token"
    assert request_instance.headers["Content-Type"] == "application/json"


def test_set_headers_with_template_substitution(request_instance):
    existing_headers = {"Authorization": "Bearer ${token}"}
    request_instance._request.headers.as_dict = existing_headers
    request_instance.headers.update(existing_headers)
    new_headers = {"token": "abc123"}

    request_instance.set_headers(new_headers)

    assert request_instance.headers["Authorization"] == "Bearer abc123"


def test_set_headers_with_partial_template_substitution(request_instance):
    existing_headers = {"Authorization": "Bearer ${token}", "X-Custom": "${custom}"}
    request_instance._request.headers.as_dict = existing_headers
    request_instance.headers.update(existing_headers)
    new_headers = {"token": "abc123"}

    request_instance.set_headers(new_headers)

    assert request_instance.headers["Authorization"] == "Bearer abc123"
    assert "X-Custom" in request_instance.headers
    assert request_instance.headers["X-Custom"] == "${custom}"


@patch("src.python_postman.modules.http.CustomTemplate")
def test_set_headers_custom_template_usage(MockCustomTemplate, request_instance):
    mock_template = Mock()
    MockCustomTemplate.return_value = mock_template
    mock_template.safe_substitute.return_value = (
        '{"Key": "Value", "Unsubstituted": "${placeholder}"}'
    )

    existing_headers = {"OldKey": "OldValue"}
    request_instance._request.headers.as_dict = existing_headers
    request_instance.headers.update(existing_headers)
    new_headers = {"NewKey": "NewValue"}

    request_instance.set_headers(new_headers)

    MockCustomTemplate.assert_called_once_with(json.dumps(existing_headers))
    mock_template.safe_substitute.assert_called_once_with(new_headers)
    assert "Key" in request_instance.headers
    assert request_instance.headers["Key"] == "Value"
    assert "Unsubstituted" not in request_instance.headers


def test_set_headers_with_empty_input(request_instance):
    existing_headers = {"Authorization": "Bearer token"}
    request_instance._request.headers.as_dict = existing_headers
    request_instance.headers.update(existing_headers)

    request_instance.set_headers({})

    assert "Authorization" in request_instance.headers
    assert request_instance.headers["Authorization"] == "Bearer token"


def test_set_headers_with_none_input(request_instance):
    existing_headers = {"Authorization": "Bearer token"}
    request_instance._request.headers.as_dict = existing_headers
    request_instance.headers.update(existing_headers)

    request_instance.set_headers(None)

    assert "Authorization" in request_instance.headers
    assert request_instance.headers["Authorization"] == "Bearer token"


@pytest.mark.parametrize(
    "invalid_input",
    [
        42,
        "not a dict",
        ["list", "instead", "of", "dict"],
        set(["set", "instead", "of", "dict"]),
    ],
)
def test_set_headers_with_invalid_input_type(request_instance, invalid_input):
    with pytest.raises((AttributeError, TypeError)):
        request_instance.set_headers(invalid_input)


def test_set_headers_with_complex_template(request_instance):
    existing_headers = {
        "Authorization": "Bearer ${token}",
        "X-Api-Key": "${api_key}",
        "User-Agent": "MyApp/${version}",
    }
    request_instance._request.headers.as_dict = existing_headers
    request_instance.headers.update(existing_headers)
    new_headers = {"token": "abc123", "api_key": "secret_key", "version": "1.0.0"}

    request_instance.set_headers(new_headers)

    assert request_instance.headers["Authorization"] == "Bearer abc123"
    assert request_instance.headers["X-Api-Key"] == "secret_key"
    assert request_instance.headers["User-Agent"] == "MyApp/1.0.0"

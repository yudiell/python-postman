import pytest
from unittest.mock import MagicMock

from src.python_postman.modules.http import Request
from src.python_postman.request import Request as CollecionRequest
from src.python_postman.url import Url


@pytest.fixture
def request_instance() -> Request:
    mock_url = MagicMock(spec=Url)
    mock_url.base_url = "https://api.example.com/${version}/users/${user_id}"
    mock_collection_request = MagicMock(spec=CollecionRequest)
    mock_collection_request.url = mock_url
    mock_request = Request(request=mock_collection_request)
    return mock_request


def test_set_url_with_variables(request_instance):
    path_variables = {"version": "v1", "user_id": "123"}
    request_instance.set_url(path_variables)
    assert request_instance.url == "https://api.example.com/v1/users/123"


def test_set_url_with_empty_dict(request_instance):
    message = (
        "One or more path variables were not substituted in the URL."
        "Please inspect your path variable names."
    )
    path_variables = {}
    with pytest.raises(ValueError, match=message):
        request_instance.set_url(path_variables)


def test_set_path_with_static_path(request_instance):
    request_instance._request.url.base_url = "https://api.example.com/static/path"
    path_variables = {"version": "v1"}
    request_instance.set_url(path_variables)
    assert request_instance.url == "https://api.example.com/static/path"


def test_set_url_with_unmatched_variables(request_instance):
    message = (
        "One or more path variables were not substituted in the URL."
        "Please inspect your path variable names."
    )
    path_variables = {"version": "v2", "unused": "extra"}
    with pytest.raises(ValueError, match=message):
        request_instance.set_url(path_variables)


def test_set_url_with_none_base_url(request_instance):
    request_instance._request.url.base_url = None
    path_variables = {"version": "v1"}
    message = (
        "Base URL was not found in the collection request."
        "Please set a base url in the collection request using Postman."
    )
    with pytest.raises(ValueError, match=message):
        request_instance.set_url(path_variables)


def test_set_url_multiple_substitutions(request_instance):
    request_instance._request.url.base_url = (
        "https://${domain}.com/${version}/users/${user_id}"
    )
    path_variables = {"domain": "api", "version": "v2", "user_id": "123"}
    request_instance.set_url(path_variables)
    assert request_instance.url == "https://api.com/v2/users/123"


def test_set_url_empty_string_substitution(request_instance):
    request_instance._request.url.base_url = "https://api.example.com/${version}/users"
    path_variables = {"version": ""}
    request_instance.set_url(path_variables)
    assert request_instance.url == "https://api.example.com//users"


def test_set_url_repeated_substitution(request_instance):
    request_instance._request.url.base_url = "https://${env}.example.com/${env}/api"
    path_variables = {"env": "prod"}
    request_instance.set_url(path_variables)
    assert request_instance.url == "https://prod.example.com/prod/api"


def test_set_url_special_characters(request_instance):
    request_instance._request.url.base_url = (
        "https://api.example.com/${path}/search?q=${query}"
    )
    path_variables = {"path": "products", "query": "special!@#$%^&*()"}
    request_instance.set_url(path_variables)
    expected_url = "https://api.example.com/products/search?q=special!@#$%^&*()"
    assert request_instance.url == expected_url

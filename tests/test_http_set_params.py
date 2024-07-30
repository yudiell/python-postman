import pytest
from unittest.mock import MagicMock
from src.python_postman.modules.http import Request
from src.python_postman.url import Url


@pytest.fixture
def mock_collection_request():
    mock_request = MagicMock(spec=Request)
    mock_request.url = MagicMock(spec=Url)
    mock_request.url.params = None
    mock_request.url.base_url = "https://api.example.com"  # Add this line
    return mock_request


def test_set_params_with_no_url_params(mock_collection_request):
    request = Request(mock_collection_request)
    params = {"key": "value"}
    request.set_params(params)
    assert request.params == {}


def test_set_params_with_url_params(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "${value2}"}
    request = Request(mock_collection_request)
    params = {"value1": "test1", "value2": "test2"}
    request.set_params(params)
    assert request.params == {"param1": "test1", "param2": "test2"}


def test_set_params_with_partial_substitution(mock_collection_request):
    mock_collection_request.url.params = {
        "param1": "${value1}",
        "param2": "${value2}",
        "param3": "${value3}",
    }
    request = Request(mock_collection_request)
    params = {"value1": "test1", "value2": "test2"}
    request.set_params(params)
    assert request.params == {"param1": "test1", "param2": "test2"}


def test_set_params_with_no_substitution(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "${value2}"}
    request = Request(mock_collection_request)
    params = {"value3": "test3", "value4": "test4"}
    request.set_params(params)
    assert request.params == {}


def test_set_params_with_mixed_substitution(mock_collection_request):
    mock_collection_request.url.params = {
        "param1": "${value1}",
        "param2": "static_value",
        "param3": "${value3}",
    }
    request = Request(mock_collection_request)
    params = {"value1": "test1", "value3": "test3"}
    request.set_params(params)
    assert request.params == {
        "param1": "test1",
        "param2": "static_value",
        "param3": "test3",
    }


def test_set_params_with_empty_params(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "${value2}"}
    request = Request(mock_collection_request)
    request.set_params({})
    assert request.params == {}


def test_set_params_with_none_params(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "${value2}"}
    request = Request(mock_collection_request)
    request.set_params(None)
    assert request.params == {}


# -----


def test_set_params_with_integer_values(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "${value2}"}
    request = Request(mock_collection_request)
    params = {"value1": 123, "value2": 456}
    request.set_params(params)
    assert request.params == {"param1": "123", "param2": "456"}


def test_set_params_with_boolean_values(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "${value2}"}
    request = Request(mock_collection_request)
    params = {"value1": True, "value2": False}
    request.set_params(params)
    assert request.params == {"param1": "True", "param2": "False"}


def test_set_params_with_nested_dictionaries(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "${value2}"}
    request = Request(mock_collection_request)
    params = {"value1": {"nested": "value"}, "value2": [1, 2, 3]}
    request.set_params(params)
    assert request.params == {"param1": '{"nested": "value"}', "param2": "[1, 2, 3]"}


def test_set_params_with_extra_params(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}"}
    request = Request(mock_collection_request)
    params = {"value1": "test1", "value2": "test2", "value3": "test3"}
    request.set_params(params)
    assert request.params == {"param1": "test1"}


def test_set_params_with_missing_params(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "${value2}"}
    request = Request(mock_collection_request)
    params = {"value1": "test1"}
    request.set_params(params)
    assert request.params == {"param1": "test1"}


def test_set_params_with_multiple_substitutions(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}_${value2}"}
    request = Request(mock_collection_request)
    params = {"value1": "test1", "value2": "test2"}
    request.set_params(params)
    assert request.params == {"param1": "test1_test2"}


def test_set_params_with_unchanged_values(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "static"}
    request = Request(mock_collection_request)
    params = {"value1": "test1"}
    request.set_params(params)
    assert request.params == {"param1": "test1", "param2": "static"}


def test_set_params_with_empty_string_values(mock_collection_request):
    mock_collection_request.url.params = {"param1": "${value1}", "param2": "${value2}"}
    request = Request(mock_collection_request)
    params = {"value1": "", "value2": "test2"}
    request.set_params(params)
    assert request.params == {"param1": "", "param2": "test2"}

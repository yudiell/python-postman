import pytest
from unittest.mock import Mock, patch
from src.python_postman.modules.http import Request
import json


@pytest.fixture
def request_instance():
    request = Request(Mock())
    request.log = Mock()
    return request


def test_set_body_no_body(request_instance):
    request_instance._request = Mock(body=None)
    request_instance.set_body({})
    request_instance.log.info.assert_called_with(
        "Request does not have a body. Skipping body setting."
    )


@pytest.mark.parametrize(
    "raw_body, body_input, expected",
    [
        (
            '{"key": "${value}", "number": ${num}, "bool": ${flag}}',
            {"value": "test", "num": 42, "flag": True},
            '{"key": "test", "number": 42, "bool": true}',
        ),
        (
            '{"string": "${str_val}", "array": [1, "${arr_val}", true]}',
            {"str_val": "hello", "arr_val": "world"},
            '{"string": "hello", "array": [1, "world", true]}',
        ),
    ],
)
def test_set_body_raw(request_instance, raw_body, body_input, expected):
    request_instance._request = Mock(body=Mock(raw=raw_body))
    request_instance.set_body(body_input)
    assert json.loads(request_instance.body) == json.loads(expected)


@pytest.mark.parametrize(
    "body_type, body_data",
    [
        ("formdata_as_dict", {"key1": "${value1}", "key2": "${value2}"}),
        ("urlencoded_as_dict", {"key1": "${value1}", "key2": "${value2}"}),
    ],
)
def test_set_body_form_data(request_instance, body_type, body_data):
    mock_body = Mock(
        **{
            "raw": None,
            "formdata_as_dict": None,
            "urlencoded_as_dict": None,
        }
    )
    setattr(mock_body, body_type, body_data)
    request_instance._request = Mock(body=mock_body)

    body_input = {"value1": "test", "value2": 42}
    request_instance.set_body(body_input)

    expected = {"key1": "test", "key2": "42"}
    assert request_instance.body == expected


def test_set_body_unsupported_format(request_instance):
    request_instance._request = Mock(
        body=Mock(raw=None, formdata_as_dict=None, urlencoded_as_dict=None)
    )
    request_instance.set_body({})
    request_instance.log.warning.assert_called_with(
        "Request body is empty or in an unsupported format."
    )


def test_set_body_with_complex_json(request_instance):
    raw_json = """{
        "string": "${str_val}",
        "number": ${num_val},
        "boolean": ${bool_val},
        "null": ${null_val},
        "array": [1, "${arr_val}", true],
        "nested": {"key": "${nested_val}"}
    }"""
    request_instance._request = Mock(body=Mock(raw=raw_json))
    body = {
        "str_val": "test",
        "num_val": 42,
        "bool_val": False,
        "null_val": "null",
        "arr_val": "array_item",
        "nested_val": "nested_value",
    }
    request_instance.set_body(body)
    expected = {
        "string": "test",
        "number": 42,
        "boolean": False,
        "null": None,
        "array": [1, "array_item", True],
        "nested": {"key": "nested_value"},
    }
    assert json.loads(request_instance.body) == expected


@patch("src.python_postman.modules.http.CustomTemplate")
def test_custom_template_usage(mock_custom_template, request_instance):
    mock_template = Mock()
    mock_custom_template.return_value = mock_template
    mock_template.safe_substitute.return_value = '{"key": "substituted_value"}'

    request_instance._request = Mock(body=Mock(raw='{"key": "${value}"}'))
    request_instance.set_body({"value": "test"})

    mock_custom_template.assert_called_with('{"key": "${value}"}')
    mock_template.safe_substitute.assert_called_with({"value": "test"})
    assert request_instance.body == '{"key": "substituted_value"}'


def test_set_body_error_handling(request_instance):
    request_instance._request = Mock(body=Mock())
    request_instance._request.body.raw = property(
        lambda self: (_ for _ in ()).throw(AttributeError("Simulated AttributeError"))
    )

    request_instance.set_body({"value": "test"})
    request_instance.log.error.assert_called()

import pytest
from pydantic import ValidationError
from python_postman.config import AuthValues  # Adjust the import path as needed


def test_auth_values_valid_input():
    auth = AuthValues(key="api_key", value="12345", type="string")
    assert auth.key == "api_key"
    assert auth.value == "12345"
    assert auth.type == "string"
    assert auth.disabled is None


def test_auth_values_with_disabled():
    auth = AuthValues(key="api_key", value="12345", type="string", disabled=True)
    assert auth.disabled is True


def test_auth_values_missing_required_field():
    with pytest.raises(ValidationError):
        AuthValues(key="api_key", value="12345")  # Missing 'type'


def test_auth_values_invalid_type():
    with pytest.raises(ValidationError):
        AuthValues(key="api_key", value="12345", type=123)  # Type should be a string


def test_auth_values_incorrect_disabled():
    with pytest.raises(ValidationError):
        AuthValues(
            key="api_key", value="12345", type="string", disabled="Invalid"
        )  # Disabled should be a boolean


def test_auth_values_invalid_disabled():
    # Pydantic v2 might be coercing non-boolean values to boolean
    auth = AuthValues(key="api_key", value="12345", type="string", disabled="yes")
    assert auth.disabled is True  # "yes" is coerced to True


def test_auth_values_extra_field():
    # Pydantic v2 might be ignoring extra fields by default
    auth = AuthValues(key="api_key", value="12345", type="string", extra_field="extra")
    assert not hasattr(auth, "extra_field")


def test_auth_values_empty_string():
    auth = AuthValues(key="", value="", type="")
    assert auth.key == ""
    assert auth.value == ""
    assert auth.type == ""


def test_auth_values_whitespace():
    auth = AuthValues(key=" space ", value=" value ", type=" type ")
    assert auth.key == " space "
    assert auth.value == " value "
    assert auth.type == " type "


def test_auth_values_dict_input():
    data = {"key": "api_key", "value": "12345", "type": "string"}
    auth = AuthValues(**data)
    assert auth.dict() == {**data, "disabled": None}


def test_auth_values_model_dump():
    auth = AuthValues(key="api_key", value="12345", type="string", disabled=False)
    expected = {"key": "api_key", "value": "12345", "type": "string", "disabled": False}
    assert auth.dict() == expected


def test_auth_values_model_copy():
    auth1 = AuthValues(key="api_key", value="12345", type="string")
    auth2 = auth1.copy()
    assert auth1 == auth2
    assert auth1 is not auth2


def test_auth_values_update():
    auth = AuthValues(key="api_key", value="12345", type="string")
    updated = auth.copy(update={"value": "67890", "disabled": True})
    assert updated.value == "67890"
    assert updated.disabled is True
    assert auth.value == "12345"  # Original instance remains unchanged

import pytest
import json
from python_postman.config import (
    Info,
    Request,
    Auth,
    AuthValues,
    Url,
)
from python_postman.collection import Collection


@pytest.fixture
def mock_collection():
    collection = Collection("zCollectionTest.postman_collection.json")
    return collection


def test_collection_initialization(mock_collection):
    collection = mock_collection

    assert isinstance(collection._info, Info)
    assert collection._info.name == "CollectionTest"
    assert len(collection._items) == 3
    assert len(collection._requests) == 9
    assert isinstance(collection._auth, Auth)
    assert collection._auth.type == "apikey"


def test_get_existing_request(mock_collection):
    collection = mock_collection
    request = collection.get_request("RequestOne")

    assert isinstance(request, Request)
    assert request.name == "RequestOne"
    assert request.method == "GET"
    assert isinstance(request.url, Url)
    assert request.url.raw == "https://example.com/v1/req-one"


def test_get_non_existent_request(mock_collection):
    collection = mock_collection
    with pytest.raises(
        ValueError, match="No request found with the name='NonExistentRequest'"
    ):
        collection.get_request("NonExistentRequest")


def test_duplicate_request_names(mock_collection):
    collection = mock_collection
    collection._requests.append(Request(name="RequestOne", method="GET"))
    with pytest.raises(
        ValueError, match="Please ensure that the Postman request names are unique."
    ):
        collection.get_request("RequestOne")


def test_collection_variables(mock_collection):
    collection = mock_collection

    assert len(collection._variables) == 1
    assert collection._variables[0].key == "baseUrl"
    assert collection._variables[0].value == "https://example.com/v1"


def test_auth_application(mock_collection):
    collection = mock_collection
    collection._auth = Auth(
        type="apikey",
        noauth=None,
        basic=None,
        bearer=None,
        apikey=[
            AuthValues(
                key="value", value="${my-api-key-value}", type="string", disabled=None
            ),
            AuthValues(key="in", value="query", type="string", disabled=None),
            AuthValues(key="key", value="My-API-Key", type="string", disabled=None),
        ],
    )
    assert collection._auth.apikey[0].value == "${my-api-key-value}"


def test_events_in_request(mock_collection):
    collection = mock_collection
    request = collection.get_request("RequestOne")

    assert hasattr(request, "prerequest")
    assert hasattr(request, "test")
    assert request.prerequest.script.exec == [
        'var preRequestScript = "Pre-Request Script"'
    ]
    assert request.test.script.exec == [
        'var postResponseScript = "Post-Response Script"'
    ]


def test_collection_file_not_found():
    with pytest.raises(FileNotFoundError):
        Collection("non_existent_file.json")


def test_invalid_json_in_collection_file():
    with pytest.raises(json.JSONDecodeError):
        Collection("zInvalidCollectionTest.postman_collection.json")

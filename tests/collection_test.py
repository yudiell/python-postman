import pytest
from unittest.mock import patch

from python_postman.config import Info, Request
from python_postman.collection import Collection

collection = Collection("CollectionTest.postman_collection.json")


def test_collection_initialization():
    assert collection._info.name == "CollectionTest"
    assert isinstance(collection._info, Info)
    # assert collection.data["item"][0]["name"] == "FolderOne"
    assert len(collection._items) == 3
    assert len(collection._requests) == 9


def test_get_request_success():
    request = collection.get_request("RequestOne")
    assert isinstance(request, Request)
    assert request.name == "RequestOne"
    assert request.method == "GET"
    assert request.url.raw == "${baseUrl}/req-one"


def test_get_request_not_found():
    with pytest.raises(
        ValueError, match="No request found with the name='Non-existent Request'"
    ):
        collection.get_request("Non-existent Request")


def test_environment_variable_substitution():
    request = collection.get_request("RequestOne")
    request.url.raw = "https://api.example.com/${TEST_VAR}"

    with patch.dict("os.environ", {"TEST_VAR": "substituted"}):
        request = collection.get_request("RequestOne")
        assert request.url.raw == "https://api.example.com/substituted"


# def test_multiple_requests_with_same_name(sample_collection_data):
#     sample_collection_data["item"].append(sample_collection_data["item"][0].copy())
#     json_data = json.dumps(sample_collection_data)
#     mock_file = mock_open(read_data=json_data)

#     with patch("builtins.open", mock_file):
#         collection = Collection("fake_path.json")
#         with pytest.raises(
#             ValueError, match="Please ensure that the Postman request names are unique."
#         ):
#             collection.get_request("Test Request")


# # Helper function to print the mock file content for debugging
# def print_mock_file_content(mock_file):
#     mock_file.return_value.read.return_value = (
#         mock_file.return_value.read.return_value.replace("${", "{{").replace("}", "}}")
#     )
#     print(f"Mock file content: {mock_file.return_value.read.return_value}")

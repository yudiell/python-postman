"""
Tests for the Folder class.
"""

import pytest
from python_postman.models.folder import Folder
from python_postman.models.request import Request
from python_postman.models.item import Item
from python_postman.models.url import Url
from python_postman.models.auth import Auth
from python_postman.models.event import Event
from python_postman.models.variable import Variable


def test_folder_inherits_from_item():
    """Test that Folder inherits from Item."""
    assert issubclass(Folder, Item)


def test_folder_initialization_minimal():
    """Test Folder initialization with minimal parameters."""
    folder = Folder("API Tests", [])

    assert folder.name == "API Tests"
    assert folder.items == []
    assert folder.description is None
    assert folder.auth is None
    assert folder.events == []
    assert folder.variables == []


def test_folder_initialization_full():
    """Test Folder initialization with all parameters."""
    url = Url("https://api.example.com/users")
    request = Request("Get Users", "GET", url)
    auth = Auth("bearer", {"token": "abc123"})
    events = [Event("prerequest", "console.log('folder test');")]
    variables = [Variable("baseUrl", "https://api.example.com")]

    folder = Folder(
        name="User API",
        items=[request],
        description="User management endpoints",
        auth=auth,
        events=events,
        variables=variables,
    )

    assert folder.name == "User API"
    assert folder.items == [request]
    assert folder.description == "User management endpoints"
    assert folder.auth == auth
    assert folder.events == events
    assert folder.variables == variables


def test_folder_get_requests_empty():
    """Test get_requests with empty folder."""
    folder = Folder("Empty Folder", [])

    requests = list(folder.get_requests())

    assert requests == []


def test_folder_get_requests_with_requests():
    """Test get_requests with folder containing requests."""
    url1 = Url("https://api.example.com/users")
    url2 = Url("https://api.example.com/posts")
    request1 = Request("Get Users", "GET", url1)
    request2 = Request("Get Posts", "GET", url2)

    folder = Folder("API Tests", [request1, request2])

    requests = list(folder.get_requests())

    assert len(requests) == 2
    assert request1 in requests
    assert request2 in requests


def test_folder_get_requests_recursive():
    """Test get_requests with nested folders."""
    # Create requests
    url1 = Url("https://api.example.com/users")
    url2 = Url("https://api.example.com/posts")
    url3 = Url("https://api.example.com/comments")

    request1 = Request("Get Users", "GET", url1)
    request2 = Request("Get Posts", "GET", url2)
    request3 = Request("Get Comments", "GET", url3)

    # Create nested folder structure
    subfolder = Folder("Posts", [request2, request3])
    main_folder = Folder("API Tests", [request1, subfolder])

    requests = list(main_folder.get_requests())

    assert len(requests) == 3
    assert request1 in requests
    assert request2 in requests
    assert request3 in requests


def test_folder_get_requests_deeply_nested():
    """Test get_requests with deeply nested folder structure."""
    # Create requests
    url1 = Url("https://api.example.com/users")
    url2 = Url("https://api.example.com/posts")
    url3 = Url("https://api.example.com/comments")

    request1 = Request("Get Users", "GET", url1)
    request2 = Request("Get Posts", "GET", url2)
    request3 = Request("Get Comments", "GET", url3)

    # Create deeply nested structure
    deep_folder = Folder("Comments", [request3])
    middle_folder = Folder("Posts", [request2, deep_folder])
    main_folder = Folder("API Tests", [request1, middle_folder])

    requests = list(main_folder.get_requests())

    assert len(requests) == 3
    assert request1 in requests
    assert request2 in requests
    assert request3 in requests


def test_folder_get_subfolders_empty():
    """Test get_subfolders with folder containing no subfolders."""
    url = Url("https://api.example.com/users")
    request = Request("Get Users", "GET", url)
    folder = Folder("API Tests", [request])

    subfolders = folder.get_subfolders()

    assert subfolders == []


def test_folder_get_subfolders_with_folders():
    """Test get_subfolders with folder containing subfolders."""
    url = Url("https://api.example.com/users")
    request = Request("Get Users", "GET", url)

    subfolder1 = Folder("Users", [])
    subfolder2 = Folder("Posts", [])

    main_folder = Folder("API Tests", [request, subfolder1, subfolder2])

    subfolders = main_folder.get_subfolders()

    assert len(subfolders) == 2
    assert subfolder1 in subfolders
    assert subfolder2 in subfolders


def test_folder_get_subfolders_mixed_items():
    """Test get_subfolders with folder containing mixed items."""
    url1 = Url("https://api.example.com/users")
    url2 = Url("https://api.example.com/posts")

    request1 = Request("Get Users", "GET", url1)
    request2 = Request("Get Posts", "GET", url2)
    subfolder = Folder("Admin", [])

    main_folder = Folder("API Tests", [request1, subfolder, request2])

    subfolders = main_folder.get_subfolders()

    assert len(subfolders) == 1
    assert subfolders[0] is subfolder


def test_folder_with_empty_lists():
    """Test Folder with explicitly empty lists."""
    folder = Folder(name="Test Folder", items=[], events=[], variables=[])

    assert folder.items == []
    assert folder.events == []
    assert folder.variables == []


def test_folder_str_representation():
    """Test string representation of Folder."""
    folder = Folder("API Tests", [])

    assert str(folder) == "Folder(name='API Tests')"


def test_folder_repr_representation():
    """Test repr representation of Folder."""
    folder = Folder("API Tests", [], "Test folder description")

    assert (
        repr(folder)
        == "Folder(name='API Tests', description='Test folder description')"
    )

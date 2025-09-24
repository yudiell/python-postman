"""
Tests for the Request class.
"""

import pytest
from python_postman.models.request import Request
from python_postman.models.item import Item
from python_postman.models.url import Url
from python_postman.models.header import Header
from python_postman.models.body import Body
from python_postman.models.auth import Auth
from python_postman.models.event import Event


def test_request_inherits_from_item():
    """Test that Request inherits from Item."""
    assert issubclass(Request, Item)


def test_request_initialization_minimal():
    """Test Request initialization with minimal parameters."""
    url = Url("https://api.example.com/users")
    request = Request("Get Users", "GET", url)

    assert request.name == "Get Users"
    assert request.method == "GET"
    assert request.url == url
    assert request.description is None
    assert request.headers == []
    assert request.body is None
    assert request.auth is None
    assert request.events == []


def test_request_initialization_full():
    """Test Request initialization with all parameters."""
    url = Url("https://api.example.com/users")
    headers = [Header("Content-Type", "application/json")]
    body = Body("raw", '{"name": "John"}')
    auth = Auth("bearer", {"token": "abc123"})
    events = [Event("prerequest", "console.log('test');")]

    request = Request(
        name="Create User",
        method="POST",
        url=url,
        description="Creates a new user",
        headers=headers,
        body=body,
        auth=auth,
        events=events,
    )

    assert request.name == "Create User"
    assert request.method == "POST"
    assert request.url == url
    assert request.description == "Creates a new user"
    assert request.headers == headers
    assert request.body == body
    assert request.auth == auth
    assert request.events == events


def test_request_get_requests():
    """Test that get_requests returns the request itself."""
    url = Url("https://api.example.com/users")
    request = Request("Get Users", "GET", url)

    requests = list(request.get_requests())

    assert len(requests) == 1
    assert requests[0] is request


def test_request_get_requests_iterator():
    """Test that get_requests returns an iterator."""
    url = Url("https://api.example.com/users")
    request = Request("Get Users", "GET", url)

    requests_iter = request.get_requests()

    # Should be able to iterate multiple times
    first_iteration = list(requests_iter)
    second_iteration = list(request.get_requests())

    assert len(first_iteration) == 1
    assert len(second_iteration) == 1
    assert first_iteration[0] is request
    assert second_iteration[0] is request


def test_request_with_empty_lists():
    """Test Request with explicitly empty lists."""
    url = Url("https://api.example.com/users")
    request = Request(name="Get Users", method="GET", url=url, headers=[], events=[])

    assert request.headers == []
    assert request.events == []


def test_request_str_representation():
    """Test string representation of Request."""
    url = Url("https://api.example.com/users")
    request = Request("Get Users", "GET", url)

    assert str(request) == "Request(name='Get Users')"


def test_request_repr_representation():
    """Test repr representation of Request."""
    url = Url("https://api.example.com/users")
    request = Request("Get Users", "GET", url, "Fetch all users")

    assert repr(request) == "Request(name='Get Users', description='Fetch all users')"

import pytest
from python_postman.config import (
    Info,
    Variables,
    AuthValues,
    Auth,
    Script,
    Event,
    Header,
    Variable,
    Param,
    Body,
    Url,
    Request,
    Item,
    Items,
    PostmanCollection,
)


def test_info():
    info = Info(
        _postman_id="123",
        name="Test Collection",
        schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        _exporter_id="456",
    )
    assert info.postman_id == "123"
    assert info.name == "Test Collection"
    assert (
        info.postman_schema
        == "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    )
    assert info.exporter_id == "456"


def test_variables():
    var = Variables(key="baseUrl", value="https://api.example.com", type="string")
    assert var.key == "baseUrl"
    assert var.value == "https://api.example.com"
    assert var.type == "string"


def test_auth():
    auth = Auth(
        type="bearer", bearer=[AuthValues(key="token", value="12345", type="string")]
    )
    assert auth.type == "bearer"
    assert auth.bearer[0].key == "token"
    assert auth.bearer[0].value == "12345"


def test_script():
    script = Script(type="text/javascript", exec=["console.log('Hello');"])
    assert script.type == "text/javascript"
    assert script.exec == ["console.log('Hello');"]


def test_event():
    event = Event(
        listen="test",
        script=Script(type="text/javascript", exec=["console.log('Test');"]),
    )
    assert event.listen == "test"
    assert event.script.type == "text/javascript"
    assert event.script.exec == ["console.log('Test');"]


def test_url():
    url = Url(
        raw="https://api.example.com/users",
        protocol="https",
        host=["api", "example", "com"],
        path=["users"],
    )
    assert url.raw == "https://api.example.com/users"
    assert url.protocol == "https"
    assert url.host == ["api", "example", "com"]
    assert url.path == ["users"]


def test_request():
    request = Request(
        method="GET",
        header=[Header(key="Content-Type", value="application/json")],
        url=Url(raw="https://api.example.com/users"),
    )
    assert request.method == "GET"
    assert len(request.headers) > 0, "Headers list is empty"
    assert request.headers[0].key == "Content-Type"
    assert request.headers[0].value == "application/json"
    assert request.url.raw == "https://api.example.com/users"


def test_item():
    item = Item(
        name="Get Users",
        request=Request(method="GET", url=Url(raw="https://api.example.com/users")),
    )
    assert item.name == "Get Users"
    assert item.request.method == "GET"
    assert item.request.url.raw == "https://api.example.com/users"


def test_items():
    items = Items(
        [
            Item(
                name="Folder 1",
                item=[
                    Item(
                        name="Request 1",
                        request=Request(
                            method="GET", url=Url(raw="https://api.example.com/users")
                        ),
                    )
                ],
            ),
            Item(
                name="Request 2",
                request=Request(
                    method="POST", url=Url(raw="https://api.example.com/users")
                ),
            ),
        ]
    )
    assert len(items.requests) == 2
    assert items.requests[0].name == "Request 1"
    assert items.requests[1].name == "Request 2"


def test_postman_collection():
    collection = PostmanCollection(
        info=Info(name="Test Collection"),
        item=[
            Item(
                name="Folder 1",
                item=[
                    Item(
                        name="Request 1",
                        request=Request(
                            method="GET", url=Url(raw="https://api.example.com/users")
                        ),
                    )
                ],
            ),
            Item(
                name="Request 2",
                request=Request(
                    method="POST", url=Url(raw="https://api.example.com/users")
                ),
            ),
        ],
        variable=[
            Variables(key="baseUrl", value="https://api.example.com", type="string")
        ],
    )
    assert collection.info.name == "Test Collection"
    assert len(collection.folders.items) == 2
    assert len(collection.requests) == 2
    assert collection.variables[0].key == "baseUrl"

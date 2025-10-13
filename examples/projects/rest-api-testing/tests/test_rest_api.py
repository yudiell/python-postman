"""Pytest tests for REST API collection."""

import pytest
from postman_collection_runner import PostmanCollectionRunner

@pytest.fixture
def runner():
    return PostmanCollectionRunner()

@pytest.fixture
def collection(runner):
    return runner.load_collection("collections/rest-api.json")

@pytest.fixture
def environment(runner):
    return runner.load_environment("environments/dev.json")

def test_collection_executes(runner, collection, environment):
    """Test that the collection executes successfully."""
    results = runner.execute(collection, environment=environment)
    assert results.total_requests > 0

def test_all_requests_succeed(runner, collection, environment):
    """Test that all requests succeed."""
    results = runner.execute(collection, environment=environment)
    assert results.failed_requests == 0, f"{results.failed_requests} requests failed"

def test_get_users_request(runner, collection, environment):
    """Test the Get All Users request."""
    results = runner.execute(collection, environment=environment)
    
    get_users = next(
        (r for r in results.request_results if r.request_name == "Get All Users"),
        None
    )
    
    assert get_users is not None
    assert get_users.success
    assert get_users.response.status_code == 200

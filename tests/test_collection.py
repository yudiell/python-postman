"""Tests for Collection class."""

import pytest
from python_postman.models import (
    Collection,
    CollectionInfo,
    Variable,
    Auth,
    Event,
    Request,
    Folder,
    Url,
    ValidationResult,
)


class TestCollection:
    """Test cases for Collection class."""

    def test_collection_init_minimal(self):
        """Test Collection initialization with minimal required data."""
        info = CollectionInfo(name="Test Collection")
        collection = Collection(info=info)

        assert collection.info == info
        assert collection.items == []
        assert collection.variables == []
        assert collection.auth is None
        assert collection.events == []

    def test_get_all_requests_empty_collection(self):
        """Test get_all_requests with empty collection."""
        info = CollectionInfo(name="Empty Collection")
        collection = Collection(info=info)

        requests = list(collection.get_all_requests())

        assert len(requests) == 0

    def test_get_all_requests_with_direct_requests(self):
        """Test get_all_requests with requests directly in collection."""
        info = CollectionInfo(name="Test Collection")

        url1 = Url(raw="https://api.example.com/test1")
        url2 = Url(raw="https://api.example.com/test2")
        request1 = Request(name="Request 1", method="GET", url=url1)
        request2 = Request(name="Request 2", method="POST", url=url2)

        collection = Collection(info=info, items=[request1, request2])

        requests = list(collection.get_all_requests())

        assert len(requests) == 2
        assert requests[0] == request1
        assert requests[1] == request2

    def test_get_request_by_name_found(self):
        """Test get_request_by_name when request exists."""
        info = CollectionInfo(name="Test Collection")

        url1 = Url(raw="https://api.example.com/test1")
        url2 = Url(raw="https://api.example.com/test2")
        request1 = Request(name="Request 1", method="GET", url=url1)
        request2 = Request(name="Request 2", method="POST", url=url2)

        folder = Folder(name="Test Folder", items=[request2])
        collection = Collection(info=info, items=[request1, folder])

        found_request = collection.get_request_by_name("Request 2")

        assert found_request == request2

    def test_get_request_by_name_not_found(self):
        """Test get_request_by_name when request doesn't exist."""
        info = CollectionInfo(name="Test Collection")

        url1 = Url(raw="https://api.example.com/test1")
        request1 = Request(name="Request 1", method="GET", url=url1)

        collection = Collection(info=info, items=[request1])

        found_request = collection.get_request_by_name("Nonexistent Request")

        assert found_request is None

    def test_get_folder_by_name_found_direct(self):
        """Test get_folder_by_name when folder is direct child."""
        info = CollectionInfo(name="Test Collection")

        folder1 = Folder(name="Folder 1", items=[])
        folder2 = Folder(name="Folder 2", items=[])

        collection = Collection(info=info, items=[folder1, folder2])

        found_folder = collection.get_folder_by_name("Folder 2")

        assert found_folder == folder2

    def test_get_folder_by_name_not_found(self):
        """Test get_folder_by_name when folder doesn't exist."""
        info = CollectionInfo(name="Test Collection")

        folder1 = Folder(name="Folder 1", items=[])
        collection = Collection(info=info, items=[folder1])

        found_folder = collection.get_folder_by_name("Nonexistent Folder")

        assert found_folder is None


class TestValidationResult:
    """Test cases for ValidationResult class."""

    def test_validation_result_init_valid(self):
        """Test ValidationResult initialization for valid result."""
        result = ValidationResult()

        assert result.is_valid is True
        assert result.errors == []

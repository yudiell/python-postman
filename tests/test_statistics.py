"""
Tests for collection statistics functionality.
"""

import json
import pytest
from python_postman.models.collection import Collection
from python_postman.models.collection_info import CollectionInfo
from python_postman.models.request import Request
from python_postman.models.folder import Folder
from python_postman.models.url import Url
from python_postman.models.auth import Auth
from python_postman.statistics.collector import CollectionStatistics


@pytest.fixture
def simple_collection():
    """Create a simple collection with a few requests."""
    info = CollectionInfo(
        name="Test Collection",
        schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    )
    
    requests = [
        Request(name="Get Users", method="GET", url=Url.from_string("https://api.example.com/users")),
        Request(name="Create User", method="POST", url=Url.from_string("https://api.example.com/users")),
        Request(name="Update User", method="PUT", url=Url.from_string("https://api.example.com/users/1")),
    ]
    
    return Collection(info=info, items=requests)


@pytest.fixture
def nested_collection():
    """Create a collection with nested folders."""
    info = CollectionInfo(
        name="Nested Collection",
        schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    )
    
    # Create requests with different methods
    get_req = Request(name="Get", method="GET", url=Url.from_string("https://api.example.com/data"))
    post_req = Request(name="Post", method="POST", url=Url.from_string("https://api.example.com/data"))
    put_req = Request(name="Put", method="PUT", url=Url.from_string("https://api.example.com/data"))
    delete_req = Request(name="Delete", method="DELETE", url=Url.from_string("https://api.example.com/data"))
    
    # Create nested folder structure
    inner_folder = Folder(name="Inner Folder", items=[put_req, delete_req])
    outer_folder = Folder(name="Outer Folder", items=[post_req, inner_folder])
    
    return Collection(info=info, items=[get_req, outer_folder])


@pytest.fixture
def collection_with_auth():
    """Create a collection with various authentication types."""
    from python_postman.models.auth import AuthParameter
    
    info = CollectionInfo(
        name="Auth Collection",
        schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
    )
    
    # Requests with different auth types
    bearer_req = Request(
        name="Bearer Request",
        method="GET",
        url=Url.from_string("https://api.example.com/secure"),
        auth=Auth(type="bearer", parameters=[AuthParameter(key="token", value="abc123")])
    )
    
    basic_req = Request(
        name="Basic Request",
        method="GET",
        url=Url.from_string("https://api.example.com/basic"),
        auth=Auth(type="basic", parameters=[AuthParameter(key="username", value="user")])
    )
    
    no_auth_req = Request(
        name="No Auth Request",
        method="GET",
        url=Url.from_string("https://api.example.com/public")
    )
    
    return Collection(info=info, items=[bearer_req, basic_req, no_auth_req])


class TestCollectionStatistics:
    """Test suite for CollectionStatistics class."""

    def test_initialization(self, simple_collection):
        """Test CollectionStatistics initialization."""
        stats = CollectionStatistics(simple_collection)
        assert stats.collection == simple_collection
        assert stats._cache is None

    def test_count_requests_simple(self, simple_collection):
        """Test counting requests in a simple collection."""
        stats = CollectionStatistics(simple_collection)
        assert stats.count_requests() == 3

    def test_count_requests_nested(self, nested_collection):
        """Test counting requests in a nested collection."""
        stats = CollectionStatistics(nested_collection)
        assert stats.count_requests() == 4  # 1 top-level + 3 in folders

    def test_count_requests_empty(self):
        """Test counting requests in an empty collection."""
        info = CollectionInfo(
            name="Empty",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        collection = Collection(info=info, items=[])
        stats = CollectionStatistics(collection)
        assert stats.count_requests() == 0

    def test_count_folders_simple(self, simple_collection):
        """Test counting folders in a collection without folders."""
        stats = CollectionStatistics(simple_collection)
        assert stats.count_folders() == 0

    def test_count_folders_nested(self, nested_collection):
        """Test counting folders in a nested collection."""
        stats = CollectionStatistics(nested_collection)
        assert stats.count_folders() == 2  # Outer folder + inner folder

    def test_count_folders_deeply_nested(self):
        """Test counting folders in a deeply nested structure."""
        info = CollectionInfo(
            name="Deep",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        
        req = Request(name="Req", method="GET", url=Url.from_string("https://api.example.com"))
        folder3 = Folder(name="Level 3", items=[req])
        folder2 = Folder(name="Level 2", items=[folder3])
        folder1 = Folder(name="Level 1", items=[folder2])
        
        collection = Collection(info=info, items=[folder1])
        stats = CollectionStatistics(collection)
        assert stats.count_folders() == 3

    def test_get_max_depth_no_folders(self, simple_collection):
        """Test max depth with no folders."""
        stats = CollectionStatistics(simple_collection)
        assert stats.get_max_depth() == 0

    def test_get_max_depth_single_level(self):
        """Test max depth with single-level folders."""
        info = CollectionInfo(
            name="Single Level",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        
        req = Request(name="Req", method="GET", url=Url.from_string("https://api.example.com"))
        folder = Folder(name="Folder", items=[req])
        
        collection = Collection(info=info, items=[folder])
        stats = CollectionStatistics(collection)
        assert stats.get_max_depth() == 1

    def test_get_max_depth_nested(self, nested_collection):
        """Test max depth with nested folders."""
        stats = CollectionStatistics(nested_collection)
        assert stats.get_max_depth() == 2  # Outer folder -> Inner folder

    def test_get_max_depth_deeply_nested(self):
        """Test max depth with deeply nested structure."""
        info = CollectionInfo(
            name="Deep",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        
        req = Request(name="Req", method="GET", url=Url.from_string("https://api.example.com"))
        folder5 = Folder(name="Level 5", items=[req])
        folder4 = Folder(name="Level 4", items=[folder5])
        folder3 = Folder(name="Level 3", items=[folder4])
        folder2 = Folder(name="Level 2", items=[folder3])
        folder1 = Folder(name="Level 1", items=[folder2])
        
        collection = Collection(info=info, items=[folder1])
        stats = CollectionStatistics(collection)
        assert stats.get_max_depth() == 5

    def test_count_by_method(self, simple_collection):
        """Test counting requests by HTTP method."""
        stats = CollectionStatistics(simple_collection)
        by_method = stats.count_by_method()
        
        assert by_method["GET"] == 1
        assert by_method["POST"] == 1
        assert by_method["PUT"] == 1

    def test_count_by_method_nested(self, nested_collection):
        """Test counting by method in nested collection."""
        stats = CollectionStatistics(nested_collection)
        by_method = stats.count_by_method()
        
        assert by_method["GET"] == 1
        assert by_method["POST"] == 1
        assert by_method["PUT"] == 1
        assert by_method["DELETE"] == 1

    def test_count_by_method_empty(self):
        """Test counting by method in empty collection."""
        info = CollectionInfo(
            name="Empty",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        collection = Collection(info=info, items=[])
        stats = CollectionStatistics(collection)
        by_method = stats.count_by_method()
        
        assert by_method == {}

    def test_count_by_auth(self, collection_with_auth):
        """Test counting requests by authentication type."""
        stats = CollectionStatistics(collection_with_auth)
        by_auth = stats.count_by_auth()
        
        assert by_auth["bearer"] == 1
        assert by_auth["basic"] == 1
        assert by_auth["none"] == 1

    def test_count_by_auth_no_auth(self, simple_collection):
        """Test counting by auth when no auth is present."""
        stats = CollectionStatistics(simple_collection)
        by_auth = stats.count_by_auth()
        
        assert by_auth["none"] == 3

    def test_get_avg_requests_per_folder(self, nested_collection):
        """Test calculating average requests per folder."""
        stats = CollectionStatistics(nested_collection)
        avg = stats.get_avg_requests_per_folder()
        
        # 4 requests / 2 folders = 2.0
        assert avg == 2.0

    def test_get_avg_requests_per_folder_no_folders(self, simple_collection):
        """Test average requests per folder when there are no folders."""
        stats = CollectionStatistics(simple_collection)
        avg = stats.get_avg_requests_per_folder()
        
        assert avg == 0.0

    def test_collect_all_stats(self, nested_collection):
        """Test collecting all statistics at once."""
        stats = CollectionStatistics(nested_collection)
        data = stats.collect()
        
        assert data["total_requests"] == 4
        assert data["total_folders"] == 2
        assert data["max_nesting_depth"] == 2
        assert data["requests_by_method"]["GET"] == 1
        assert data["requests_by_method"]["POST"] == 1
        assert data["requests_by_method"]["PUT"] == 1
        assert data["requests_by_method"]["DELETE"] == 1
        assert data["avg_requests_per_folder"] == 2.0

    def test_collect_with_cache(self, simple_collection):
        """Test that collect uses cache on subsequent calls."""
        stats = CollectionStatistics(simple_collection)
        
        # First call should calculate
        data1 = stats.collect(use_cache=True)
        assert stats._cache is not None
        
        # Second call should use cache
        data2 = stats.collect(use_cache=True)
        assert data1 == data2
        assert data1 is data2  # Same object reference

    def test_collect_without_cache(self, simple_collection):
        """Test that collect can bypass cache."""
        stats = CollectionStatistics(simple_collection)
        
        # First call with cache
        data1 = stats.collect(use_cache=True)
        
        # Second call without cache
        data2 = stats.collect(use_cache=False)
        assert data1 == data2
        assert data1 is not data2  # Different object reference

    def test_clear_cache(self, simple_collection):
        """Test clearing the statistics cache."""
        stats = CollectionStatistics(simple_collection)
        
        # Collect with cache
        stats.collect(use_cache=True)
        assert stats._cache is not None
        
        # Clear cache
        stats.clear_cache()
        assert stats._cache is None

    def test_to_json(self, simple_collection):
        """Test exporting statistics to JSON."""
        stats = CollectionStatistics(simple_collection)
        json_output = stats.to_json()
        
        # Verify it's valid JSON
        data = json.loads(json_output)
        assert data["total_requests"] == 3
        assert data["total_folders"] == 0
        assert "requests_by_method" in data
        assert "requests_by_auth" in data

    def test_to_json_custom_indent(self, simple_collection):
        """Test JSON export with custom indentation."""
        stats = CollectionStatistics(simple_collection)
        json_output = stats.to_json(indent=4)
        
        # Verify indentation
        assert "    " in json_output  # 4 spaces
        data = json.loads(json_output)
        assert data["total_requests"] == 3

    def test_to_csv(self, simple_collection):
        """Test exporting statistics to CSV."""
        stats = CollectionStatistics(simple_collection)
        csv_output = stats.to_csv()
        
        # Verify CSV structure
        lines = csv_output.strip().split("\n")
        assert len(lines) > 0
        
        # Check for expected headers and data
        assert "Metric,Value" in csv_output
        assert "Total Requests,3" in csv_output
        assert "Total Folders,0" in csv_output
        assert "HTTP Method,Count" in csv_output
        assert "Auth Type,Count" in csv_output

    def test_to_csv_with_methods(self, nested_collection):
        """Test CSV export includes method breakdown."""
        stats = CollectionStatistics(nested_collection)
        csv_output = stats.to_csv()
        
        # Verify method counts are present
        assert "GET,1" in csv_output
        assert "POST,1" in csv_output
        assert "PUT,1" in csv_output
        assert "DELETE,1" in csv_output

    def test_collection_get_statistics_method(self, simple_collection):
        """Test that Collection.get_statistics() returns CollectionStatistics."""
        stats = simple_collection.get_statistics()
        
        assert isinstance(stats, CollectionStatistics)
        assert stats.collection == simple_collection

    def test_statistics_with_mixed_structure(self):
        """Test statistics with a complex mixed structure."""
        info = CollectionInfo(
            name="Mixed",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        
        # Top-level requests
        req1 = Request(name="Top 1", method="GET", url=Url.from_string("https://api.example.com"))
        req2 = Request(name="Top 2", method="POST", url=Url.from_string("https://api.example.com"))
        
        # Folder with requests
        req3 = Request(name="Folder 1 Req", method="PUT", url=Url.from_string("https://api.example.com"))
        folder1 = Folder(name="Folder 1", items=[req3])
        
        # Nested folders
        req4 = Request(name="Nested Req", method="DELETE", url=Url.from_string("https://api.example.com"))
        inner_folder = Folder(name="Inner", items=[req4])
        outer_folder = Folder(name="Outer", items=[inner_folder])
        
        collection = Collection(info=info, items=[req1, req2, folder1, outer_folder])
        stats = CollectionStatistics(collection)
        
        data = stats.collect()
        assert data["total_requests"] == 4
        assert data["total_folders"] == 3
        assert data["max_nesting_depth"] == 2

    def test_repr(self, simple_collection):
        """Test string representation of CollectionStatistics."""
        stats = CollectionStatistics(simple_collection)
        repr_str = repr(stats)
        
        assert "CollectionStatistics" in repr_str
        assert "Test Collection" in repr_str

    def test_statistics_performance_large_collection(self):
        """Test statistics calculation on a larger collection."""
        info = CollectionInfo(
            name="Large Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        
        # Create 100 requests
        requests = []
        for i in range(100):
            method = ["GET", "POST", "PUT", "DELETE"][i % 4]
            req = Request(
                name=f"Request {i}",
                method=method,
                url=Url.from_string(f"https://api.example.com/resource/{i}")
            )
            requests.append(req)
        
        collection = Collection(info=info, items=requests)
        stats = CollectionStatistics(collection)
        
        data = stats.collect()
        assert data["total_requests"] == 100
        assert data["requests_by_method"]["GET"] == 25
        assert data["requests_by_method"]["POST"] == 25
        assert data["requests_by_method"]["PUT"] == 25
        assert data["requests_by_method"]["DELETE"] == 25

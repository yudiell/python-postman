"""
Tests for search and filtering functionality.
"""

import pytest
from python_postman.models.collection import Collection
from python_postman.models.request import Request
from python_postman.models.folder import Folder
from python_postman.models.url import Url
from python_postman.models.auth import Auth, AuthParameter
from python_postman.models.event import Event
from python_postman.models.collection_info import CollectionInfo
from python_postman.search import SearchResult, RequestQuery


@pytest.fixture
def sample_collection():
    """Create a sample collection for testing."""
    # Create requests
    get_users = Request(
        name="Get Users",
        method="GET",
        url=Url.from_string("https://api.example.com/users"),
    )
    
    post_user = Request(
        name="Create User",
        method="POST",
        url=Url.from_string("https://api.example.com/users"),
        auth=Auth(type="bearer", parameters=[AuthParameter(key="token", value="{{token}}")]),
    )
    
    get_user_by_id = Request(
        name="Get User by ID",
        method="GET",
        url=Url.from_string("https://api.example.com/users/:id"),
    )
    
    delete_user = Request(
        name="Delete User",
        method="DELETE",
        url=Url.from_string("https://api.example.com/users/:id"),
        auth=Auth(type="bearer", parameters=[AuthParameter(key="token", value="{{token}}")]),
    )
    
    # Add test script to one request
    get_users.events = [
        Event(listen="test", script={"exec": ["pm.test('Status is 200', function() {", "  pm.response.to.have.status(200);", "});"]})
    ]
    
    # Create requests for different host
    get_products = Request(
        name="Get Products",
        method="GET",
        url=Url.from_string("https://api.shop.com/products"),
    )
    
    # Create folders
    users_folder = Folder(
        name="Users",
        items=[get_users, post_user, get_user_by_id, delete_user],
    )
    
    products_folder = Folder(
        name="Products",
        items=[get_products],
    )
    
    # Create nested folder
    admin_get_users = Request(
        name="Admin Get Users",
        method="GET",
        url=Url.from_string("https://api.example.com/admin/users"),
        auth=Auth(type="basic", parameters=[AuthParameter(key="username", value="admin")]),
    )
    
    admin_folder = Folder(
        name="Admin",
        items=[admin_get_users],
    )
    
    nested_folder = Folder(
        name="API",
        items=[users_folder, admin_folder],
    )
    
    # Create collection
    info = CollectionInfo(
        name="Test Collection",
        schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    )
    
    collection = Collection(
        info=info,
        items=[nested_folder, products_folder],
    )
    
    return collection


class TestSearchResult:
    """Tests for SearchResult class."""
    
    def test_search_result_creation(self):
        """Test creating a SearchResult."""
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://example.com"),
        )
        path = ["Folder1", "Folder2", "Test Request"]
        
        result = SearchResult(request, path)
        
        assert result.request == request
        assert result.path == path
        assert result.full_path == "Folder1 > Folder2 > Test Request"
    
    def test_search_result_repr(self):
        """Test SearchResult string representation."""
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://example.com"),
        )
        path = ["Folder", "Test Request"]
        
        result = SearchResult(request, path)
        
        assert "Test Request" in repr(result)
        assert "Folder > Test Request" in repr(result)
    
    def test_search_result_equality(self):
        """Test SearchResult equality."""
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://example.com"),
        )
        path = ["Folder", "Test Request"]
        
        result1 = SearchResult(request, path)
        result2 = SearchResult(request, path)
        
        assert result1 == result2


class TestRequestQuery:
    """Tests for RequestQuery class."""
    
    def test_query_creation(self, sample_collection):
        """Test creating a RequestQuery."""
        query = RequestQuery(sample_collection)
        
        assert query.collection == sample_collection
        assert query.filters == []
        assert query._folder_filter is None
    
    def test_by_method_filter(self, sample_collection):
        """Test filtering by HTTP method."""
        results = sample_collection.search().by_method("GET").execute()
        
        assert len(results) == 4  # Get Users, Get User by ID, Admin Get Users, Get Products
        for result in results:
            assert result.request.method == "GET"
    
    def test_by_method_case_insensitive(self, sample_collection):
        """Test that method filter is case-insensitive."""
        results_upper = sample_collection.search().by_method("POST").execute()
        results_lower = sample_collection.search().by_method("post").execute()
        
        assert len(results_upper) == len(results_lower) == 1
        assert results_upper[0].request.name == "Create User"
    
    def test_by_url_pattern_filter(self, sample_collection):
        """Test filtering by URL pattern."""
        # Find all requests with /users in the path
        results = sample_collection.search().by_url_pattern(r"/users").execute()
        
        assert len(results) == 5  # All user-related endpoints
        for result in results:
            assert "/users" in result.request.url.to_string()
    
    def test_by_url_pattern_with_regex(self, sample_collection):
        """Test filtering with complex regex pattern."""
        # Find requests with path parameters (contains :id)
        results = sample_collection.search().by_url_pattern(r"/:id").execute()
        
        assert len(results) == 2  # Get User by ID, Delete User
    
    def test_by_url_pattern_invalid_regex(self, sample_collection):
        """Test that invalid regex raises ValueError."""
        with pytest.raises(ValueError, match="Invalid regex pattern"):
            sample_collection.search().by_url_pattern(r"[invalid(").execute()
    
    def test_by_host_filter(self, sample_collection):
        """Test filtering by host."""
        results = sample_collection.search().by_host("api.example.com").execute()
        
        assert len(results) == 5  # All requests except Get Products
        for result in results:
            assert "api.example.com" in result.request.url.to_string()
    
    def test_by_host_different_host(self, sample_collection):
        """Test filtering by different host."""
        results = sample_collection.search().by_host("api.shop.com").execute()
        
        assert len(results) == 1
        assert results[0].request.name == "Get Products"
    
    def test_by_auth_type_filter(self, sample_collection):
        """Test filtering by authentication type."""
        results = sample_collection.search().by_auth_type("bearer").execute()
        
        assert len(results) == 2  # Create User, Delete User
        for result in results:
            assert result.request.auth.type == "bearer"
    
    def test_by_auth_type_basic(self, sample_collection):
        """Test filtering by basic auth."""
        results = sample_collection.search().by_auth_type("basic").execute()
        
        assert len(results) == 1
        assert results[0].request.name == "Admin Get Users"
    
    def test_has_scripts_any(self, sample_collection):
        """Test filtering by presence of any scripts."""
        results = sample_collection.search().has_scripts().execute()
        
        assert len(results) == 1
        assert results[0].request.name == "Get Users"
    
    def test_has_scripts_specific_type(self, sample_collection):
        """Test filtering by specific script type."""
        results = sample_collection.search().has_scripts("test").execute()
        
        assert len(results) == 1
        assert results[0].request.name == "Get Users"
    
    def test_has_scripts_prerequest(self, sample_collection):
        """Test filtering by prerequest scripts."""
        results = sample_collection.search().has_scripts("prerequest").execute()
        
        assert len(results) == 0  # No prerequest scripts in sample
    
    def test_in_folder_filter(self, sample_collection):
        """Test filtering by folder."""
        results = sample_collection.search().in_folder("Users").execute()
        
        assert len(results) == 4  # All requests in Users folder
        for result in results:
            assert "Users" in result.path
    
    def test_in_folder_nested(self, sample_collection):
        """Test filtering by nested folder."""
        results = sample_collection.search().in_folder("Admin").execute()
        
        assert len(results) == 1
        assert results[0].request.name == "Admin Get Users"
    
    def test_combined_filters(self, sample_collection):
        """Test combining multiple filters."""
        results = (
            sample_collection.search()
            .by_method("GET")
            .by_host("api.example.com")
            .in_folder("Users")
            .execute()
        )
        
        assert len(results) == 2  # Get Users, Get User by ID
        for result in results:
            assert result.request.method == "GET"
            assert "api.example.com" in result.request.url.to_string()
            assert "Users" in result.path
    
    def test_complex_query(self, sample_collection):
        """Test complex query with multiple filters."""
        results = (
            sample_collection.search()
            .by_method("GET")
            .by_url_pattern(r"/users")
            .by_host("api.example.com")
            .execute()
        )
        
        assert len(results) == 3  # Get Users, Get User by ID, Admin Get Users
    
    def test_execute_returns_list(self, sample_collection):
        """Test that execute returns a list."""
        results = sample_collection.search().by_method("GET").execute()
        
        assert isinstance(results, list)
        assert all(isinstance(r, SearchResult) for r in results)
    
    def test_execute_iter_returns_iterator(self, sample_collection):
        """Test that execute_iter returns an iterator."""
        results_iter = sample_collection.search().by_method("GET").execute_iter()
        
        # Convert to list to verify
        results = list(results_iter)
        assert len(results) == 4
        assert all(isinstance(r, SearchResult) for r in results)
    
    def test_no_filters_returns_all(self, sample_collection):
        """Test that query with no filters returns all requests."""
        results = sample_collection.search().execute()
        
        # Should return all 6 requests
        assert len(results) == 6
    
    def test_search_result_paths(self, sample_collection):
        """Test that search results include correct paths."""
        results = sample_collection.search().in_folder("Users").execute()
        
        for result in results:
            # Path should be: API > Users > Request Name
            assert len(result.path) == 3
            assert result.path[0] == "API"
            assert result.path[1] == "Users"
    
    def test_method_chaining(self, sample_collection):
        """Test that methods return self for chaining."""
        query = sample_collection.search()
        
        assert query.by_method("GET") is query
        assert query.by_host("api.example.com") is query
        assert query.by_auth_type("bearer") is query
        assert query.has_scripts() is query
        assert query.in_folder("Users") is query


class TestCollectionSearchMethod:
    """Tests for Collection.search() method."""
    
    def test_collection_has_search_method(self, sample_collection):
        """Test that Collection has search method."""
        assert hasattr(sample_collection, "search")
        assert callable(sample_collection.search)
    
    def test_search_returns_query(self, sample_collection):
        """Test that search() returns RequestQuery."""
        query = sample_collection.search()
        
        assert isinstance(query, RequestQuery)
        assert query.collection == sample_collection
    
    def test_search_integration(self, sample_collection):
        """Test full integration of search functionality."""
        # Use the search method from collection
        results = sample_collection.search().by_method("POST").execute()
        
        assert len(results) == 1
        assert results[0].request.name == "Create User"


class TestEdgeCases:
    """Tests for edge cases."""
    
    def test_empty_collection(self):
        """Test searching in empty collection."""
        info = CollectionInfo(
            name="Empty Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        )
        collection = Collection(info=info, items=[])
        
        results = collection.search().by_method("GET").execute()
        
        assert results == []
    
    def test_no_matching_results(self, sample_collection):
        """Test query with no matching results."""
        results = sample_collection.search().by_method("PATCH").execute()
        
        assert results == []
    
    def test_filter_by_nonexistent_folder(self, sample_collection):
        """Test filtering by folder that doesn't exist."""
        results = sample_collection.search().in_folder("NonExistent").execute()
        
        assert results == []
    
    def test_filter_by_nonexistent_auth_type(self, sample_collection):
        """Test filtering by auth type that doesn't exist."""
        results = sample_collection.search().by_auth_type("oauth2").execute()
        
        assert results == []
    
    def test_requests_without_auth(self, sample_collection):
        """Test that requests without auth are not matched by auth filter."""
        # Get Users has no auth
        results = sample_collection.search().by_auth_type("bearer").execute()
        
        # Should not include Get Users
        assert all(r.request.name != "Get Users" for r in results)

"""
Tests for Item class clarity improvements (REQ-005).
"""

import pytest
from python_postman.models.item import Item
from python_postman.models.request import Request
from python_postman.models.folder import Folder
from python_postman.models.url import Url


class TestItemDirectInstantiation:
    """Test that Item cannot be instantiated directly."""

    def test_item_direct_instantiation_raises_error(self):
        """Test that attempting to instantiate Item directly raises TypeError."""
        with pytest.raises(TypeError) as exc_info:
            Item(name="Test Item")
        
        error_message = str(exc_info.value)
        # Python's ABC raises its own error about abstract methods
        # Our custom error would only show if ABC didn't catch it first
        assert "abstract" in error_message.lower()
        assert "Item" in error_message

    def test_item_has_helpful_error_guidance_in_docstring(self):
        """Test that Item class docstring provides helpful guidance."""
        docstring = Item.__doc__
        assert "should NOT be instantiated directly" in docstring
        assert "Request" in docstring
        assert "Folder" in docstring
        assert "create_request" in docstring
        assert "create_folder" in docstring

    def test_request_instantiation_works(self):
        """Test that Request can be instantiated normally."""
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com/test")
        )
        assert request.name == "Test Request"
        assert request.method == "GET"

    def test_folder_instantiation_works(self):
        """Test that Folder can be instantiated normally."""
        folder = Folder(
            name="Test Folder",
            items=[]
        )
        assert folder.name == "Test Folder"
        assert folder.items == []


class TestItemFactoryMethods:
    """Test Item factory methods."""

    def test_create_request_basic(self):
        """Test creating a basic request using factory method."""
        request = Item.create_request(
            name="Get Users",
            method="GET",
            url="https://api.example.com/users"
        )
        
        assert isinstance(request, Request)
        assert request.name == "Get Users"
        assert request.method == "GET"
        assert request.url.raw == "https://api.example.com/users"
        assert request.description is None
        assert request.headers == []
        assert request.body is None
        assert request.auth is None

    def test_create_request_with_description(self):
        """Test creating a request with description using factory method."""
        request = Item.create_request(
            name="Create User",
            method="POST",
            url="https://api.example.com/users",
            description="Creates a new user in the system"
        )
        
        assert isinstance(request, Request)
        assert request.name == "Create User"
        assert request.method == "POST"
        assert request.description == "Creates a new user in the system"

    def test_create_request_with_all_parameters(self):
        """Test creating a request with all parameters using factory method."""
        from python_postman.models.header import Header
        from python_postman.models.body import Body
        from python_postman.models.auth import Auth
        
        headers = [Header(key="Content-Type", value="application/json")]
        body = Body(mode="raw", raw='{"name": "John"}')
        auth = Auth(type="bearer")
        
        request = Item.create_request(
            name="Create User",
            method="POST",
            url="https://api.example.com/users",
            description="Creates a new user",
            headers=headers,
            body=body,
            auth=auth
        )
        
        assert isinstance(request, Request)
        assert request.name == "Create User"
        assert request.headers == headers
        assert request.body == body
        assert request.auth == auth

    def test_create_folder_basic(self):
        """Test creating a basic folder using factory method."""
        folder = Item.create_folder(
            name="User Endpoints",
            description="All user-related API endpoints"
        )
        
        assert isinstance(folder, Folder)
        assert folder.name == "User Endpoints"
        assert folder.description == "All user-related API endpoints"
        assert folder.items == []
        assert folder.auth is None

    def test_create_folder_with_items(self):
        """Test creating a folder with items using factory method."""
        request1 = Item.create_request(
            name="Get Users",
            method="GET",
            url="https://api.example.com/users"
        )
        request2 = Item.create_request(
            name="Create User",
            method="POST",
            url="https://api.example.com/users"
        )
        
        folder = Item.create_folder(
            name="User Endpoints",
            items=[request1, request2]
        )
        
        assert isinstance(folder, Folder)
        assert folder.name == "User Endpoints"
        assert len(folder.items) == 2
        assert folder.items[0] == request1
        assert folder.items[1] == request2

    def test_create_folder_with_all_parameters(self):
        """Test creating a folder with all parameters using factory method."""
        from python_postman.models.auth import Auth
        from python_postman.models.variable import Variable
        
        auth = Auth(type="bearer")
        variables = [Variable(key="base_url", value="https://api.example.com")]
        
        folder = Item.create_folder(
            name="User Endpoints",
            description="User API endpoints",
            auth=auth,
            variables=variables
        )
        
        assert isinstance(folder, Folder)
        assert folder.name == "User Endpoints"
        assert folder.auth == auth
        assert folder.variables == variables

    def test_factory_methods_return_correct_types(self):
        """Test that factory methods return instances of correct types."""
        request = Item.create_request(
            name="Test",
            method="GET",
            url="https://example.com"
        )
        folder = Item.create_folder(name="Test Folder")
        
        # Verify they are instances of Item (through inheritance)
        assert isinstance(request, Item)
        assert isinstance(folder, Item)
        
        # Verify they are instances of their specific types
        assert isinstance(request, Request)
        assert isinstance(folder, Folder)
        
        # Verify they are not instances of each other's types
        assert not isinstance(request, Folder)
        assert not isinstance(folder, Request)


class TestItemDocumentation:
    """Test that Item class has proper documentation."""

    def test_item_class_has_docstring(self):
        """Test that Item class has a comprehensive docstring."""
        assert Item.__doc__ is not None
        assert "abstract base class" in Item.__doc__.lower()
        assert "Request" in Item.__doc__
        assert "Folder" in Item.__doc__
        assert "create_request" in Item.__doc__
        assert "create_folder" in Item.__doc__

    def test_item_init_has_docstring(self):
        """Test that Item.__init__ has proper documentation."""
        assert Item.__init__.__doc__ is not None
        assert "TypeError" in Item.__init__.__doc__

    def test_create_request_has_docstring(self):
        """Test that create_request factory method has documentation."""
        assert Item.create_request.__doc__ is not None
        assert "Factory method" in Item.create_request.__doc__
        assert "Request" in Item.create_request.__doc__

    def test_create_folder_has_docstring(self):
        """Test that create_folder factory method has documentation."""
        assert Item.create_folder.__doc__ is not None
        assert "Factory method" in Item.create_folder.__doc__
        assert "Folder" in Item.create_folder.__doc__

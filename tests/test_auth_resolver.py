"""
Tests for authentication inheritance resolution.
"""

import pytest
from python_postman.models.auth import Auth, AuthParameter
from python_postman.models.request import Request
from python_postman.models.folder import Folder
from python_postman.models.collection import Collection
from python_postman.models.collection_info import CollectionInfo
from python_postman.models.url import Url
from python_postman.introspection import AuthResolver, AuthSource, ResolvedAuth


class TestAuthSource:
    """Test AuthSource enum."""

    def test_auth_source_values(self):
        """Test that AuthSource has expected values."""
        assert AuthSource.REQUEST.value == "request"
        assert AuthSource.FOLDER.value == "folder"
        assert AuthSource.COLLECTION.value == "collection"
        assert AuthSource.NONE.value == "none"


class TestResolvedAuth:
    """Test ResolvedAuth class."""

    def test_resolved_auth_initialization(self):
        """Test ResolvedAuth initialization."""
        auth = Auth(type="bearer", parameters=[AuthParameter("token", "test-token")])
        resolved = ResolvedAuth(auth, AuthSource.REQUEST, ["MyRequest"])

        assert resolved.auth == auth
        assert resolved.source == AuthSource.REQUEST
        assert resolved.path == ["MyRequest"]

    def test_resolved_auth_repr(self):
        """Test ResolvedAuth string representation."""
        auth = Auth(type="bearer", parameters=[AuthParameter("token", "test-token")])
        resolved = ResolvedAuth(auth, AuthSource.REQUEST, ["MyRequest"])

        repr_str = repr(resolved)
        assert "ResolvedAuth" in repr_str
        assert "request" in repr_str
        assert "bearer" in repr_str
        assert "MyRequest" in repr_str

    def test_resolved_auth_no_auth(self):
        """Test ResolvedAuth with no authentication."""
        resolved = ResolvedAuth(None, AuthSource.NONE, ["MyRequest"])

        assert resolved.auth is None
        assert resolved.source == AuthSource.NONE
        assert "None" in repr(resolved)

    def test_resolved_auth_equality(self):
        """Test ResolvedAuth equality comparison."""
        auth1 = Auth(type="bearer", parameters=[AuthParameter("token", "test-token")])
        auth2 = Auth(type="bearer", parameters=[AuthParameter("token", "test-token")])

        resolved1 = ResolvedAuth(auth1, AuthSource.REQUEST, ["MyRequest"])
        resolved2 = ResolvedAuth(auth2, AuthSource.REQUEST, ["MyRequest"])
        resolved3 = ResolvedAuth(auth1, AuthSource.FOLDER, ["MyRequest"])

        assert resolved1 == resolved2
        assert resolved1 != resolved3
        assert resolved1 != "not a ResolvedAuth"


class TestAuthResolver:
    """Test AuthResolver class."""

    def test_resolve_request_level_auth(self):
        """Test resolving authentication at request level."""
        # Create request with auth
        request_auth = Auth(type="bearer", parameters=[AuthParameter("token", "request-token")])
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            auth=request_auth
        )

        # Resolve auth
        resolved = AuthResolver.resolve_auth(request)

        assert resolved.auth == request_auth
        assert resolved.source == AuthSource.REQUEST
        assert resolved.path == ["Test Request"]

    def test_resolve_folder_level_auth(self):
        """Test resolving authentication at folder level."""
        # Create folder with auth
        folder_auth = Auth(type="apikey", parameters=[
            AuthParameter("key", "X-API-Key"),
            AuthParameter("value", "folder-key")
        ])
        folder = Folder(
            name="Test Folder",
            items=[],
            auth=folder_auth
        )

        # Create request without auth
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        # Resolve auth
        resolved = AuthResolver.resolve_auth(request, parent_folder=folder)

        assert resolved.auth == folder_auth
        assert resolved.source == AuthSource.FOLDER
        assert resolved.path == ["Test Folder", "Test Request"]

    def test_resolve_collection_level_auth(self):
        """Test resolving authentication at collection level."""
        # Create collection with auth
        collection_auth = Auth(type="basic", parameters=[
            AuthParameter("username", "user"),
            AuthParameter("password", "pass")
        ])
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            ),
            auth=collection_auth
        )

        # Create request without auth
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        # Resolve auth
        resolved = AuthResolver.resolve_auth(request, collection=collection)

        assert resolved.auth == collection_auth
        assert resolved.source == AuthSource.COLLECTION
        assert resolved.path == ["Test Collection", "Test Request"]

    def test_resolve_no_auth(self):
        """Test resolving when no authentication is defined."""
        # Create request without auth
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        # Resolve auth
        resolved = AuthResolver.resolve_auth(request)

        assert resolved.auth is None
        assert resolved.source == AuthSource.NONE
        assert resolved.path == ["Test Request"]

    def test_resolve_request_overrides_folder(self):
        """Test that request-level auth overrides folder-level auth."""
        # Create folder with auth
        folder_auth = Auth(type="apikey", parameters=[
            AuthParameter("key", "X-API-Key"),
            AuthParameter("value", "folder-key")
        ])
        folder = Folder(
            name="Test Folder",
            items=[],
            auth=folder_auth
        )

        # Create request with different auth
        request_auth = Auth(type="bearer", parameters=[AuthParameter("token", "request-token")])
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            auth=request_auth
        )

        # Resolve auth
        resolved = AuthResolver.resolve_auth(request, parent_folder=folder)

        assert resolved.auth == request_auth
        assert resolved.source == AuthSource.REQUEST
        assert resolved.path == ["Test Request"]

    def test_resolve_folder_overrides_collection(self):
        """Test that folder-level auth overrides collection-level auth."""
        # Create collection with auth
        collection_auth = Auth(type="basic", parameters=[
            AuthParameter("username", "user"),
            AuthParameter("password", "pass")
        ])
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            ),
            auth=collection_auth
        )

        # Create folder with different auth
        folder_auth = Auth(type="bearer", parameters=[AuthParameter("token", "folder-token")])
        folder = Folder(
            name="Test Folder",
            items=[],
            auth=folder_auth
        )

        # Create request without auth
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        # Resolve auth
        resolved = AuthResolver.resolve_auth(request, parent_folder=folder, collection=collection)

        assert resolved.auth == folder_auth
        assert resolved.source == AuthSource.FOLDER
        assert resolved.path == ["Test Folder", "Test Request"]

    def test_resolve_nested_folders(self):
        """Test resolving authentication through nested folder hierarchy."""
        # Create parent folder with auth
        parent_auth = Auth(type="bearer", parameters=[AuthParameter("token", "parent-token")])
        parent_folder = Folder(
            name="Parent Folder",
            items=[],
            auth=parent_auth
        )

        # Create child folder without auth
        child_folder = Folder(
            name="Child Folder",
            items=[]
        )
        child_folder._parent_folder = parent_folder

        # Create request without auth
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        # Resolve auth
        resolved = AuthResolver.resolve_auth(request, parent_folder=child_folder)

        assert resolved.auth == parent_auth
        assert resolved.source == AuthSource.FOLDER
        assert resolved.path == ["Parent Folder", "Child Folder", "Test Request"]

    def test_resolve_deeply_nested_folders(self):
        """Test resolving authentication through deeply nested folder hierarchy."""
        # Create grandparent folder with auth
        grandparent_auth = Auth(type="apikey", parameters=[
            AuthParameter("key", "X-API-Key"),
            AuthParameter("value", "grandparent-key")
        ])
        grandparent_folder = Folder(
            name="Grandparent Folder",
            items=[],
            auth=grandparent_auth
        )

        # Create parent folder without auth
        parent_folder = Folder(
            name="Parent Folder",
            items=[]
        )
        parent_folder._parent_folder = grandparent_folder

        # Create child folder without auth
        child_folder = Folder(
            name="Child Folder",
            items=[]
        )
        child_folder._parent_folder = parent_folder

        # Create request without auth
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        # Resolve auth
        resolved = AuthResolver.resolve_auth(request, parent_folder=child_folder)

        assert resolved.auth == grandparent_auth
        assert resolved.source == AuthSource.FOLDER
        assert resolved.path == ["Grandparent Folder", "Parent Folder", "Child Folder", "Test Request"]

    def test_resolve_with_full_hierarchy(self):
        """Test resolving with complete hierarchy (collection, folders, request)."""
        # Create collection with auth
        collection_auth = Auth(type="basic", parameters=[
            AuthParameter("username", "collection-user"),
            AuthParameter("password", "collection-pass")
        ])
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            ),
            auth=collection_auth
        )

        # Create parent folder without auth
        parent_folder = Folder(
            name="Parent Folder",
            items=[]
        )

        # Create child folder with auth
        child_auth = Auth(type="bearer", parameters=[AuthParameter("token", "child-token")])
        child_folder = Folder(
            name="Child Folder",
            items=[],
            auth=child_auth
        )
        child_folder._parent_folder = parent_folder

        # Create request without auth
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        # Resolve auth - should use child folder auth
        resolved = AuthResolver.resolve_auth(request, parent_folder=child_folder, collection=collection)

        assert resolved.auth == child_auth
        assert resolved.source == AuthSource.FOLDER
        assert resolved.path == ["Child Folder", "Test Request"]


class TestRequestGetEffectiveAuth:
    """Test Request.get_effective_auth() method."""

    def test_get_effective_auth_with_request_auth(self):
        """Test get_effective_auth when request has auth."""
        request_auth = Auth(type="bearer", parameters=[AuthParameter("token", "request-token")])
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com"),
            auth=request_auth
        )

        resolved = request.get_effective_auth()

        assert resolved.auth == request_auth
        assert resolved.source == AuthSource.REQUEST

    def test_get_effective_auth_with_stored_parent(self):
        """Test get_effective_auth using stored parent folder reference."""
        folder_auth = Auth(type="apikey", parameters=[
            AuthParameter("key", "X-API-Key"),
            AuthParameter("value", "folder-key")
        ])
        folder = Folder(
            name="Test Folder",
            items=[],
            auth=folder_auth
        )

        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        request._parent_folder = folder

        resolved = request.get_effective_auth()

        assert resolved.auth == folder_auth
        assert resolved.source == AuthSource.FOLDER

    def test_get_effective_auth_with_stored_collection(self):
        """Test get_effective_auth using stored collection reference."""
        collection_auth = Auth(type="basic", parameters=[
            AuthParameter("username", "user"),
            AuthParameter("password", "pass")
        ])
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            ),
            auth=collection_auth
        )

        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        request._collection = collection

        resolved = request.get_effective_auth()

        assert resolved.auth == collection_auth
        assert resolved.source == AuthSource.COLLECTION

    def test_get_effective_auth_with_explicit_arguments(self):
        """Test get_effective_auth with explicit parent and collection arguments."""
        folder_auth = Auth(type="bearer", parameters=[AuthParameter("token", "folder-token")])
        folder = Folder(
            name="Test Folder",
            items=[],
            auth=folder_auth
        )

        collection_auth = Auth(type="basic", parameters=[
            AuthParameter("username", "user"),
            AuthParameter("password", "pass")
        ])
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            ),
            auth=collection_auth
        )

        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        # Explicit arguments should override stored references
        resolved = request.get_effective_auth(parent_folder=folder, collection=collection)

        assert resolved.auth == folder_auth
        assert resolved.source == AuthSource.FOLDER

    def test_get_effective_auth_explicit_overrides_stored(self):
        """Test that explicit arguments override stored references."""
        # Set up stored references
        stored_folder_auth = Auth(type="bearer", parameters=[AuthParameter("token", "stored-token")])
        stored_folder = Folder(
            name="Stored Folder",
            items=[],
            auth=stored_folder_auth
        )

        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        request._parent_folder = stored_folder

        # Provide explicit folder with different auth
        explicit_folder_auth = Auth(type="apikey", parameters=[
            AuthParameter("key", "X-API-Key"),
            AuthParameter("value", "explicit-key")
        ])
        explicit_folder = Folder(
            name="Explicit Folder",
            items=[],
            auth=explicit_folder_auth
        )

        # Explicit argument should be used
        resolved = request.get_effective_auth(parent_folder=explicit_folder)

        assert resolved.auth == explicit_folder_auth
        assert resolved.source == AuthSource.FOLDER
        assert "Explicit Folder" in resolved.path


class TestFolderSetParent:
    """Test Folder.set_parent() and set_collection() methods."""

    def test_folder_set_parent(self):
        """Test setting parent folder."""
        parent = Folder(name="Parent", items=[])
        child = Folder(name="Child", items=[])

        child.set_parent(parent)

        assert child._parent_folder == parent

    def test_folder_set_parent_none(self):
        """Test setting parent folder to None."""
        folder = Folder(name="Folder", items=[])
        folder.set_parent(None)

        assert folder._parent_folder is None

    def test_folder_set_collection(self):
        """Test setting collection reference."""
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            )
        )
        folder = Folder(name="Folder", items=[])

        folder.set_collection(collection)

        assert folder._collection == collection


class TestRequestSetParent:
    """Test Request.set_parent() and set_collection() methods."""

    def test_request_set_parent(self):
        """Test setting parent folder."""
        folder = Folder(name="Folder", items=[])
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        request.set_parent(folder)

        assert request._parent_folder == folder

    def test_request_set_parent_none(self):
        """Test setting parent folder to None."""
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )
        request.set_parent(None)

        assert request._parent_folder is None

    def test_request_set_collection(self):
        """Test setting collection reference."""
        collection = Collection(
            info=CollectionInfo(
                name="Test Collection",
                schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
            )
        )
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com")
        )

        request.set_collection(collection)

        assert request._collection == collection

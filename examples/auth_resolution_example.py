"""
Example demonstrating authentication inheritance resolution.

This example shows how to use the AuthResolver to determine which authentication
will be used for a request by walking up the collection hierarchy.
"""

from python_postman.models.auth import Auth, AuthParameter
from python_postman.models.request import Request
from python_postman.models.folder import Folder
from python_postman.models.collection import Collection
from python_postman.models.collection_info import CollectionInfo
from python_postman.models.url import Url
from python_postman.introspection import AuthResolver, AuthSource


def main():
    """Demonstrate authentication inheritance resolution."""
    
    print("=" * 70)
    print("Authentication Inheritance Resolution Example")
    print("=" * 70)
    print()
    
    # Create a collection with collection-level auth
    collection_auth = Auth(
        type="basic",
        parameters=[
            AuthParameter("username", "collection-user"),
            AuthParameter("password", "collection-pass")
        ]
    )
    collection = Collection(
        info=CollectionInfo(
            name="API Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        ),
        auth=collection_auth
    )
    
    # Create a parent folder with folder-level auth
    parent_folder_auth = Auth(
        type="bearer",
        parameters=[AuthParameter("token", "parent-folder-token")]
    )
    parent_folder = Folder(
        name="Authenticated Endpoints",
        items=[],
        auth=parent_folder_auth
    )
    parent_folder.set_collection(collection)
    
    # Create a child folder without auth (will inherit from parent)
    child_folder = Folder(
        name="User Management",
        items=[]
    )
    child_folder.set_parent(parent_folder)
    child_folder.set_collection(collection)
    
    # Example 1: Request with its own auth (highest priority)
    print("Example 1: Request with its own authentication")
    print("-" * 70)
    request_auth = Auth(
        type="apikey",
        parameters=[
            AuthParameter("key", "X-API-Key"),
            AuthParameter("value", "request-specific-key")
        ]
    )
    request1 = Request(
        name="Create User",
        method="POST",
        url=Url.from_string("https://api.example.com/users"),
        auth=request_auth
    )
    request1.set_parent(child_folder)
    request1.set_collection(collection)
    
    resolved1 = request1.get_effective_auth()
    print(f"Request: {request1.name}")
    print(f"Resolved Auth Type: {resolved1.auth.type if resolved1.auth else 'None'}")
    print(f"Auth Source: {resolved1.source.value}")
    print(f"Hierarchy Path: {' > '.join(resolved1.path)}")
    print()
    
    # Example 2: Request inheriting from folder
    print("Example 2: Request inheriting from folder")
    print("-" * 70)
    request2 = Request(
        name="Get User",
        method="GET",
        url=Url.from_string("https://api.example.com/users/123")
    )
    request2.set_parent(child_folder)
    request2.set_collection(collection)
    
    resolved2 = request2.get_effective_auth()
    print(f"Request: {request2.name}")
    print(f"Resolved Auth Type: {resolved2.auth.type if resolved2.auth else 'None'}")
    print(f"Auth Source: {resolved2.source.value}")
    print(f"Hierarchy Path: {' > '.join(resolved2.path)}")
    print()
    
    # Example 3: Request inheriting from collection (no folder auth)
    print("Example 3: Request inheriting from collection")
    print("-" * 70)
    no_auth_folder = Folder(
        name="Public Endpoints",
        items=[]
    )
    no_auth_folder.set_collection(collection)
    
    request3 = Request(
        name="Get Public Data",
        method="GET",
        url=Url.from_string("https://api.example.com/public")
    )
    request3.set_parent(no_auth_folder)
    request3.set_collection(collection)
    
    resolved3 = request3.get_effective_auth()
    print(f"Request: {request3.name}")
    print(f"Resolved Auth Type: {resolved3.auth.type if resolved3.auth else 'None'}")
    print(f"Auth Source: {resolved3.source.value}")
    print(f"Hierarchy Path: {' > '.join(resolved3.path)}")
    print()
    
    # Example 4: Request with no auth anywhere
    print("Example 4: Request with no authentication anywhere")
    print("-" * 70)
    no_auth_collection = Collection(
        info=CollectionInfo(
            name="No Auth Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
    )
    
    request4 = Request(
        name="Anonymous Request",
        method="GET",
        url=Url.from_string("https://api.example.com/anonymous")
    )
    request4.set_collection(no_auth_collection)
    
    resolved4 = request4.get_effective_auth()
    print(f"Request: {request4.name}")
    print(f"Resolved Auth Type: {resolved4.auth.type if resolved4.auth else 'None'}")
    print(f"Auth Source: {resolved4.source.value}")
    print(f"Hierarchy Path: {' > '.join(resolved4.path)}")
    print()
    
    # Example 5: Using AuthResolver directly
    print("Example 5: Using AuthResolver directly")
    print("-" * 70)
    request5 = Request(
        name="Direct Resolution",
        method="GET",
        url=Url.from_string("https://api.example.com/direct")
    )
    
    # Resolve with explicit hierarchy
    resolved5 = AuthResolver.resolve_auth(
        request=request5,
        parent_folder=parent_folder,
        collection=collection
    )
    print(f"Request: {request5.name}")
    print(f"Resolved Auth Type: {resolved5.auth.type if resolved5.auth else 'None'}")
    print(f"Auth Source: {resolved5.source.value}")
    print(f"Hierarchy Path: {' > '.join(resolved5.path)}")
    print()
    
    print("=" * 70)
    print("Summary:")
    print("=" * 70)
    print("Authentication resolution follows this priority:")
    print("1. Request-level auth (highest priority)")
    print("2. Folder-level auth (walks up parent folders)")
    print("3. Collection-level auth (lowest priority)")
    print("4. No auth if none found")
    print()


if __name__ == "__main__":
    main()

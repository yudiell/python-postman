"""
Tests for description field usage and documentation.
"""

import pytest
from python_postman.models import Item, Request, Folder, Url, Collection, CollectionInfo


class TestDescriptionFields:
    """Test description field functionality."""

    def test_item_description_in_request(self):
        """Test that Request has description field from Item."""
        request = Request(
            name="Test Request",
            method="GET",
            url=Url.from_string("https://api.example.com/test"),
            description="This is a test request description"
        )
        
        assert request.description == "This is a test request description"
        assert hasattr(request, 'description')

    def test_item_description_in_folder(self):
        """Test that Folder has description field from Item."""
        folder = Folder(
            name="Test Folder",
            items=[],
            description="This is a test folder description"
        )
        
        assert folder.description == "This is a test folder description"
        assert hasattr(folder, 'description')

    def test_factory_method_with_description(self):
        """Test factory methods support description parameter."""
        # Test create_request
        request = Item.create_request(
            name="Factory Request",
            method="POST",
            url="https://api.example.com/create",
            description="Created via factory method"
        )
        assert request.description == "Created via factory method"
        
        # Test create_folder
        folder = Item.create_folder(
            name="Factory Folder",
            description="Created via factory method"
        )
        assert folder.description == "Created via factory method"

    def test_description_optional(self):
        """Test that description is optional."""
        request = Request(
            name="No Description",
            method="GET",
            url=Url.from_string("https://api.example.com/test")
        )
        assert request.description is None
        
        folder = Folder(
            name="No Description",
            items=[]
        )
        assert folder.description is None

    def test_description_serialization(self):
        """Test that descriptions are preserved in to_dict/from_dict."""
        # Create request with description
        original_request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com/test"),
            description="Original description"
        )
        
        # Serialize and deserialize
        data = original_request.to_dict()
        restored_request = Request.from_dict(data)
        
        assert restored_request.description == "Original description"
        
        # Create folder with description
        original_folder = Folder(
            name="Test Folder",
            items=[],
            description="Folder description"
        )
        
        # Serialize and deserialize
        data = original_folder.to_dict()
        restored_folder = Folder.from_dict(data)
        
        assert restored_folder.description == "Folder description"

    def test_description_with_markdown(self):
        """Test that markdown content is preserved in descriptions."""
        markdown_desc = """
# API Endpoint

This endpoint does something important.

## Parameters
- `id`: The resource ID
- `name`: The resource name

## Response
Returns a JSON object with the resource data.
"""
        
        request = Request(
            name="Markdown Test",
            method="GET",
            url=Url.from_string("https://api.example.com/test"),
            description=markdown_desc
        )
        
        assert request.description == markdown_desc
        assert "# API Endpoint" in request.description
        assert "## Parameters" in request.description

    def test_description_modification(self):
        """Test that descriptions can be modified after creation."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com/test")
        )
        
        # Initially None
        assert request.description is None
        
        # Add description
        request.description = "New description"
        assert request.description == "New description"
        
        # Modify description
        request.description = "Updated description"
        assert request.description == "Updated description"

    def test_nested_items_with_descriptions(self):
        """Test that nested structures preserve descriptions."""
        # Create requests with descriptions
        req1 = Item.create_request(
            name="Request 1",
            method="GET",
            url="https://api.example.com/1",
            description="First request"
        )
        
        req2 = Item.create_request(
            name="Request 2",
            method="POST",
            url="https://api.example.com/2",
            description="Second request"
        )
        
        # Create folder with description containing requests
        folder = Item.create_folder(
            name="API Folder",
            description="Folder containing API requests",
            items=[req1, req2]
        )
        
        # Verify all descriptions are preserved
        assert folder.description == "Folder containing API requests"
        assert folder.items[0].description == "First request"
        assert folder.items[1].description == "Second request"

    def test_collection_info_description(self):
        """Test that collection info has description field."""
        info = CollectionInfo(
            name="Test Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            description="This is a test collection"
        )
        
        assert info.description == "This is a test collection"

    def test_description_in_full_collection(self):
        """Test descriptions in a complete collection structure."""
        # Create collection with description
        info = CollectionInfo(
            name="API Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            description="Complete API collection"
        )
        
        # Create folder with requests
        folder = Item.create_folder(
            name="Users",
            description="User management endpoints"
        )
        
        request = Item.create_request(
            name="Get User",
            method="GET",
            url="https://api.example.com/users/1",
            description="Retrieves a user by ID"
        )
        
        folder.items.append(request)
        
        # Create collection
        collection = Collection(info=info, items=[folder])
        
        # Verify all descriptions
        assert collection.info.description == "Complete API collection"
        assert collection.items[0].description == "User management endpoints"
        
        requests = list(collection.get_requests())
        assert requests[0].description == "Retrieves a user by ID"

    def test_empty_string_description(self):
        """Test that empty string descriptions are handled correctly."""
        request = Request(
            name="Test",
            method="GET",
            url=Url.from_string("https://api.example.com/test"),
            description=""
        )
        
        # Empty string is preserved (not converted to None)
        assert request.description == ""
        assert request.description is not None

    def test_description_with_special_characters(self):
        """Test that special characters in descriptions are preserved."""
        special_desc = "Test with special chars: <>&\"'`\n\t\r"
        
        request = Request(
            name="Special Chars",
            method="GET",
            url=Url.from_string("https://api.example.com/test"),
            description=special_desc
        )
        
        assert request.description == special_desc
        
        # Verify serialization preserves special characters
        data = request.to_dict()
        restored = Request.from_dict(data)
        assert restored.description == special_desc

    def test_description_unicode(self):
        """Test that Unicode characters in descriptions are preserved."""
        unicode_desc = "Test with Unicode: 你好 🌍 café"
        
        request = Request(
            name="Unicode Test",
            method="GET",
            url=Url.from_string("https://api.example.com/test"),
            description=unicode_desc
        )
        
        assert request.description == unicode_desc
        
        # Verify serialization preserves Unicode
        data = request.to_dict()
        restored = Request.from_dict(data)
        assert restored.description == unicode_desc


class TestDescriptionDocumentation:
    """Test that documentation examples work correctly."""

    def test_audit_descriptions_example(self):
        """Test the audit descriptions example from documentation."""
        # Create collection with mixed description coverage
        info = CollectionInfo(
            name="Test Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )
        
        folder_with_desc = Item.create_folder(
            name="Folder 1",
            description="Has description"
        )
        
        folder_without_desc = Item.create_folder(
            name="Folder 2"
        )
        
        req_with_desc = Item.create_request(
            name="Request 1",
            method="GET",
            url="https://api.example.com/1",
            description="Has description"
        )
        
        req_without_desc = Item.create_request(
            name="Request 2",
            method="GET",
            url="https://api.example.com/2"
        )
        
        folder_with_desc.items.append(req_with_desc)
        folder_without_desc.items.append(req_without_desc)
        
        collection = Collection(
            info=info,
            items=[folder_with_desc, folder_without_desc]
        )
        
        # Audit function from documentation
        def audit_descriptions(collection):
            stats = {
                'total_items': 0,
                'items_with_descriptions': 0,
                'missing': []
            }
            
            def check_items(items, path=""):
                for item in items:
                    current_path = f"{path}/{item.name}"
                    stats['total_items'] += 1
                    
                    has_description = bool(item.description and item.description.strip())
                    
                    if has_description:
                        stats['items_with_descriptions'] += 1
                    else:
                        stats['missing'].append({
                            'type': item.__class__.__name__,
                            'name': item.name,
                            'path': current_path
                        })
                    
                    if hasattr(item, 'items'):
                        check_items(item.items, current_path)
            
            check_items(collection.items)
            return stats
        
        stats = audit_descriptions(collection)
        
        # Verify audit results
        assert stats['total_items'] == 4  # 2 folders + 2 requests
        assert stats['items_with_descriptions'] == 2  # 1 folder + 1 request
        assert len(stats['missing']) == 2
        
        # Verify missing items are correctly identified
        missing_names = [item['name'] for item in stats['missing']]
        assert 'Folder 2' in missing_names
        assert 'Request 2' in missing_names

    def test_generate_markdown_example(self):
        """Test the markdown generation example from documentation."""
        # Create simple collection
        info = CollectionInfo(
            name="API",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            description="API Collection"
        )
        
        request = Item.create_request(
            name="Get Data",
            method="GET",
            url="https://api.example.com/data",
            description="Retrieves data"
        )
        
        collection = Collection(info=info, items=[request])
        
        # Generate markdown (simplified version)
        def generate_markdown(collection):
            lines = [f"# {collection.info.name}\n"]
            if collection.info.description:
                lines.append(f"{collection.info.description}\n")
            
            for request in collection.get_requests():
                lines.append(f"\n## {request.method} {request.name}\n")
                if request.description:
                    lines.append(f"{request.description}\n")
            
            return "\n".join(lines)
        
        markdown = generate_markdown(collection)
        
        # Verify markdown content
        assert "# API" in markdown
        assert "API Collection" in markdown
        assert "## GET Get Data" in markdown
        assert "Retrieves data" in markdown


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

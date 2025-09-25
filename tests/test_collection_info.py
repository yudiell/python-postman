"""Unit tests for CollectionInfo model."""

import pytest
from python_postman.models.collection_info import CollectionInfo


class TestCollectionInfo:
    """Test cases for CollectionInfo class."""

    def test_init_with_required_fields(self):
        """Test CollectionInfo initialization with required fields only."""
        info = CollectionInfo(name="Test Collection")
        assert info.name == "Test Collection"
        assert info.description is None
        assert info.schema is None

    def test_init_with_all_fields(self):
        """Test CollectionInfo initialization with all fields."""
        info = CollectionInfo(
            name="Test Collection",
            description="A test collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        )
        assert info.name == "Test Collection"
        assert info.description == "A test collection"
        assert (
            info.schema
            == "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )

    def test_validate_success(self):
        """Test successful validation."""
        info = CollectionInfo(name="Valid Collection")
        assert info.validate() is True

    def test_validate_empty_name_fails(self):
        """Test validation fails with empty name."""
        info = CollectionInfo(name="")
        with pytest.raises(ValueError, match="Collection name is required"):
            info.validate()

    def test_validate_none_name_fails(self):
        """Test validation fails with None name."""
        info = CollectionInfo(name=None)
        with pytest.raises(ValueError, match="Collection name is required"):
            info.validate()

    def test_validate_whitespace_name_fails(self):
        """Test validation fails with whitespace-only name."""
        info = CollectionInfo(name="   ")
        with pytest.raises(ValueError, match="Collection name is required"):
            info.validate()

    def test_validate_non_string_name_fails(self):
        """Test validation fails with non-string name."""
        info = CollectionInfo(name=123)
        with pytest.raises(ValueError, match="Collection name is required"):
            info.validate()

    def test_validate_non_string_description_fails(self):
        """Test validation fails with non-string description."""
        info = CollectionInfo(name="Test", description=123)
        with pytest.raises(ValueError, match="Collection description must be a string"):
            info.validate()

    def test_validate_non_string_schema_fails(self):
        """Test validation fails with non-string schema."""
        info = CollectionInfo(name="Test", schema=123)
        with pytest.raises(ValueError, match="Collection schema must be a string"):
            info.validate()

    def test_from_dict_minimal(self):
        """Test creating CollectionInfo from minimal dictionary."""
        data = {"name": "Test Collection"}
        info = CollectionInfo.from_dict(data)
        assert info.name == "Test Collection"
        assert info.description is None
        assert info.schema is None

    def test_from_dict_complete(self):
        """Test creating CollectionInfo from complete dictionary."""
        data = {
            "name": "Test Collection",
            "description": "A test collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        }
        info = CollectionInfo.from_dict(data)
        assert info.name == "Test Collection"
        assert info.description == "A test collection"
        assert (
            info.schema
            == "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        )

    def test_from_dict_missing_name(self):
        """Test creating CollectionInfo from dictionary without name."""
        data = {"description": "A test collection"}
        info = CollectionInfo.from_dict(data)
        assert info.name is None
        assert info.description == "A test collection"

    def test_to_dict_minimal(self):
        """Test converting CollectionInfo to dictionary with minimal data."""
        info = CollectionInfo(name="Test Collection")
        result = info.to_dict()
        expected = {"name": "Test Collection"}
        assert result == expected

    def test_to_dict_complete(self):
        """Test converting CollectionInfo to dictionary with complete data."""
        info = CollectionInfo(
            name="Test Collection",
            description="A test collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        )
        result = info.to_dict()
        expected = {
            "name": "Test Collection",
            "description": "A test collection",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        }
        assert result == expected

    def test_repr(self):
        """Test string representation."""
        info = CollectionInfo(name="Test", description="Desc", schema="Schema")
        expected = "CollectionInfo(name='Test', description='Desc', schema='Schema')"
        assert repr(info) == expected

    def test_equality_same_objects(self):
        """Test equality between identical CollectionInfo objects."""
        info1 = CollectionInfo(name="Test", description="Desc", schema="Schema")
        info2 = CollectionInfo(name="Test", description="Desc", schema="Schema")
        assert info1 == info2

    def test_equality_different_objects(self):
        """Test inequality between different CollectionInfo objects."""
        info1 = CollectionInfo(name="Test1", description="Desc", schema="Schema")
        info2 = CollectionInfo(name="Test2", description="Desc", schema="Schema")
        assert info1 != info2

    def test_equality_different_types(self):
        """Test inequality with different object types."""
        info = CollectionInfo(name="Test")
        assert info != "not a CollectionInfo object"

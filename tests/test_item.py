"""
Tests for the Item abstract base class.
"""

import pytest
from abc import ABC
from python_postman.models.item import Item


class ConcreteItem(Item):
    """Concrete implementation of Item for testing purposes."""

    def get_requests(self):
        return iter([])


def test_item_is_abstract():
    """Test that Item is an abstract base class."""
    assert issubclass(Item, ABC)

    # Should not be able to instantiate Item directly
    with pytest.raises(TypeError):
        Item("test", "description")


def test_concrete_item_initialization():
    """Test that concrete Item subclass can be initialized properly."""
    item = ConcreteItem("Test Item", "Test description")

    assert item.name == "Test Item"
    assert item.description == "Test description"


def test_concrete_item_initialization_without_description():
    """Test that concrete Item can be initialized without description."""
    item = ConcreteItem("Test Item")

    assert item.name == "Test Item"
    assert item.description is None


def test_item_str_representation():
    """Test string representation of Item."""
    item = ConcreteItem("Test Item", "Test description")

    assert str(item) == "ConcreteItem(name='Test Item')"


def test_item_repr_representation():
    """Test repr representation of Item."""
    item = ConcreteItem("Test Item", "Test description")

    assert (
        repr(item) == "ConcreteItem(name='Test Item', description='Test description')"
    )


def test_item_repr_without_description():
    """Test repr representation of Item without description."""
    item = ConcreteItem("Test Item")

    assert repr(item) == "ConcreteItem(name='Test Item', description='None')"


def test_get_requests_is_abstract():
    """Test that get_requests method is abstract."""
    # This is implicitly tested by the fact that ConcreteItem must implement it
    item = ConcreteItem("Test Item")

    # Should be able to call the method
    requests = list(item.get_requests())
    assert requests == []

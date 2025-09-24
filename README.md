# Python Postman Collection Parser

A Python library for parsing and working with Postman collection.json files. This library provides a clean, object-oriented interface for reading Postman collections and accessing their components programmatically.

## Features

- **Parse Postman Collections**: Load collections from files, JSON strings, or dictionaries
- **Object-Oriented API**: Work with collections using intuitive Python objects
- **Full Collection Support**: Access requests, folders, variables, authentication, and scripts
- **Validation**: Built-in validation for collection structure and schema compliance
- **Iteration**: Easy iteration through all requests regardless of folder structure
- **Search**: Find requests and folders by name
- **Type Hints**: Full type annotation support for better IDE experience

## Installation

```bash
pip install python-postman
```

## Quick Start

### Loading a Collection

```python
from python_postman import PythonPostman

# Load from file
collection = PythonPostman.from_file("path/to/collection.json")

# Load from JSON string
json_string = '{"info": {"name": "My Collection"}, "item": []}'
collection = PythonPostman.from_json(json_string)

# Load from dictionary
collection_dict = {"info": {"name": "My Collection"}, "item": []}
collection = PythonPostman.from_dict(collection_dict)
```

### Accessing Collection Information

```python
# Basic collection info
print(f"Collection Name: {collection.info.name}")
print(f"Description: {collection.info.description}")
print(f"Schema: {collection.info.schema}")

# Collection-level variables
for variable in collection.variables:
    print(f"Variable: {variable.key} = {variable.value}")

# Collection-level authentication
if collection.auth:
    print(f"Auth Type: {collection.auth.type}")
```

### Working with Requests

```python
# Iterate through all requests (flattens folder structure)
for request in collection.get_all_requests():
    print(f"Request: {request.method} {request.name}")
    print(f"URL: {request.url}")

    # Access headers
    for header in request.headers:
        print(f"Header: {header.key} = {header.value}")

    # Access request body
    if request.body:
        print(f"Body Type: {request.body.mode}")
        print(f"Body Content: {request.body.raw}")

# Find specific request by name
request = collection.get_request_by_name("Login Request")
if request:
    print(f"Found request: {request.method} {request.url}")
```

### Working with Folders

```python
# Access top-level items
for item in collection.items:
    if hasattr(item, 'items'):  # It's a folder
        print(f"Folder: {item.name}")
        print(f"Items in folder: {len(item.items)}")

        # Get all requests in this folder
        for request in item.get_requests():
            print(f"  Request: {request.name}")
    else:  # It's a request
        print(f"Request: {item.name}")

# Find specific folder by name
folder = collection.get_folder_by_name("Authentication")
if folder:
    print(f"Found folder: {folder.name}")
    print(f"Subfolders: {len(folder.get_subfolders())}")
```

### Working with Variables

```python
# Collection variables
for var in collection.variables:
    print(f"Collection Variable: {var.key} = {var.value}")
    if var.description:
        print(f"  Description: {var.description}")

# Folder variables (if folder has variables)
for item in collection.items:
    if hasattr(item, 'variables') and item.variables:
        print(f"Folder '{item.name}' variables:")
        for var in item.variables:
            print(f"  {var.key} = {var.value}")
```

### Authentication

```python
# Collection-level auth
if collection.auth:
    print(f"Collection Auth: {collection.auth.type}")

    # Access auth details based on type
    if collection.auth.type == "bearer":
        token = collection.auth.bearer.get("token")
        print(f"Bearer Token: {token}")
    elif collection.auth.type == "basic":
        username = collection.auth.basic.get("username")
        print(f"Basic Auth Username: {username}")

# Request-level auth (overrides collection auth)
for request in collection.get_all_requests():
    if request.auth:
        print(f"Request '{request.name}' has {request.auth.type} auth")
```

### Events (Scripts)

```python
# Collection-level events
for event in collection.events:
    print(f"Collection Event: {event.listen}")
    print(f"Script: {event.script}")

# Request-level events
for request in collection.get_all_requests():
    for event in request.events:
        if event.listen == "prerequest":
            print(f"Pre-request script for {request.name}")
        elif event.listen == "test":
            print(f"Test script for {request.name}")
```

### Validation

```python
# Validate collection structure
validation_result = collection.validate()

if validation_result.is_valid:
    print("Collection is valid!")
else:
    print("Collection validation failed:")
    for error in validation_result.errors:
        print(f"  - {error}")

# Quick validation without creating full objects
is_valid = PythonPostman.validate_collection_dict(collection_dict)
print(f"Collection dict is valid: {is_valid}")
```

### Creating New Collections

```python
# Create a new empty collection
collection = PythonPostman.create_collection(
    name="My New Collection",
    description="A collection created programmatically"
)

print(f"Created collection: {collection.info.name}")
```

## API Reference

### Main Classes

- **`PythonPostman`**: Main entry point for loading collections
- **`Collection`**: Represents a complete Postman collection
- **`Request`**: Individual HTTP request
- **`Folder`**: Container for organizing requests and sub-folders
- **`Variable`**: Collection, folder, or request-level variables
- **`Auth`**: Authentication configuration
- **`Event`**: Pre-request scripts and test scripts

### Exception Handling

The library provides specific exceptions for different error scenarios:

```python
from python_postman import (
    PostmanCollectionError,      # Base exception
    CollectionParseError,        # JSON parsing errors
    CollectionValidationError,   # Structure validation errors
    CollectionFileError,         # File operation errors
)

try:
    collection = PythonPostman.from_file("collection.json")
except CollectionFileError as e:
    print(f"File error: {e}")
except CollectionParseError as e:
    print(f"Parse error: {e}")
except CollectionValidationError as e:
    print(f"Validation error: {e}")
```

## Requirements

- Python 3.8+
- No external dependencies for core functionality

## Development

### Setting up Development Environment

```bash
# Clone the repository
git clone https://github.com/python-postman/python-postman.git
cd python-postman

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run tests with coverage
pytest --cov=python_postman

# Format code
black python_postman tests
isort python_postman tests

# Type checking
mypy python_postman
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_collection.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=python_postman --cov-report=html
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Changelog

### 0.1.0 (Initial Release)

- Initial release with full Postman collection parsing support
- Support for collections, requests, folders, variables, authentication, and events
- Comprehensive validation and error handling
- Full type annotation support
- Extensive test coverage

## Support

If you encounter any issues or have questions, please file an issue on the [GitHub issue tracker](https://github.com/python-postman/python-postman/issues).

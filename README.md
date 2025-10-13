# Python Postman

A comprehensive Python library for working with Postman collections. Parse, execute, search, and analyze Postman collection.json files with a clean, object-oriented interface. Execute HTTP requests with full async/sync support, dynamic variable resolution, and authentication handling.

## Features

- **Parse Postman Collections**: Load collections from files, JSON strings, or dictionaries
- **Object-Oriented API**: Work with collections using intuitive Python objects
- **Full Collection Support**: Access requests, folders, variables, authentication, and events
- **HTTP Request Execution**: Execute requests using httpx with full async/sync support
- **Variable Resolution**: Dynamic variable substitution with proper scoping
- **Authentication Handling**: Automatic auth processing for Bearer, Basic, and API Key
- **Request Extensions**: Runtime modification of URLs, headers, body, and auth
- **Validation**: Built-in validation for collection structure and schema compliance
- **Iteration**: Easy iteration through all requests regardless of folder structure
- **Search**: Find requests and folders by name
- **Type Hints**: Full type annotation support for better IDE experience

## Installation

```bash
# Basic installation (parsing only)
pip install python-postman

# With HTTP execution support
pip install python-postman[execution]
# or
pip install python-postman httpx
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
for variable in collection.variables: # This requests a list of Variable objects
    print(f"Variable: {variable.key} = {variable.value}")

# Collection variables dictionary. This is a quick way to get key-value pairs.
# You can pass/update these and add them to the execution context.
collection_variables = collection.get_variables()

# Collection-level authentication
if collection.auth:
    print(f"Auth Type: {collection.auth.type}")
```

### Working with Requests

```python
# Get a list of requests by name
collection.list_requests()

# Find specific request by name
login_request = collection.get_request_by_name("Login Request")
if login_request:
    print(f"Found request: {login_request.method} {login_request.url}")

# Iterate through all requests (flattens folder structure)
for request in collection.get_requests():
    print(f"Request: {request.method} {request.name}")
    print(f"URL: {request.url}")

    # Access headers
    for header in request.headers:
        print(f"Header: {header.key} = {header.value}")

    # Access request body
    if request.body:
        print(f"Body Type: {request.body.mode}")
        print(f"Body Content: {request.body.raw}")
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
for request in collection.get_requests():
    if request.auth:
        print(f"Request '{request.name}' has {request.auth.type} auth")
```

### Events (Scripts)

```python
# Access script content from collection-level events
for event in collection.events:
    print(f"Collection Event: {event.listen}")
    print(f"Script Content: {event.script}")

# Access script content from request-level events
# Note: JavaScript execution is not supported - scripts are accessible as text only
for request in collection.get_requests():
    for event in request.events:
        if event.listen == "prerequest":
            print(f"Pre-request script for {request.name}: {event.script}")
        elif event.listen == "test":
            print(f"Test script for {request.name}: {event.script}")
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

## HTTP Request Execution

The library supports executing HTTP requests from Postman collections using httpx. This feature requires the `httpx` dependency.

### Basic Request Execution

```python
import asyncio
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

async def main():
    # Load collection
    collection = PythonPostman.from_file("api_collection.json")

    # Create executor
    executor = RequestExecutor(
        client_config={"timeout": 30.0, "verify": True},
        global_headers={"User-Agent": "python-postman/1.0"}
    )

    # Create execution context with variables
    context = ExecutionContext(
        environment_variables={
            "base_url": "https://api.example.com",
            "api_key": "your-api-key"
        }
    )

    # Execute a single request
    request = collection.get_request_by_name("Get Users")
    result = await executor.execute_request(request, context)

    if result.success:
        print(f"Status: {result.response.status_code}")
        print(f"Response: {result.response.json}")
        print(f"Time: {result.response.elapsed_ms:.2f}ms")
    else:
        print(f"Error: {result.error}")

    await executor.aclose()

asyncio.run(main())
```

### Synchronous Execution

```python
from python_postman.execution import RequestExecutor, ExecutionContext

# Synchronous execution
with RequestExecutor() as executor:
    context = ExecutionContext(
        environment_variables={"base_url": "https://httpbin.org"}
    )

    result = executor.execute_request_sync(request, context)
    if result.success:
        print(f"Status: {result.response.status_code}")
```

### Collection Execution

```python
# Execute entire collection
async def execute_collection():
    executor = RequestExecutor()

    # Sequential execution
    result = await executor.execute_collection(collection)
    print(f"Executed {result.total_requests} requests")
    print(f"Success rate: {result.successful_requests}/{result.total_requests}")

    # Parallel execution
    result = await executor.execute_collection(
        collection,
        parallel=True,
        stop_on_error=False
    )

    # Get the request responses
    for result in result.results:
        print(f"Request: {result.request.name}")
        print(f"Result Text: {result.response.text}")

    print(f"Parallel execution completed in {result.total_time_ms:.2f}ms")

    await executor.aclose()
```

### Variable Management

```python
# Variable scoping: request > folder > collection > environment
context = ExecutionContext(
    environment_variables={"env": "production"},
    collection_variables={"api_version": "v1", "timeout": "30"},
    folder_variables={"endpoint": "/users"},
    request_variables={"user_id": "12345"}
)

# Variables are resolved with proper precedence
url = context.resolve_variables("{{base_url}}/{{api_version}}{{endpoint}}/{{user_id}}")
print(url)  # "https://api.example.com/v1/users/12345"

# Dynamic variable updates
context.set_variable("session_token", "abc123", "environment")
```

### Path Parameters

The library supports both Postman-style variables (`{{variable}}`) and path parameters (`:parameter`):

```python
# Path parameters use :parameterName syntax
context = ExecutionContext(
    environment_variables={
        "baseURL": "https://api.example.com",
        "userId": "12345",
        "datasetId": "abc123"
    }
)

# Mix Postman variables and path parameters
url = context.resolve_variables("{{baseURL}}/users/:userId/datasets/:datasetId")
print(url)  # "https://api.example.com/users/12345/datasets/abc123"

# Path parameters follow the same scoping rules as Postman variables
url = context.resolve_variables("{{baseURL}}/:datasetId?$offset=0&$limit=10")
print(url)  # "https://api.example.com/abc123?$offset=0&$limit=10"
```

### Request Extensions

```python
from python_postman.execution import RequestExtensions

# Runtime request modifications
extensions = RequestExtensions(
    # Substitute existing values
    header_substitutions={"Authorization": "Bearer {{new_token}}"},
    url_substitutions={"host": "staging.api.example.com"},

    # Add new values
    header_extensions={"X-Request-ID": "req-{{timestamp}}"},
    param_extensions={"debug": "true", "version": "v2"},
    body_extensions={"metadata": {"client": "python-postman"}}
)

result = await executor.execute_request(
    request,
    context,
    extensions=extensions
)
```

### Authentication

```python
# Authentication is handled automatically based on collection/request auth settings

# Bearer Token
context = ExecutionContext(
    environment_variables={"bearer_token": "eyJhbGciOiJIUzI1NiIs..."}
)

# Basic Auth
context = ExecutionContext(
    environment_variables={
        "username": "admin",
        "password": "secret123"
    }
)

# API Key
context = ExecutionContext(
    environment_variables={"api_key": "sk-1234567890abcdef"}
)

# Auth is applied automatically during request execution
result = await executor.execute_request(request, context)
```

### Request Methods on Models

```python
# Execute requests directly from Request objects
request = collection.get_request_by_name("Health Check")

# Async execution
result = await request.execute(
    executor=executor,
    context=context,
    substitutions={"env": "staging"}
)

# Sync execution
result = request.execute_sync(
    executor=executor,
    context=context
)

# Execute collections directly
result = await collection.execute(
    executor=executor,
    parallel=True
)
```

### Error Handling

```python
from python_postman.execution import (
    ExecutionError,
    RequestExecutionError,
    VariableResolutionError,
    AuthenticationError
)

try:
    result = await executor.execute_request(request, context)
    if not result.success:
        print(f"Request failed: {result.error}")
except VariableResolutionError as e:
    print(f"Variable error: {e}")
except AuthenticationError as e:
    print(f"Auth error: {e}")
except RequestExecutionError as e:
    print(f"Execution error: {e}")
```

## API Reference

### Main Classes

- **`PythonPostman`**: Main entry point for loading collections
- **`Collection`**: Represents a complete Postman collection
- **`Request`**: Individual HTTP request
- **`Folder`**: Container for organizing requests and sub-folders
- **`Variable`**: Collection, folder, or request-level variables
- **`Auth`**: Authentication configuration
- **`Event`**: Pre-request and test script definitions (text only, execution not supported)

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

### 0.8.0 (Updated version)

- Updated version to 0.8.0
- Updated README.md
- Updated pyproject.toml
- Updated tests
- Updated docs
- Updated examples
- Updated code

## Support

If you encounter any issues or have questions, please file an issue on the [GitHub issue tracker](https://github.com/python-postman/python-postman/issues).

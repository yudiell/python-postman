# Python Postman - User Guide

A comprehensive Python library for working with Postman collections. Parse, inspect, modify, search, analyze, and execute Postman `collection.json` files with a clean, object-oriented API.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Loading Collections](#loading-collections)
- [Accessing Collection Information](#accessing-collection-information)
- [Working with Requests](#working-with-requests)
- [Working with Folders](#working-with-folders)
- [Working with URLs](#working-with-urls)
- [Working with Headers](#working-with-headers)
- [Working with Request Bodies](#working-with-request-bodies)
- [Working with Variables](#working-with-variables)
- [Authentication](#authentication)
- [Events and Scripts](#events-and-scripts)
- [Example Responses](#example-responses)
- [Validation](#validation)
- [Search and Filtering](#search-and-filtering)
- [Collection Statistics](#collection-statistics)
- [Introspection](#introspection)
- [Creating and Modifying Collections](#creating-and-modifying-collections)
- [Serialization](#serialization)
- [Executing HTTP Requests](#executing-http-requests)
- [Variable Resolution at Runtime](#variable-resolution-at-runtime)
- [Request Extensions](#request-extensions)
- [Collection and Folder Execution](#collection-and-folder-execution)
- [Error Handling](#error-handling)
- [Complete Workflow Example](#complete-workflow-example)

---

## Installation

### Core (parsing, analysis, and modification only -- zero dependencies)

```bash
pip install python-postman
```

### With HTTP execution support

```bash
pip install python-postman[execution]
```

This additionally installs `httpx` (>=0.28.1) and `python-dotenv` (>=1.0.0).

### Requirements

- Python 3.9 or higher
- Postman Collection v2.0.0 or v2.1.0 format

---

## Quick Start

```python
from python_postman import PythonPostman

# Load a Postman collection
collection = PythonPostman.from_file("my_api.collection.json")

# Print basic info
print(f"Collection: {collection.info.name}")
print(f"Requests: {len(list(collection.get_requests()))}")

# Iterate through all requests
for request in collection.get_requests():
    print(f"  {request.method} {request.url.to_string()} - {request.name}")
```

---

## Loading Collections

The `PythonPostman` class is the main entry point. It provides three ways to load a collection:

### From a file

```python
from python_postman import PythonPostman

collection = PythonPostman.from_file("path/to/collection.json")
```

### From a JSON string

```python
json_string = '{"info": {"name": "My API"}, "item": []}'
collection = PythonPostman.from_json(json_string)
```

### From a dictionary

```python
collection_dict = {
    "info": {"name": "My API", "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"},
    "item": []
}
collection = PythonPostman.from_dict(collection_dict)
```

All three methods validate the collection automatically on load. If the collection structure is invalid, a `CollectionValidationError` is raised.

---

## Accessing Collection Information

```python
# Collection metadata
print(collection.info.name)          # "My API"
print(collection.info.description)   # "API description"
print(collection.info.schema)        # Schema URL

# Schema version (auto-detected)
print(collection.schema_version)     # SchemaVersion.V2_1_0

# Top-level items (requests and folders)
print(len(collection.items))         # Number of top-level items
```

---

## Working with Requests

### Listing and finding requests

```python
# Get a flat list of all request names
names = collection.list_requests()
print(names)  # ["Login", "Get Users", "Create User", ...]

# Iterate through all requests (flattens nested folders)
for request in collection.get_requests():
    print(f"{request.method} {request.name}")

# Find a specific request by name
login = collection.get_request_by_name("Login")
if login:
    print(f"Found: {login.method} {login.url.to_string()}")
```

### Request properties

```python
request = collection.get_request_by_name("Create User")

# Basic properties
request.name           # "Create User"
request.method         # "POST"
request.description    # Optional description text
request.url            # Url object
request.headers        # List of Header objects
request.body           # Body object or None
request.auth           # Auth object or None
request.events         # List of Event objects (scripts)
request.responses      # List of ExampleResponse objects
```

### Convenience methods on Request

```python
request.has_body()              # True if the request has body content
request.has_auth()              # True if request-level auth is set
request.has_headers()           # True if request has headers
request.has_prerequest_script() # True if a pre-request script exists
request.has_test_script()       # True if a test script exists
request.get_content_type()      # Returns Content-Type header value or None

# HTTP method characteristics
request.is_safe()               # True for GET, HEAD, OPTIONS
request.is_idempotent()         # True for GET, HEAD, PUT, DELETE, OPTIONS
request.is_cacheable()          # True for GET, HEAD
```

---

## Working with Folders

Folders organize requests into groups. They can be nested.

```python
# Access top-level items and check their type
for item in collection.items:
    if isinstance(item, Folder):
        print(f"Folder: {item.name} ({len(item.items)} items)")
    else:
        print(f"Request: {item.name}")

# Find a folder by name (searches recursively)
auth_folder = collection.get_folder_by_name("Authentication")
if auth_folder:
    print(f"Folder: {auth_folder.name}")
    print(f"Description: {auth_folder.description}")

    # Get all requests in this folder and its subfolders
    for request in auth_folder.get_requests():
        print(f"  {request.method} {request.name}")

    # Get only direct subfolders
    subfolders = auth_folder.get_subfolders()
    for subfolder in subfolders:
        print(f"  Subfolder: {subfolder.name}")
```

### Folder properties

```python
folder.name         # Folder name
folder.description  # Optional description
folder.items        # List of items (Requests and Folders)
folder.auth         # Optional folder-level auth
folder.events       # Optional folder-level events (scripts)
folder.variables    # Optional folder-level variables
```

---

## Working with URLs

The `Url` object represents a parsed URL with all its components.

### Accessing URL components

```python
url = request.url

url.raw         # Original raw URL string
url.protocol    # "https"
url.host        # ["api", "example", "com"] (list of segments)
url.path        # ["v1", "users", ":userId"] (list of segments)
url.port        # "443" or None
url.query       # List of QueryParam objects
url.hash        # URL fragment or None
url.variable    # List of path variable definitions
```

### Converting to string

```python
# Get the URL as a string (uses raw URL if available)
url_string = url.to_string()

# Get the URL with variables resolved
url_string = url.to_string(
    resolve_variables=True,
    variable_context={"base_url": "https://api.example.com", "userId": "123"}
)
```

### Working with query parameters

```python
# Add a query parameter
url.add_query_param("page", "1", description="Page number")

# Get a query parameter
param = url.get_query_param("page")
if param:
    print(f"{param.key}={param.value}")  # "page=1"

# Remove a query parameter
url.remove_query_param("page")

# Access all query parameters
for param in url.query:
    if not param.disabled:
        print(f"  {param.key}={param.value}")
```

### Extracting path variables

```python
# Get all path variable names from the URL
# Detects both {{variable}} and :variable formats
path_vars = url.get_path_variables()
print(path_vars)  # ["userId", "base_url"]
```

### Creating URLs

```python
from python_postman import Url

# From a string
url = Url.from_string("https://api.example.com/v1/users?page=1")

# From components
url = Url(
    protocol="https",
    host=["api", "example", "com"],
    path=["v1", "users"],
    query=[QueryParam(key="page", value="1")]
)
```

---

## Working with Headers

### Accessing request headers

```python
for header in request.headers:
    if header.is_active():
        print(f"{header.key}: {header.value}")
```

### Header properties

```python
header.key          # Header name, e.g. "Content-Type"
header.value        # Header value, e.g. "application/json"
header.description  # Optional description
header.disabled     # True if the header is disabled

header.is_active()          # True if not disabled and has a key
header.is_standard_header() # True if it's a recognized HTTP header
header.normalize_key()      # Returns "Content-Type" (Title-Case)
```

### Resolving variables in headers

```python
# Get header value with variable substitution
effective_value = header.get_effective_value(
    variable_context={"api_key": "sk-123456"}
)
# If header.value is "Bearer {{api_key}}", returns "Bearer sk-123456"
```

### Using HeaderCollection

The `HeaderCollection` class provides a higher-level interface for managing groups of headers:

```python
from python_postman import HeaderCollection, Header

headers = HeaderCollection([
    Header(key="Content-Type", value="application/json"),
    Header(key="Authorization", value="Bearer {{token}}")
])

# Get a header (case-insensitive)
ct = headers.get("content-type")

# Set or update a header
headers.set("X-Request-ID", "req-12345")

# Remove a header
headers.remove("Authorization")

# Convert to a dict suitable for HTTP requests
http_dict = headers.to_http_dict(variable_context={"token": "abc123"})
# {"Content-Type": "application/json", "X-Request-ID": "req-12345"}
```

---

## Working with Request Bodies

The `Body` object supports multiple content types.

### Body modes

```python
from python_postman import BodyMode

# Available modes:
BodyMode.RAW          # Raw text (JSON, XML, text, etc.)
BodyMode.URLENCODED   # application/x-www-form-urlencoded
BodyMode.FORMDATA     # multipart/form-data
BodyMode.FILE         # File upload
BodyMode.BINARY       # Binary data
BodyMode.GRAPHQL      # GraphQL queries
```

### Reading body content

```python
body = request.body

if body:
    print(f"Mode: {body.mode}")        # "raw", "formdata", etc.
    print(f"Active: {body.is_active()}")

    # Get the body mode as enum
    mode = body.get_mode()             # BodyMode.RAW

    # Get content type header for this body
    content_type = body.get_content_type()  # "application/json"

    # Get body content (mode-aware)
    content = body.get_content()
    # Returns: str for raw, dict for urlencoded, list of tuples for formdata
```

### Raw body

```python
if body.mode == "raw":
    print(body.raw)  # Raw content string (JSON, XML, text, etc.)

    # Check body options for language hint
    language = body.options.get("raw", {}).get("language")  # "json", "xml", etc.
```

### Form data

```python
if body.mode == "formdata":
    for param in body.formdata:
        if param.is_active():
            print(f"{param.key}: {param.value}")
            if param.is_file():
                print(f"  File source: {param.src}")

# Similarly for URL-encoded
if body.mode == "urlencoded":
    for param in body.urlencoded:
        print(f"{param.key}={param.value}")
```

### Modifying body parameters

```python
# Add a form parameter
body.add_form_parameter("email", "user@example.com")

# Add a file parameter
body.add_form_parameter("avatar", None, param_type="file")

# Remove a form parameter
body.remove_form_parameter("email")

# Get a specific parameter
param = body.get_form_parameter("email")
```

---

## Working with Variables

Variables are defined at collection, folder, or request level and use `{{variable_name}}` syntax.

### Accessing collection variables

```python
# As a list of Variable objects
for var in collection.variables:
    if not var.disabled:
        print(f"{var.key} = {var.value} (type: {var.type})")

# As a key-value dictionary (excludes disabled variables)
variables = collection.get_variables()
print(variables)  # {"base_url": "https://api.example.com", "api_version": "v1"}
```

### Variable properties

```python
var.key          # Variable name
var.value        # Variable value (any type)
var.type         # Optional type string ("string", "boolean", "number")
var.description  # Optional description
var.disabled     # True if variable is disabled

# Get type as enum (inferred from value if not set)
var_type = var.get_type()  # VariableType.STRING

# Resolve nested variable references
resolved = var.resolve_value(context={"env": "production"})
# If var.value is "{{env}}.api.com", returns "production.api.com"
```

### Folder-level variables

```python
folder = collection.get_folder_by_name("Users")
if folder and folder.variables:
    for var in folder.variables:
        print(f"Folder variable: {var.key} = {var.value}")
```

---

## Authentication

Authentication can be set at the collection, folder, or request level. Lower levels override higher ones (request > folder > collection).

### Supported auth types

- `bearer` -- Bearer token
- `basic` -- Basic authentication (username/password)
- `apikey` -- API key (in header or query parameter)
- `oauth1` -- OAuth 1.0
- `oauth2` -- OAuth 2.0
- `digest` -- Digest authentication
- `hawk` -- Hawk authentication
- `ntlm` -- NTLM authentication
- `noauth` -- Explicitly no authentication

### Reading auth configuration

```python
# Collection-level auth
if collection.auth:
    print(f"Auth type: {collection.auth.type}")  # "bearer"

    # Type-checking helpers
    collection.auth.is_bearer_auth()   # True
    collection.auth.is_basic_auth()    # False
    collection.auth.is_api_key_auth()  # False

# Auth parameters
for param in collection.auth.parameters:
    print(f"  {param.key}: {param.value}")
```

### Getting credentials by auth type

```python
auth = request.auth

# Bearer token
if auth and auth.is_bearer_auth():
    token = auth.get_bearer_token()
    print(f"Token: {token}")

# Basic auth
if auth and auth.is_basic_auth():
    credentials = auth.get_basic_credentials()
    print(f"Username: {credentials['username']}")
    print(f"Password: {credentials['password']}")

# API key
if auth and auth.is_api_key_auth():
    config = auth.get_api_key_config()
    print(f"Key: {config['key']}")
    print(f"Value: {config['value']}")
    print(f"Location: {config['in']}")  # "header" or "query"
```

### Auth parameter manipulation

```python
# Get a specific parameter value
token = auth.get_parameter("token")

# Get all parameters as a dict
params = auth.get_parameter_dict()

# Add or update a parameter
auth.add_parameter("token", "new-token-value")

# Remove a parameter
auth.remove_parameter("token")
```

### Resolving effective auth (inheritance)

A request may inherit authentication from its parent folder or the collection. Use the introspection module to resolve the effective auth:

```python
# Using the request's stored hierarchy references
resolved = request.get_effective_auth()
print(f"Auth type: {resolved.auth.type if resolved.auth else 'None'}")
print(f"Source: {resolved.source.value}")  # "request", "folder", or "collection"
print(f"Path: {' > '.join(resolved.path)}")

# Or use AuthResolver directly
from python_postman.introspection import AuthResolver

resolved = AuthResolver.resolve_auth(request, parent_folder, collection)
```

---

## Events and Scripts

Events represent pre-request scripts and test scripts attached to requests, folders, or the collection.

### Accessing events

```python
# Collection-level events
for event in collection.events:
    print(f"Event type: {event.listen}")  # "prerequest" or "test"
    print(f"Has script: {event.has_script()}")

# Request-level events
for event in request.events:
    if event.is_prerequest():
        print("Pre-request script:")
    elif event.is_test():
        print("Test script:")

    # Get script content as a string
    content = event.get_script_content()
    if content:
        print(content)

    # Get script content as lines
    lines = event.get_script_lines()
```

### Event properties

```python
event.listen     # "prerequest" or "test"
event.script     # Script content (str, list, or dict)
event.disabled   # True if event is disabled

event.is_prerequest()      # True for pre-request events
event.is_test()            # True for test events
event.has_script()         # True if event has non-empty script content
event.get_script_content() # Returns script as a single string
event.get_script_lines()   # Returns script as a list of lines
event.get_script_type()    # Script type from script object (if available)
event.get_script_id()      # Script ID from script object (if available)
```

---

## Example Responses

Postman collections can store example responses alongside requests.

```python
# Access example responses on a request
for response in request.responses:
    print(f"Example: {response.name}")
    print(f"  Status: {response.code} {response.status}")
    print(f"  Body: {response.body[:100] if response.body else 'None'}...")

    # Check response format
    if response.is_json():
        data = response.get_json()
        print(f"  JSON data: {data}")

    # Get cookies from the response
    cookies = response.get_cookies()
    for cookie in cookies:
        print(f"  Cookie: {cookie.name}={cookie.value}")

# Find a specific example response
example = request.get_response_by_name("Success Response")

# Add a new example response
from python_postman import ExampleResponse

new_example = ExampleResponse(
    name="404 Not Found",
    status="Not Found",
    code=404,
    body='{"error": "Resource not found"}'
)
request.add_response(new_example)
```

---

## Validation

### Validating a loaded collection

```python
result = collection.validate()

if result.is_valid:
    print("Collection is valid!")
else:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
```

### Quick validation without full parsing

```python
is_valid = PythonPostman.validate_collection_dict(collection_dict)
print(f"Valid: {is_valid}")
```

### What gets validated

- Collection info has a non-empty name
- All items are valid `Item` instances (Request or Folder)
- All variables have valid keys
- Auth configuration has valid type and required parameters
- Events have valid `listen` type and script structure
- Schema version is a supported Postman format (v2.0.0 or v2.1.0)

---

## Search and Filtering

The search API provides a fluent, chainable interface for finding requests.

### Basic search

```python
# Find all POST requests
results = collection.search().by_method("POST").execute()
for result in results:
    print(f"{result.full_path}: {result.request.method} {result.request.name}")
```

### Available filters

```python
query = collection.search()

# Filter by HTTP method (case-insensitive)
query.by_method("GET")

# Filter by URL pattern (regex)
query.by_url_pattern(r"/api/v\d+/users")

# Filter by host
query.by_host("api.example.com")

# Filter by authentication type
query.by_auth_type("bearer")

# Filter by script presence
query.has_scripts()              # Any script
query.has_scripts("test")        # Test scripts only
query.has_scripts("prerequest")  # Pre-request scripts only

# Filter to a specific folder (recursive)
query.in_folder("User Management")
```

### Chaining multiple filters

```python
results = collection.search() \
    .by_method("POST") \
    .by_url_pattern(r"/users") \
    .by_auth_type("bearer") \
    .in_folder("User Management") \
    .execute()

print(f"Found {len(results)} matching requests")
```

### Search results

Each `SearchResult` contains:

```python
for result in results:
    result.request    # The matched Request object
    result.path       # List of folder/request names, e.g. ["Users", "Create User"]
    result.full_path  # String path, e.g. "Users > Create User"
```

### Using iterators for large collections

```python
# Memory-efficient iteration
for result in collection.search().by_method("GET").execute_iter():
    print(result.request.name)
```

---

## Collection Statistics

Get quantitative analysis of your collection's structure.

```python
stats = collection.get_statistics()

# Collect all statistics at once
data = stats.collect()
print(f"Total requests: {data['total_requests']}")
print(f"Total folders: {data['total_folders']}")
print(f"Max nesting depth: {data['max_nesting_depth']}")
print(f"Avg requests per folder: {data['avg_requests_per_folder']:.1f}")

# Breakdown by HTTP method
by_method = data['requests_by_method']  # {"GET": 10, "POST": 5, ...}

# Breakdown by auth type (resolves inheritance)
by_auth = data['requests_by_auth']  # {"bearer": 8, "none": 7, ...}
```

### Individual statistics methods

```python
stats.count_requests()              # Total request count
stats.count_folders()               # Total folder count (including nested)
stats.get_max_depth()               # Maximum folder nesting depth
stats.count_by_method()             # Dict of method -> count
stats.count_by_auth()               # Dict of auth type -> count
stats.get_avg_requests_per_folder() # Average requests per folder
```

### Exporting statistics

```python
# Export to JSON
json_output = stats.to_json(indent=2)
with open("stats.json", "w") as f:
    f.write(json_output)

# Export to CSV
csv_output = stats.to_csv()
with open("stats.csv", "w") as f:
    f.write(csv_output)
```

### Caching

Statistics are cached after the first `collect()` call. If you modify the collection and need fresh stats:

```python
stats.clear_cache()
fresh_data = stats.collect()
```

---

## Introspection

### Authentication resolver

Trace how authentication is inherited through the collection hierarchy:

```python
from python_postman.introspection import AuthResolver, AuthSource

resolved = AuthResolver.resolve_auth(request, parent_folder, collection)

# Where the auth came from
if resolved.source == AuthSource.REQUEST:
    print("Auth defined on the request itself")
elif resolved.source == AuthSource.FOLDER:
    print("Auth inherited from a parent folder")
elif resolved.source == AuthSource.COLLECTION:
    print("Auth inherited from the collection")
elif resolved.source == AuthSource.NONE:
    print("No authentication configured")

# The hierarchy path
print(f"Path: {' > '.join(resolved.path)}")
# e.g. "My API > Users > Create User"
```

### Variable tracer

Analyze variable definitions and usage across the collection:

```python
from python_postman.introspection import VariableTracer

tracer = VariableTracer(collection)
```

#### Trace where a variable is defined

```python
references = tracer.trace_variable("api_key")
for ref in references:
    print(f"Scope: {ref.scope.value}, Value: {ref.value}, Location: {ref.location}")
```

#### Find variables defined in multiple scopes (shadowed)

```python
shadowed = tracer.find_shadowed_variables()
for var_name, refs in shadowed.items():
    print(f"'{var_name}' is defined in {len(refs)} scopes:")
    for ref in refs:
        print(f"  {ref.scope.value}: {ref.value} at {ref.location}")
```

#### Find variables referenced but never defined

```python
undefined = tracer.find_undefined_references()
if undefined:
    print("Warning: undefined variables found:")
    for var in undefined:
        print(f"  - {var}")
```

#### Find all locations where a variable is used

```python
usage = tracer.find_variable_usage("base_url")
for location in usage:
    print(f"  {location}")
# Output:
#   Users > Get User - URL
#   Users > Create User - URL
#   Auth > Login - Body (raw)
```

---

## Creating and Modifying Collections

### Creating a new collection

```python
collection = PythonPostman.create_collection(
    name="My New API",
    description="API for user management"
)
```

### Adding requests to a collection

```python
from python_postman import Request, Url, Header, Body, Auth, AuthParameter

# Create a request
request = Request(
    name="Get Users",
    method="GET",
    url=Url.from_string("https://api.example.com/v1/users"),
    headers=[
        Header(key="Accept", value="application/json"),
    ]
)

# Add it to the collection
collection.items.append(request)
```

### Creating a folder with requests

```python
from python_postman import Folder

folder = Folder(
    name="User Management",
    items=[
        Request(
            name="List Users",
            method="GET",
            url=Url.from_string("{{base_url}}/users")
        ),
        Request(
            name="Create User",
            method="POST",
            url=Url.from_string("{{base_url}}/users"),
            body=Body(mode="raw", raw='{"name": "John", "email": "john@example.com"}'),
            headers=[Header(key="Content-Type", value="application/json")]
        ),
    ],
    description="Endpoints for user CRUD operations"
)

collection.items.append(folder)
```

### Modifying existing requests

```python
# Find and modify a request
request = collection.get_request_by_name("Get Users")
if request:
    # Update URL host
    request.url.host = ["staging", "api", "example", "com"]

    # Add a header
    request.headers.append(Header(key="X-Environment", value="staging"))

    # Set authentication
    request.auth = Auth(
        type="bearer",
        parameters=[AuthParameter(key="token", value="{{auth_token}}")]
    )
```

### Adding collection-level variables

```python
from python_postman import Variable

collection.variables.append(Variable(key="base_url", value="https://api.example.com"))
collection.variables.append(Variable(key="api_version", value="v1"))
```

---

## Serialization

### Convert to dictionary

```python
collection_dict = collection.to_dict()
```

### Convert to JSON

```python
# Compact JSON
json_string = collection.to_json()

# Pretty-printed JSON
json_string = collection.to_json(indent=2)

# Save to file
with open("output_collection.json", "w") as f:
    f.write(collection.to_json(indent=2))
```

All model objects (`Request`, `Folder`, `Url`, `Header`, `Body`, `Auth`, `Event`, `Variable`, etc.) also have `to_dict()` methods.

---

## Executing HTTP Requests

> **Requires**: `pip install python-postman[execution]`

The execution layer allows you to run HTTP requests defined in your collection against live APIs.

### Check execution availability

```python
from python_postman import is_execution_available

if is_execution_available():
    print("Execution features available")
else:
    print("Install httpx: pip install python-postman[execution]")
```

### Basic async execution

```python
import asyncio
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

async def main():
    collection = PythonPostman.from_file("api_collection.json")

    # Create an executor
    executor = RequestExecutor(
        client_config={"timeout": 30.0, "verify": True},
        global_headers={"User-Agent": "python-postman/1.0"}
    )

    # Create a context with variables
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
        print(f"Body: {result.response.text}")
        print(f"Duration: {result.response.elapsed_ms:.2f}ms")
    else:
        print(f"Error: {result.error}")

    # Clean up
    await executor.aclose()

asyncio.run(main())
```

### Synchronous execution

```python
from python_postman.execution import RequestExecutor, ExecutionContext

with RequestExecutor() as executor:
    context = ExecutionContext(
        environment_variables={"base_url": "https://httpbin.org"}
    )

    result = executor.execute_request_sync(request, context)
    if result.success:
        print(f"Status: {result.response.status_code}")
```

### Using context managers

```python
# Async
async with RequestExecutor() as executor:
    result = await executor.execute_request(request, context)

# Sync
with RequestExecutor() as executor:
    result = executor.execute_request_sync(request, context)
```

### Executing directly from model objects

Requests and collections have convenience `execute` methods:

```python
# Async execution from a request object
result = await request.execute(
    executor=executor,
    context=context,
    substitutions={"user_id": "123"}
)

# Sync execution from a request object
result = request.execute_sync(
    executor=executor,
    context=context
)

# Execute an entire collection
result = await collection.execute(
    executor=executor,
    parallel=True
)
```

### RequestExecutor configuration

```python
executor = RequestExecutor(
    # httpx client options (timeout, SSL verification, redirects, etc.)
    client_config={
        "timeout": 30.0,          # Request timeout in seconds
        "verify": True,           # SSL certificate verification
        "follow_redirects": True, # Follow HTTP redirects
    },

    # Global variable overrides (highest precedence)
    variable_overrides={"env": "production"},

    # Headers added to every request
    global_headers={"User-Agent": "my-app/1.0", "X-Client": "python-postman"},

    # Script execution timeout in seconds
    script_timeout=30.0,

    # Delay between sequential requests (seconds)
    request_delay=0.1,
)
```

### Reading execution results

```python
result = await executor.execute_request(request, context)

# Check success
result.success           # True if no error and response received
result.status_code       # HTTP status code (or None on error)
result.execution_time_ms # Total execution time including scripts

# Access the response
response = result.response
response.status_code     # 200
response.text            # Response body as text
response.json            # Response body parsed as JSON
response.content         # Response body as bytes
response.headers         # Response headers as dict
response.elapsed_ms      # HTTP request duration in milliseconds
response.url             # Final request URL
response.request_method  # HTTP method used

# Response status helpers
response.is_success()       # True for 2xx
response.is_redirect()      # True for 3xx
response.is_client_error()  # True for 4xx
response.is_server_error()  # True for 5xx

# Access test script results
if result.test_results:
    print(f"Tests passed: {result.test_results.passed}")
    print(f"Tests failed: {result.test_results.failed}")
    print(f"Success rate: {result.test_results.success_rate:.0%}")

    for assertion in result.test_results.assertions:
        status = "PASS" if assertion.passed else "FAIL"
        print(f"  {status}: {assertion.name}")
```

### Authentication during execution

Authentication is processed automatically during request execution based on the collection's auth configuration. You supply credential values through the execution context:

```python
# Bearer token
context = ExecutionContext(
    environment_variables={"bearer_token": "eyJhbGciOiJIUzI1NiIs..."}
)

# Basic auth
context = ExecutionContext(
    environment_variables={"username": "admin", "password": "secret"}
)

# API key
context = ExecutionContext(
    environment_variables={"api_key": "sk-1234567890abcdef"}
)

# Auth is resolved and applied automatically
result = await executor.execute_request(request, context)
```

---

## Variable Resolution at Runtime

The `ExecutionContext` manages variables with scoped precedence: **request > folder > collection > environment**.

### Creating a context

```python
from python_postman.execution import ExecutionContext

context = ExecutionContext(
    environment_variables={"env": "production", "base_url": "https://api.example.com"},
    collection_variables={"api_version": "v1", "timeout": "30"},
    folder_variables={"endpoint": "/users"},
    request_variables={"user_id": "12345"}
)
```

### Getting and setting variables

```python
# Get a variable (follows precedence order)
value = context.get_variable("user_id")       # "12345" (from request scope)
value = context.get_variable("base_url")       # "https://api.example.com" (from environment)

# Check if a variable exists
exists = context.has_variable("api_key")

# Set a variable in a specific scope
context.set_variable("session_token", "abc123", "environment")
context.set_variable("request_id", "req-001", "request")

# Get all variables merged with proper precedence
all_vars = context.get_all_variables()

# Clear all variables in a scope
context.clear_scope("request")
```

### Resolving variables in strings

The context resolves both `{{variable}}` (Postman-style) and `:variable` (path parameter) syntax:

```python
# Postman-style variables
url = context.resolve_variables("{{base_url}}/{{api_version}}/users/{{user_id}}")
# "https://api.example.com/v1/users/12345"

# Path parameters
url = context.resolve_variables("{{base_url}}/users/:user_id/datasets/:datasetId")
# Variables user_id and datasetId are resolved from context

# Nested variable resolution
context = ExecutionContext(
    environment_variables={"env": "prod"},
    collection_variables={"host": "{{env}}.api.example.com"}
)
resolved = context.resolve_variables("https://{{host}}/api")
# "https://prod.api.example.com/api"
```

### Creating child contexts

```python
# Create a child context with additional request-level variables
child = context.create_child_context(
    request_variables={"request_id": "req-999"}
)
```

---

## Request Extensions

Request extensions allow you to modify requests at runtime without changing the original collection. They support both **substitution** (replacing existing values) and **extension** (adding new values).

```python
from python_postman.execution import RequestExtensions

extensions = RequestExtensions(
    # Replace existing URL components
    url_substitutions={"host": "staging.api.example.com", "protocol": "http"},

    # Replace existing header values
    header_substitutions={"Authorization": "Bearer {{new_token}}"},

    # Add new headers
    header_extensions={"X-Request-ID": "req-{{timestamp}}", "X-Debug": "true"},

    # Replace existing query parameter values
    param_substitutions={"version": "v2"},

    # Add new query parameters
    param_extensions={"debug": "true", "format": "json"},

    # Modify body content (works with JSON bodies)
    body_substitutions={"old_field": "new_value"},
    body_extensions={"metadata": {"client": "python-postman"}},

    # Modify auth parameters
    auth_substitutions={"token": "{{fresh_token}}"},
)

# Apply during execution
result = await executor.execute_request(request, context, extensions=extensions)
```

### Checking for modifications

```python
if extensions.has_modifications():
    print("Extensions will modify the request")
```

---

## Collection and Folder Execution

### Execute an entire collection

```python
# Sequential execution (preserves order)
result = await executor.execute_collection(collection, context=context)

# Parallel execution (faster, order not guaranteed)
result = await executor.execute_collection(
    collection,
    context=context,
    parallel=True
)

# Stop on first error
result = await executor.execute_collection(
    collection,
    context=context,
    stop_on_error=True
)
```

### Execute a folder

```python
folder = collection.get_folder_by_name("User Tests")
result = await executor.execute_folder(folder, context, parallel=True)
```

### Reading collection/folder execution results

```python
print(f"Collection: {result.collection_name}")
print(f"Total: {result.total_requests}")
print(f"Passed: {result.successful_requests}")
print(f"Failed: {result.failed_requests}")
print(f"Success rate: {result.success_rate:.0%}")
print(f"Duration: {result.total_time_ms:.0f}ms")

# Iterate individual results
for exec_result in result.results:
    if exec_result.success:
        print(f"  OK: {exec_result.request.name} ({exec_result.response.status_code})")
    else:
        print(f"  FAIL: {exec_result.request.name} - {exec_result.error}")

# Aggregated test results
tests = result.test_results
print(f"Tests: {tests.passed} passed, {tests.failed} failed")
```

---

## Error Handling

### Parsing errors

```python
from python_postman import (
    PostmanCollectionError,      # Base exception for all errors
    CollectionParseError,        # JSON parsing errors
    CollectionValidationError,   # Structure validation errors
    CollectionFileError,         # File I/O errors
)

try:
    collection = PythonPostman.from_file("collection.json")
except CollectionFileError as e:
    print(f"Could not read file: {e}")
except CollectionParseError as e:
    print(f"Invalid JSON: {e}")
except CollectionValidationError as e:
    print(f"Invalid collection structure: {e}")
```

### Execution errors

```python
from python_postman.execution import (
    ExecutionError,            # Base execution error
    RequestExecutionError,     # HTTP request failed
    VariableResolutionError,   # Variable not found or circular reference
    ScriptExecutionError,      # Script failed to run
    AuthenticationError,       # Authentication processing failed
    ExecutionTimeoutError,     # Request or script timed out
)

try:
    result = await executor.execute_request(request, context)
    if not result.success:
        print(f"Request failed: {result.error}")
except ExecutionTimeoutError as e:
    print(f"Timeout ({e.timeout_type}): {e}")
except VariableResolutionError as e:
    print(f"Missing variable '{e.variable_name}': {e}")
except AuthenticationError as e:
    print(f"Auth error ({e.auth_type}): {e}")
except RequestExecutionError as e:
    print(f"HTTP error: {e}")
```

### All exceptions carry a `details` dictionary

```python
try:
    collection = PythonPostman.from_file("bad.json")
except PostmanCollectionError as e:
    print(f"Error: {e}")
    print(f"Details: {e.details}")
```

---

## Complete Workflow Example

This example demonstrates a full parse-inspect-modify-execute pipeline:

```python
import asyncio
from python_postman import PythonPostman, Header, Auth, AuthParameter
from python_postman.execution import RequestExecutor, ExecutionContext
from python_postman.introspection import AuthResolver, VariableTracer

async def main():
    # --- 1. PARSE ---
    collection = PythonPostman.from_file("api_collection.json")
    print(f"Loaded: {collection.info.name}")

    # --- 2. INSPECT ---
    # Validate structure
    validation = collection.validate()
    assert validation.is_valid, f"Invalid: {validation.errors}"

    # Analyze statistics
    stats = collection.get_statistics()
    data = stats.collect()
    print(f"Requests: {data['total_requests']}, Folders: {data['total_folders']}")
    print(f"Methods: {data['requests_by_method']}")

    # Check for undefined variables
    tracer = VariableTracer(collection)
    undefined = tracer.find_undefined_references()
    if undefined:
        print(f"Warning: undefined variables: {undefined}")

    # Search for specific requests
    post_requests = collection.search().by_method("POST").execute()
    print(f"Found {len(post_requests)} POST requests")

    # --- 3. MODIFY ---
    # Add a custom header to all requests
    for request in collection.get_requests():
        request.headers.append(Header(key="X-Environment", value="staging"))

    # Save the modified collection
    with open("modified.json", "w") as f:
        f.write(collection.to_json(indent=2))

    # --- 4. EXECUTE ---
    context = ExecutionContext(
        environment_variables={
            "base_url": "https://staging.api.example.com",
            "api_key": "test-key-12345"
        },
        collection_variables=collection.get_variables()
    )

    async with RequestExecutor(
        client_config={"timeout": 30.0},
        global_headers={"User-Agent": "test-suite/1.0"}
    ) as executor:
        result = await executor.execute_collection(collection, context=context)

        # --- 5. REPORT ---
        print(f"\nExecution Results:")
        print(f"  Total: {result.total_requests}")
        print(f"  Passed: {result.successful_requests}")
        print(f"  Failed: {result.failed_requests}")
        print(f"  Duration: {result.total_time_ms:.0f}ms")

        for r in result.results:
            status = f"{r.response.status_code}" if r.success else "ERROR"
            print(f"  [{status}] {r.request.name} ({r.execution_time_ms:.0f}ms)")

asyncio.run(main())
```

---

## API Quick Reference

### Entry Points

| Method | Description |
|---|---|
| `PythonPostman.from_file(path)` | Load collection from a JSON file |
| `PythonPostman.from_json(string)` | Load collection from a JSON string |
| `PythonPostman.from_dict(dict)` | Load collection from a dictionary |
| `PythonPostman.create_collection(name)` | Create a new empty collection |
| `PythonPostman.validate_collection_dict(dict)` | Quick-validate a dictionary |

### Collection

| Method / Property | Description |
|---|---|
| `collection.info` | Collection metadata (`CollectionInfo`) |
| `collection.items` | Top-level items (requests and folders) |
| `collection.variables` | Collection-level variables |
| `collection.auth` | Collection-level authentication |
| `collection.events` | Collection-level events |
| `collection.get_requests()` | Iterator over all requests (recursive) |
| `collection.list_requests()` | List of all request names |
| `collection.get_request_by_name(name)` | Find a request by name |
| `collection.get_folder_by_name(name)` | Find a folder by name |
| `collection.get_variables()` | Variables as a dict |
| `collection.validate()` | Validate collection structure |
| `collection.search()` | Start a search query |
| `collection.get_statistics()` | Get statistics analyzer |
| `collection.to_dict()` | Convert to dictionary |
| `collection.to_json(indent)` | Convert to JSON string |
| `collection.execute(...)` | Execute all requests (async) |
| `collection.create_executor(...)` | Create a configured executor |

### Request

| Method / Property | Description |
|---|---|
| `request.name` | Request name |
| `request.method` | HTTP method |
| `request.url` | URL object |
| `request.headers` | List of headers |
| `request.body` | Body object |
| `request.auth` | Auth object |
| `request.events` | List of events |
| `request.responses` | List of example responses |
| `request.has_body()` | Check for body content |
| `request.has_auth()` | Check for auth |
| `request.has_headers()` | Check for headers |
| `request.has_prerequest_script()` | Check for pre-request script |
| `request.has_test_script()` | Check for test script |
| `request.get_content_type()` | Get Content-Type header |
| `request.get_effective_auth()` | Resolve inherited auth |
| `request.execute(...)` | Execute request (async) |
| `request.execute_sync(...)` | Execute request (sync) |

### Execution

| Class | Description |
|---|---|
| `RequestExecutor` | Main execution engine |
| `ExecutionContext` | Variable scoping and resolution |
| `RequestExtensions` | Runtime request modifications |
| `ExecutionResult` | Single request result |
| `CollectionExecutionResult` | Collection execution result |
| `FolderExecutionResult` | Folder execution result |
| `ExecutionResponse` | HTTP response wrapper |
| `ScriptResults` | Test script results |

---

## Supported Postman Collection Formats

- Postman Collection v2.0.0
- Postman Collection v2.1.0

> **Note**: Postman Collection v1.0.0 is not supported. Export your collection as v2.1.0 from Postman.

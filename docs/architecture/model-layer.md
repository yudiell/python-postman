# Model Layer Documentation

## Overview

The model layer is the core of python-postman, responsible for parsing, representing, and manipulating Postman collections as Python objects. This layer has no external dependencies and can be used independently for collection analysis, validation, and transformation.

## Core Concepts

### Collections as Object Graphs

A Postman collection is represented as a hierarchical object graph:

```
Collection
├── CollectionInfo (metadata)
├── Auth (optional)
├── Variables []
└── Items []
    ├── Request
    │   ├── Url
    │   ├── Headers []
    │   ├── Body (optional)
    │   ├── Auth (optional)
    │   ├── Events [] (scripts)
    │   └── Responses [] (examples)
    └── Folder
        ├── Auth (optional)
        └── Items [] (recursive)
```

## Key Classes

### PythonPostman (Parser)

Entry point for loading collections.

```python
from python_postman import PythonPostman

# Parse from file
parser = PythonPostman()
collection = parser.parse("collection.json")

# Parse from dictionary
collection = parser.parse_dict(json_data)
```

**Key Methods:**

- `parse(file_path)` - Parse collection from file
- `parse_dict(data)` - Parse collection from dictionary
- `validate(collection)` - Validate collection structure

### Collection

Represents a complete Postman collection.

```python
# Access collection metadata
print(collection.info.name)
print(collection.info.description)

# Access items (requests and folders)
for item in collection.items:
    if isinstance(item, Request):
        print(f"Request: {item.name}")
    elif isinstance(item, Folder):
        print(f"Folder: {item.name}")

# Get all requests (flattened)
all_requests = collection.get_requests()

# Search for specific requests
results = collection.search().by_method("POST").execute()

# Validate collection
validation_result = collection.validate()
if not validation_result.is_valid:
    for error in validation_result.errors:
        print(f"Error: {error}")
```

**Key Attributes:**

- `info` - Collection metadata (CollectionInfo)
- `items` - Top-level items (List[Request | Folder])
- `auth` - Collection-level authentication
- `variables` - Collection variables
- `schema_version` - Detected schema version

**Key Methods:**

- `get_requests()` - Get all requests (flattened)
- `get_folders()` - Get all folders (flattened)
- `search()` - Create search query builder
- `validate()` - Validate collection structure
- `to_dict()` - Serialize to dictionary
- `to_json()` - Serialize to JSON string

### Request

Represents an HTTP request.

```python
request = collection.items[0]

# Access request properties
print(request.name)
print(request.method)
print(request.url.to_string())

# Check request characteristics
if request.has_body():
    print(f"Body mode: {request.body.mode}")
    print(f"Body content: {request.body.raw}")

if request.has_auth():
    print(f"Auth type: {request.auth.type}")

# Get effective authentication (with inheritance)
resolved_auth = request.get_effective_auth(parent_folder, collection)
print(f"Auth source: {resolved_auth.source}")

# Access headers
for header in request.headers:
    print(f"{header.key}: {header.value}")

# Access example responses
for response in request.responses:
    print(f"Example: {response.name} - {response.code}")
```

**Key Attributes:**

- `name` - Request name
- `method` - HTTP method (GET, POST, etc.)
- `url` - Url object
- `headers` - List of Header objects
- `body` - Body object (optional)
- `auth` - Auth object (optional)
- `events` - List of Event objects (scripts)
- `responses` - List of ExampleResponse objects

**Key Methods:**

- `has_body()` - Check if request has body
- `has_auth()` - Check if request has authentication
- `has_headers()` - Check if request has headers
- `has_prerequest_script()` - Check for pre-request script
- `has_test_script()` - Check for test script
- `get_content_type()` - Get Content-Type header
- `is_idempotent()` - Check if method is idempotent
- `is_cacheable()` - Check if method is cacheable
- `is_safe()` - Check if method is safe
- `get_effective_auth()` - Resolve authentication with inheritance
- `add_response()` - Add example response
- `get_response_by_name()` - Find example response by name

### Folder

Represents a folder containing requests and other folders.

```python
folder = collection.items[0]

# Access folder properties
print(folder.name)
print(folder.description)

# Iterate through folder items
for item in folder.items:
    print(item.name)

# Folder-level authentication
if folder.auth:
    print(f"Folder auth: {folder.auth.type}")
```

**Key Attributes:**

- `name` - Folder name
- `description` - Folder description
- `items` - List of Request and Folder objects
- `auth` - Folder-level authentication (optional)

**Key Methods:**

- `add_item()` - Add request or folder
- `get_requests()` - Get all requests in folder (recursive)
- `get_folders()` - Get all subfolders (recursive)

### Url

Represents a request URL with components.

```python
url = request.url

# Access URL components
print(url.protocol)  # http, https
print(url.host)      # api.example.com
print(url.port)      # 443
print(url.path)      # /v1/users

# Get full URL string
full_url = url.to_string()

# Access query parameters
for param in url.query:
    print(f"{param.key}={param.value}")

# Create URL from string
url = Url.from_string("https://api.example.com/v1/users?page=1")
```

**Key Attributes:**

- `protocol` - Protocol (http, https)
- `host` - Host/domain
- `port` - Port number
- `path` - URL path segments
- `query` - Query parameters
- `raw` - Raw URL string

**Key Methods:**

- `to_string()` - Convert to full URL string
- `from_string()` - Create from URL string (class method)

### Auth

Represents authentication configuration.

```python
auth = request.auth

# Access auth properties
print(auth.type)  # basic, bearer, apikey, oauth1, oauth2

# Access auth parameters
for param in auth.parameters:
    print(f"{param.key}: {param.value}")

# Get specific parameter
api_key = auth.get_parameter("apiKey")
```

**Key Attributes:**

- `type` - Authentication type
- `parameters` - List of AuthParameter objects

**Key Methods:**

- `get_parameter()` - Get parameter by key
- `set_parameter()` - Set parameter value

### Body

Represents request body.

```python
body = request.body

# Check body mode
print(body.mode)  # raw, urlencoded, formdata, file, graphql

# Access raw body
if body.mode == "raw":
    print(body.raw)

# Access form data
if body.mode == "formdata":
    for param in body.formdata:
        print(f"{param.key}={param.value}")

# Access URL-encoded data
if body.mode == "urlencoded":
    for param in body.urlencoded:
        print(f"{param.key}={param.value}")
```

**Key Attributes:**

- `mode` - Body mode
- `raw` - Raw body content
- `formdata` - Form data parameters
- `urlencoded` - URL-encoded parameters
- `file` - File reference
- `graphql` - GraphQL query

### Response (Example Response)

Represents an example response saved in the collection.

```python
response = request.responses[0]

# Access response properties
print(response.name)
print(response.code)      # 200, 404, etc.
print(response.status)    # OK, Not Found, etc.
print(response.body)

# Access response headers
for header in response.headers:
    print(f"{header.key}: {header.value}")

# Parse JSON body
json_data = response.get_json()

# Access timing information
print(response.response_time)  # milliseconds
```

**Key Attributes:**

- `name` - Example name
- `code` - HTTP status code
- `status` - HTTP status text
- `headers` - Response headers
- `body` - Response body
- `response_time` - Response time in ms

**Key Methods:**

- `get_json()` - Parse body as JSON
- `get_cookies()` - Extract cookies from headers

### Variable

Represents a collection or environment variable.

```python
variable = collection.variables[0]

# Access variable properties
print(variable.key)
print(variable.value)
print(variable.type)  # string, boolean, number, etc.
```

**Key Attributes:**

- `key` - Variable name
- `value` - Variable value
- `type` - Variable type
- `description` - Variable description

### Event (Script)

Represents a pre-request or test script.

```python
for event in request.events:
    print(event.listen)  # prerequest, test
    print(event.script.exec)  # Script code lines
```

**Key Attributes:**

- `listen` - Event type (prerequest, test)
- `script` - Script object with exec (code lines)

## Schema Version Management

The library automatically detects and validates Postman collection schema versions.

```python
from python_postman.models.schema import SchemaVersion, SchemaValidator

# Detect version
version = SchemaValidator.detect_version(collection.info.schema)
print(version)  # SchemaVersion.V2_1_0

# Validate version
is_valid, error = SchemaValidator.validate_version(collection.info.schema)
if not is_valid:
    print(f"Unsupported version: {error}")

# Access collection schema version
print(collection.schema_version)
```

**Supported Versions:**

- v2.0.0 - Postman Collection Format v2.0.0
- v2.1.0 - Postman Collection Format v2.1.0

## Type Safety

The library provides enums and type hints for better IDE support and type checking.

```python
from python_postman.types.http_methods import HttpMethod, HttpMethodType
from python_postman.types.auth_types import AuthTypeEnum, AuthTypeType

# Use enums for type safety
method = HttpMethod.POST
auth_type = AuthTypeEnum.BEARER

# Type hints work with both enums and strings
def process_request(method: HttpMethodType):
    pass

process_request("GET")  # Valid
process_request(HttpMethod.POST)  # Valid
```

## Validation

Collections can be validated to ensure structural integrity.

```python
# Validate collection
result = collection.validate()

# Check validation result
if result.is_valid:
    print("Collection is valid")
else:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")

    print("Validation warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
```

**Validation Checks:**

- Schema version compatibility
- Required fields presence
- URL format validity
- Authentication configuration
- Variable references

## Serialization

Collections can be serialized back to JSON format.

```python
# Convert to dictionary
data = collection.to_dict()

# Convert to JSON string
json_str = collection.to_json(indent=2)

# Save to file
with open("output.json", "w") as f:
    f.write(json_str)
```

## Best Practices

1. **Always validate collections after parsing**

   ```python
   collection = parser.parse("collection.json")
   result = collection.validate()
   if not result.is_valid:
       handle_errors(result.errors)
   ```

2. **Use type hints for better IDE support**

   ```python
   from python_postman.models import Collection, Request

   def process_collection(collection: Collection) -> None:
       pass
   ```

3. **Handle missing optional fields gracefully**

   ```python
   if request.has_body():
       process_body(request.body)
   ```

4. **Use convenience methods for common checks**

   ```python
   if request.is_safe() and request.is_cacheable():
       cache_request(request)
   ```

5. **Leverage search for complex queries**
   ```python
   api_requests = collection.search() \
       .by_host("api.example.com") \
       .by_method("POST") \
       .execute()
   ```

## Next Steps

- [Execution Layer Documentation](execution-layer.md)
- [Layer Interaction Patterns](layer-interaction.md)
- [Complete Examples](../examples/)

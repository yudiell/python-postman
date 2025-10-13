# Layer Interaction Patterns

## Overview

This document explains how the model layer and execution layer interact, and provides patterns for common use cases. Understanding these interactions helps you choose the right approach for your needs.

## Layer Separation

The python-postman library maintains a clear separation between layers:

```
┌─────────────────────────────────────────┐
│         Application Code                │
└─────────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ Model Layer  │    │ Execution    │
│ (Core)       │◄───│ Layer        │
│              │    │ (Optional)   │
└──────────────┘    └──────────────┘
        │                   │
        ▼                   ▼
┌──────────────┐    ┌──────────────┐
│ JSON Files   │    │ HTTP APIs    │
└──────────────┘    └──────────────┘
```

### Model Layer (Core)

- **Purpose**: Parse, represent, and manipulate collections
- **Dependencies**: Python standard library only
- **Use Cases**: Analysis, validation, transformation, documentation

### Execution Layer (Optional)

- **Purpose**: Execute HTTP requests from collections
- **Dependencies**: httpx library
- **Use Cases**: API testing, automation, integration testing

## Interaction Patterns

### Pattern 1: Model-Only Usage

Use only the model layer for collection analysis and manipulation.

```python
from python_postman import PythonPostman

# Parse collection
parser = PythonPostman()
collection = parser.parse("collection.json")

# Analyze collection
print(f"Collection: {collection.info.name}")
print(f"Total requests: {len(collection.get_requests())}")

# Search for specific requests
post_requests = collection.search().by_method("POST").execute()
print(f"POST requests: {len(post_requests)}")

# Validate collection
result = collection.validate()
if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")

# Modify collection
new_request = Request(
    name="New Request",
    method="GET",
    url=Url.from_string("https://api.example.com/new")
)
collection.items.append(new_request)

# Save modified collection
with open("modified_collection.json", "w") as f:
    f.write(collection.to_json(indent=2))
```

**When to use:**

- Documentation generation
- Collection validation
- Collection transformation
- Static analysis
- Collection merging/splitting

### Pattern 2: Model + Execution

Use both layers for complete request execution.

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse collection (Model Layer)
parser = PythonPostman()
collection = parser.parse("collection.json")

# Validate before execution (Model Layer)
result = collection.validate()
if not result.is_valid:
    raise ValueError("Invalid collection")

# Setup execution (Execution Layer)
executor = RequestExecutor()
context = ExecutionContext()
context.set_variable("api_key", "secret123")

# Execute requests (Execution Layer)
for request in collection.get_requests():
    result = await executor.execute_request(request, context=context)
    print(f"{request.name}: {result.response.status_code}")
```

**When to use:**

- API testing
- Integration testing
- Automated workflows
- CI/CD pipelines
- Request chaining

### Pattern 3: Selective Execution

Use model layer to filter, then execute selected requests.

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse and filter (Model Layer)
parser = PythonPostman()
collection = parser.parse("collection.json")

# Find specific requests to execute
auth_requests = collection.search() \
    .by_folder("Authentication") \
    .by_method("POST") \
    .execute()

# Execute only filtered requests (Execution Layer)
executor = RequestExecutor()
context = ExecutionContext()

for search_result in auth_requests:
    result = await executor.execute_request(
        search_result.request,
        context=context
    )
    print(f"{search_result.full_path}: {result.response.status_code}")
```

**When to use:**

- Smoke testing (execute critical requests only)
- Targeted testing
- Conditional execution
- Performance testing specific endpoints

### Pattern 4: Introspection + Execution

Use introspection to understand collection structure before execution.

```python
from python_postman import PythonPostman
from python_postman.introspection import AuthResolver
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse collection
parser = PythonPostman()
collection = parser.parse("collection.json")

# Introspect authentication (Model Layer)
for request in collection.get_requests():
    resolved_auth = AuthResolver.resolve_auth(request, None, collection)
    print(f"{request.name}: Auth from {resolved_auth.source.value}")

    # Only execute requests with proper auth
    if resolved_auth.auth:
        executor = RequestExecutor()
        context = ExecutionContext()
        result = await executor.execute_request(request, context=context)
        print(f"  Status: {result.response.status_code}")
```

**When to use:**

- Debugging authentication issues
- Understanding collection structure
- Conditional execution based on configuration
- Pre-execution validation

### Pattern 5: Transform + Execute

Transform collection before execution.

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse collection
parser = PythonPostman()
collection = parser.parse("collection.json")

# Transform collection (Model Layer)
for request in collection.get_requests():
    # Add common header to all requests
    request.headers.append(Header(
        key="X-Custom-Header",
        value="custom-value"
    ))

    # Update base URL
    if request.url.host == "staging.example.com":
        request.url.host = "production.example.com"

# Execute transformed collection (Execution Layer)
executor = RequestExecutor()
context = ExecutionContext()
results = await executor.execute_collection(collection, context=context)
```

**When to use:**

- Environment switching
- Adding common headers/auth
- URL transformation
- Request modification

### Pattern 6: Execute + Analyze

Execute requests and analyze results using model layer.

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse and execute
parser = PythonPostman()
collection = parser.parse("collection.json")

executor = RequestExecutor()
context = ExecutionContext()
results = await executor.execute_collection(collection, context=context)

# Analyze results (Model Layer + Execution Layer)
success_count = sum(1 for r in results if r.success)
failure_count = sum(1 for r in results if not r.success)

print(f"Success: {success_count}/{len(results)}")
print(f"Failure: {failure_count}/{len(results)}")

# Group by status code
from collections import Counter
status_codes = Counter(r.response.status_code for r in results if r.success)
print(f"Status codes: {status_codes}")

# Find slow requests
slow_requests = [r for r in results if r.duration_ms > 1000]
print(f"Slow requests (>1s): {len(slow_requests)}")
```

**When to use:**

- Performance analysis
- Success rate monitoring
- Result aggregation
- Report generation

## Common Workflows

### Workflow 1: Parse → Inspect → Modify → Execute

Complete workflow using both layers.

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# 1. Parse (Model Layer)
parser = PythonPostman()
collection = parser.parse("collection.json")

# 2. Inspect (Model Layer)
print(f"Collection: {collection.info.name}")
print(f"Requests: {len(collection.get_requests())}")

# Validate
result = collection.validate()
if not result.is_valid:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")

# 3. Modify (Model Layer)
# Add API key to all requests
for request in collection.get_requests():
    if not request.has_auth():
        request.auth = Auth(
            type="apikey",
            parameters=[
                AuthParameter(key="key", value="X-API-Key"),
                AuthParameter(key="value", value="{{api_key}}")
            ]
        )

# 4. Execute (Execution Layer)
executor = RequestExecutor()
context = ExecutionContext()
context.set_variable("api_key", "your-api-key")

results = await executor.execute_collection(collection, context=context)

# 5. Report
for result in results:
    status = "✓" if result.success else "✗"
    print(f"{status} {result.request.name}: {result.response.status_code}")
```

### Workflow 2: Parse → Generate Documentation

Use model layer to generate API documentation.

````python
from python_postman import PythonPostman

# Parse collection
parser = PythonPostman()
collection = parser.parse("collection.json")

# Generate markdown documentation
def generate_docs(collection):
    docs = [f"# {collection.info.name}\n"]
    docs.append(f"{collection.info.description}\n")

    for request in collection.get_requests():
        docs.append(f"## {request.name}\n")
        docs.append(f"**Method:** `{request.method}`\n")
        docs.append(f"**URL:** `{request.url.to_string()}`\n")

        if request.description:
            docs.append(f"\n{request.description}\n")

        # Add example responses
        if request.responses:
            docs.append("\n### Example Responses\n")
            for response in request.responses:
                docs.append(f"#### {response.name}\n")
                docs.append(f"Status: `{response.code} {response.status}`\n")
                docs.append(f"```json\n{response.body}\n```\n")

        docs.append("\n---\n")

    return "\n".join(docs)

# Generate and save
documentation = generate_docs(collection)
with open("API_DOCS.md", "w") as f:
    f.write(documentation)
````

### Workflow 3: Parse → Validate → Deploy

Validate collection before deployment.

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse collection
parser = PythonPostman()
collection = parser.parse("collection.json")

# Validate structure
validation_result = collection.validate()
if not validation_result.is_valid:
    print("Collection validation failed:")
    for error in validation_result.errors:
        print(f"  - {error}")
    exit(1)

# Validate against live API (smoke test)
executor = RequestExecutor()
context = ExecutionContext()
context.set_variable("base_url", "https://staging.example.com")

# Execute critical requests
critical_requests = collection.search() \
    .by_folder("Critical") \
    .execute()

all_passed = True
for search_result in critical_requests:
    result = await executor.execute_request(
        search_result.request,
        context=context
    )

    if not result.success or result.response.status_code >= 400:
        print(f"✗ {search_result.request.name} failed")
        all_passed = False
    else:
        print(f"✓ {search_result.request.name} passed")

if all_passed:
    print("All critical tests passed. Ready for deployment.")
else:
    print("Some tests failed. Deployment blocked.")
    exit(1)
```

## Data Flow Between Layers

### From Model to Execution

```python
# Model layer creates request object
request = Request(
    name="Get User",
    method="GET",
    url=Url.from_string("{{base_url}}/users/{{user_id}}")
)

# Execution layer uses request object
executor = RequestExecutor()
context = ExecutionContext()
context.set_variable("base_url", "https://api.example.com")
context.set_variable("user_id", "123")

# Execution layer resolves variables and executes
result = await executor.execute_request(request, context=context)
```

### From Execution to Model

```python
# Execution layer produces results
result = await executor.execute_request(request, context=context)

# Model layer can store results as example responses
example_response = ExampleResponse(
    name="Success Response",
    code=result.response.status_code,
    status=result.response.reason,
    headers=[
        Header(key=k, value=v)
        for k, v in result.response.headers.items()
    ],
    body=result.response.text
)

# Add to request
request.add_response(example_response)

# Save updated collection
with open("updated_collection.json", "w") as f:
    f.write(collection.to_json(indent=2))
```

## Best Practices

### 1. Validate Before Execution

Always validate collections before executing requests.

```python
# Validate first
result = collection.validate()
if not result.is_valid:
    raise ValueError("Invalid collection")

# Then execute
executor = RequestExecutor()
results = await executor.execute_collection(collection)
```

### 2. Use Context for Variables

Always use ExecutionContext for variable management.

```python
# Good
context = ExecutionContext()
context.set_variable("api_key", api_key)
result = await executor.execute_request(request, context=context)

# Bad - variables won't be resolved
result = await executor.execute_request(request)
```

### 3. Separate Concerns

Keep model operations separate from execution operations.

```python
# Good - clear separation
collection = parser.parse("collection.json")
filtered_requests = collection.search().by_method("POST").execute()

executor = RequestExecutor()
for search_result in filtered_requests:
    result = await executor.execute_request(search_result.request)

# Bad - mixing concerns
collection = parser.parse("collection.json")
for item in collection.items:
    if isinstance(item, Request) and item.method == "POST":
        result = await executor.execute_request(item)
```

### 4. Handle Errors at Each Layer

Handle errors appropriately for each layer.

```python
# Model layer errors
try:
    collection = parser.parse("collection.json")
except FileNotFoundError:
    print("Collection file not found")
except ValueError as e:
    print(f"Invalid collection format: {e}")

# Execution layer errors
try:
    result = await executor.execute_request(request, context=context)
    if not result.success:
        print(f"Request failed: {result.error}")
except Exception as e:
    print(f"Execution error: {e}")
```

### 5. Use Introspection Before Execution

Use introspection to understand collection before executing.

```python
from python_postman.introspection import AuthResolver

# Understand auth configuration first
for request in collection.get_requests():
    resolved_auth = AuthResolver.resolve_auth(request, None, collection)
    if resolved_auth.source == AuthSource.NONE:
        print(f"Warning: {request.name} has no authentication")

# Then execute with confidence
results = await executor.execute_collection(collection, context=context)
```

## Performance Considerations

### Model Layer Performance

- **Lazy Loading**: Parse collections on-demand
- **Caching**: Cache search results and statistics
- **Efficient Traversal**: Use iterators for large collections

```python
# Good - iterator for large collections
for request in collection.get_requests():
    process_request(request)

# Bad - loads all into memory
all_requests = list(collection.get_requests())
for request in all_requests:
    process_request(request)
```

### Execution Layer Performance

- **Async Execution**: Use async for concurrent requests
- **Connection Pooling**: Reuse executor instance
- **Timeouts**: Set appropriate timeouts

```python
# Good - concurrent execution
results = await asyncio.gather(*[
    executor.execute_request(req, context)
    for req in requests
])

# Bad - sequential execution
results = []
for req in requests:
    result = await executor.execute_request(req, context)
    results.append(result)
```

## Next Steps

- [Complete Examples](../examples/)
- [Decision Tree Guide](../guides/decision-tree.md)
- [Troubleshooting Guide](../guides/troubleshooting.md)

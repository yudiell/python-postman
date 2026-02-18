# Execution Layer Documentation

## Overview

The execution layer provides runtime HTTP request execution capabilities for Postman collections. This layer is optional and requires the `httpx` library as a dependency. It enables you to execute requests defined in collections, handle authentication, resolve variables, and run pre-request and test scripts.

## Installation

To use the execution layer, install python-postman with the execution extras:

```bash
pip install python-postman[execution]
```

Or install httpx separately:

```bash
pip install python-postman httpx
```

## Core Concepts

### Execution Flow

1. **Request Selection** - Choose which request(s) to execute
2. **Variable Resolution** - Resolve variables in URL, headers, body
3. **Authentication Setup** - Apply authentication configuration
4. **Pre-request Scripts** - Execute pre-request scripts
5. **HTTP Execution** - Send HTTP request
6. **Response Capture** - Capture response data
7. **Test Scripts** - Execute test scripts
8. **Result Collection** - Collect execution results

## Key Classes

### RequestExecutor

Main class for executing requests.

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse collection
collection = PythonPostman.from_file("collection.json")

# Create executor
executor = RequestExecutor()

# Execute a single request
request = collection.items[0]
context = ExecutionContext()
result = await executor.execute_request(request, context)

# Check result
if result.success:
    print(f"Status: {result.response.status_code}")
    print(f"Body: {result.response.text}")
else:
    print(f"Error: {result.error}")
```

**Key Methods:**

- `execute_request(request, context)` - Execute single request (async)
- `execute_request_sync(request, context)` - Execute single request (sync)
- `execute_collection(collection, context=None)` - Execute all requests
- `execute_folder(folder, context=None)` - Execute folder requests
- `execute_requests(requests, context=None)` - Execute multiple requests

**Configuration Options:**

```python
executor = RequestExecutor(
    client_config={"timeout": 30.0, "verify": True, "follow_redirects": True},
    global_headers={"User-Agent": "python-postman/1.0"},
    variable_overrides={"base_url": "https://api.example.com"},
    script_timeout=30.0,    # Script execution timeout in seconds
    request_delay=0.0       # Delay between requests in seconds
)
```

### ExecutionContext

Manages execution state including variables, environment, and configuration.

```python
from python_postman.execution import ExecutionContext

# Create context
context = ExecutionContext()

# Set variables
context.set_variable("api_key", "secret123")
context.set_variable("base_url", "https://api.example.com")

# Set environment-scoped variables
context.set_variable("env", "production", "environment")

# Execute with context
result = await executor.execute_request(request, context=context)

# Access variables set during execution
token = context.get_variable("auth_token")
```

**Variable Scopes:**

- **Global Variables** - Available across all requests
- **Environment Variables** - Environment-specific values
- **Collection Variables** - Defined in collection
- **Request Variables** - Set during request execution

**Variable Precedence** (highest to lowest):

1. Request variables (highest precedence)
2. Folder variables
3. Collection variables
4. Environment variables (lowest precedence)

**Key Methods:**

- `set_variable(key, value, scope)` - Set variable in scope ("request", "folder", "collection", "environment")
- `get_variable(key)` - Get variable value (follows precedence)
- `has_variable(key)` - Check if variable exists in any scope
- `get_all_variables()` - Get all variables merged with precedence
- `clear_scope(scope)` - Clear all variables in a scope
- `create_child_context(request_variables)` - Create child context for request execution

### ExecutionResult

Contains the result of request execution.

```python
result = await executor.execute_request(request, context)

# Check success
if result.success:
    # Access response
    print(f"Status: {result.response.status_code}")
    print(f"Headers: {result.response.headers}")
    print(f"Body: {result.response.text}")
    print(f"JSON: {result.response.json}")

    # Access timing
    print(f"Duration: {result.execution_time_ms}ms")

    # Access test results
    if result.test_results:
        print(f"Tests passed: {result.test_results.passed}")
        print(f"Tests failed: {result.test_results.failed}")
else:
    # Handle error
    print(f"Error: {result.error}")
```

**Key Attributes:**

- `success` - Whether execution succeeded
- `response` - ExecutionResponse object
- `error` - Error (Optional[Exception], if failed)
- `execution_time_ms` - Execution duration in milliseconds
- `test_results` - ScriptResults object
- `request` - Original request object

### ExecutionResponse

Represents the HTTP response from execution.

```python
response = result.response

# Access status
print(response.status_code)

# Access headers
print(response.headers)
content_type = response.headers.get("content-type")

# Access body
print(response.text)        # Text content
print(response.content)     # Raw bytes
data = response.json       # Parse as JSON (property)

# Access timing
print(response.elapsed_ms)  # Response time in milliseconds
```

**Key Attributes:**

- `status_code` - HTTP status code
- `headers` - Response headers (dict)
- `text` - Response body as text
- `content` - Response body as bytes
- `elapsed_ms` - Response time in milliseconds
- `url` - Final URL (after redirects)

**Key Properties and Methods:**

- `json` - Response body parsed as JSON (property)
- `elapsed_seconds` - Response time in seconds
- `request_method` - HTTP method used
- `is_success()`, `is_redirect()`, `is_client_error()`, `is_server_error()` - Status checks
- `to_dict()` - Convert to dictionary

### AuthHandler

Handles authentication for requests.

```python
from python_postman.execution import AuthHandler

# Create auth handler
auth_handler = AuthHandler()

# Apply authentication to request
httpx_request = auth_handler.apply_auth(request, context)
```

**Supported Authentication Types:**

- **Basic Auth** - Username and password
- **Bearer Token** - Token-based authentication
- **API Key** - API key in header or query parameter
- **OAuth 1.0** - OAuth 1.0 signature
- **OAuth 2.0** - OAuth 2.0 token
- **No Auth** - No authentication

**Authentication Resolution:**
The auth handler automatically resolves authentication using inheritance:

1. Request-level auth (highest priority)
2. Folder-level auth
3. Collection-level auth (lowest priority)

### VariableResolver

Resolves variables in URLs, headers, and bodies.

```python
from python_postman.execution import VariableResolver

# Create resolver
resolver = VariableResolver(context)

# Resolve URL
url_string = "{{base_url}}/users/{{user_id}}"
resolved_url = resolver.resolve_string(url_string)
# Result: "https://api.example.com/users/123"

# Resolve headers
headers = {"Authorization": "Bearer {{token}}"}
resolved_headers = resolver.resolve_headers(headers)

# Resolve body
body = '{"name": "{{user_name}}"}'
resolved_body = resolver.resolve_string(body)
```

**Variable Syntax:**

- `{{variable_name}}` - Variable reference
- `:parameterName` - Path parameter (resolved from context variables)

> **Note**: Postman dynamic variables (`{{$guid}}`, `{{$timestamp}}`, `{{$randomInt}}`) are not currently supported. Use regular variables with values set in the execution context instead.

### ScriptRunner

Executes pre-request and test scripts.

```python
from python_postman.execution import ScriptRunner

# Create script runner
script_runner = ScriptRunner(timeout=30.0)

# Execute pre-request scripts (collection-level then request-level)
script_runner.execute_pre_request_scripts(request, collection, context)

# Execute test scripts and get results
results = script_runner.execute_test_scripts(request, response, context)
```

**Script Environment:**
Scripts have access to:

- `pm.variables` - Variable management
- `pm.environment` - Environment variables
- `pm.request` - Request object
- `pm.response` - Response object
- `pm.test()` - Define tests
- `pm.expect()` - Assertions

**Example Script:**

```javascript
// Pre-request script
pm.variables.set("timestamp", Date.now());

// Test script
pm.test("Status code is 200", function () {
  pm.response.to.have.status(200);
});

pm.test("Response has user data", function () {
  const data = pm.response.json();
  pm.expect(data).to.have.property("user");
});
```

### ScriptResults

Contains test execution results.

```python
test_results = result.test_results

# Check overall status
if test_results.failed == 0:
    print("All tests passed!")
else:
    print(f"Passed: {test_results.passed}")
    print(f"Failed: {test_results.failed}")
    print(f"Success rate: {test_results.success_rate:.0%}")

# Access individual assertion results
for assertion in test_results.assertions:
    print(f"{assertion.name}: {'PASS' if assertion.passed else 'FAIL'}")
    if not assertion.passed:
        print(f"  Error: {assertion.error}")
```

**Key Attributes:**

- `assertions` - List of ScriptAssertion objects (each has `.name`, `.passed`, `.error`)
- `passed` - Number of passed assertions
- `failed` - Number of failed assertions
- `total` - Property: total assertion count
- `success_rate` - Property: 0.0 to 1.0

## Usage Patterns

### Execute Single Request

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse collection
collection = PythonPostman.from_file("collection.json")

# Create executor and context
executor = RequestExecutor()
context = ExecutionContext()

# Set variables
context.set_variable("api_key", "your-api-key")

# Execute request
request = collection.items[0]
result = await executor.execute_request(request, context=context)

# Process result
if result.success:
    print(f"Success: {result.response.status_code}")
else:
    print(f"Failed: {result.error}")
```

### Execute Entire Collection

```python
# Execute all requests in collection
collection_result = await executor.execute_collection(collection, context=context)

# Process results
for result in collection_result.results:
    print(f"{result.request.name}: {result.response.status_code}")
```

### Execute with Custom Configuration

```python
# Create executor with custom settings
executor = RequestExecutor(
    client_config={"timeout": 60.0, "follow_redirects": False, "verify": False}
)

# Execute request
result = await executor.execute_request(request, context=context)
```

### Chain Requests with Variables

```python
# First request - login
login_request = collection.get_request_by_name("Login")
login_result = await executor.execute_request(login_request, context=context)

# Extract token from response
token = login_result.response.json["token"]
context.set_variable("auth_token", token)

# Second request - use token
user_request = collection.get_request_by_name("Get User")
user_result = await executor.execute_request(user_request, context=context)
```

### Handle Errors

```python
try:
    result = await executor.execute_request(request, context=context)

    if not result.success:
        print(f"Error: {result.error}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Synchronous Execution

For synchronous code, use the same RequestExecutor class:

```python
from python_postman.execution import RequestExecutor, ExecutionContext

# Synchronous execution uses the same RequestExecutor class
with RequestExecutor() as executor:
    context = ExecutionContext()
    result = executor.execute_request_sync(request, context)
    print(f"Status: {result.response.status_code}")
```

## Advanced Features

### Custom Authentication

Implement custom authentication by extending AuthHandler:

```python
from python_postman.execution import AuthHandler

class CustomAuthHandler(AuthHandler):
    def apply_custom_auth(self, request, context):
        # Custom authentication logic
        pass
```

### Custom Variable Functions

Add custom variable functions:

```python
from python_postman.execution import VariableResolver

class CustomVariableResolver(VariableResolver):
    def resolve_custom_function(self, function_name):
        if function_name == "$customValue":
            return "custom-value"
        return super().resolve_custom_function(function_name)
```

## Performance Considerations

1. **Connection Pooling** - httpx automatically pools connections
2. **Async Execution** - Use async for concurrent requests
3. **Timeout Configuration** - Set appropriate timeouts
4. **Resource Cleanup** - Close executor when done

```python
# Use context manager for automatic cleanup
async with RequestExecutor() as executor:
    context = ExecutionContext()
    result = await executor.execute_request(request, context)
```

## Error Handling

Common error types:

- `timeout` - Request timed out
- `connection` - Connection failed
- `ssl` - SSL verification failed
- `http` - HTTP error (4xx, 5xx)
- `script` - Script execution error
- `validation` - Request validation error

## Best Practices

1. **Always use ExecutionContext for variables**

   ```python
   context = ExecutionContext()
   context.set_variable("api_key", api_key)
   ```

2. **Handle errors gracefully**

   ```python
   if not result.success:
       log_error(result.error)
   ```

3. **Use async for better performance**

   ```python
   results = await asyncio.gather(*[
       executor.execute_request(req, context)
       for req in requests
   ])
   ```

4. **Set appropriate timeouts**

   ```python
   executor = RequestExecutor(client_config={"timeout": 30.0})
   ```

5. **Verify SSL in production**

   ```python
   executor = RequestExecutor(client_config={"verify": True})
   ```

## Next Steps

- [Layer Interaction Patterns](layer-interaction.md)
- [Complete Workflow Examples](../examples/)
- [Troubleshooting Guide](../guides/troubleshooting.md)

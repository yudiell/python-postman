# Python Postman Execution Examples

This directory contains comprehensive examples demonstrating the HTTP request execution capabilities of the python-postman library.

## Prerequisites

To run these examples, you need to install the library with execution support:

```bash
pip install python-postman[execution]
# or
pip install python-postman httpx
```

## Example Files

### 1. [basic_execution.py](basic_execution.py)

Demonstrates fundamental request execution concepts:

- Loading Postman collections
- Creating and configuring RequestExecutor
- Executing single requests
- Executing entire collections
- Basic error handling

**Key concepts covered:**

- `RequestExecutor` initialization
- `ExecutionContext` for variable management
- Async request execution
- Collection execution with results

### 2. [advanced_execution.py](advanced_execution.py)

Shows advanced execution features:

- Runtime variable substitutions
- Request extensions for modifying requests
- Parallel vs sequential collection execution
- Folder execution with variable inheritance
- Performance comparisons

**Key concepts covered:**

- `RequestExtensions` for runtime modifications
- Parallel execution patterns
- Variable scoping and inheritance
- Performance optimization

### 3. [synchronous_execution.py](synchronous_execution.py)

Demonstrates synchronous execution patterns:

- Synchronous request execution
- Context manager usage
- Request and collection convenience methods
- Simple error handling for sync workflows

**Key concepts covered:**

- `execute_request_sync()` method
- Context managers for resource cleanup
- Direct request execution methods
- Synchronous workflow patterns

### 4. [authentication_examples.py](authentication_examples.py)

Covers authentication handling:

- Bearer token authentication
- Basic authentication
- API key authentication
- Collection vs request-level auth
- Dynamic token refresh patterns

**Key concepts covered:**

- Authentication configuration
- Auth inheritance and precedence
- Dynamic credential management
- Security best practices

### 5. [variable_examples.py](variable_examples.py)

Focuses on variable management:

- Variable scoping and precedence
- Nested variable resolution
- Dynamic variable updates
- Error handling for missing variables
- Circular reference protection

**Key concepts covered:**

- Variable precedence rules
- `ExecutionContext` management
- Variable resolution patterns
- Error handling strategies

## Running the Examples

Each example is self-contained and can be run independently:

```bash
# Run basic execution example
python examples/basic_execution.py

# Run advanced features example
python examples/advanced_execution.py

# Run synchronous execution example
python examples/synchronous_execution.py

# Run authentication examples
python examples/authentication_examples.py

# Run variable management examples
python examples/variable_examples.py
```

## Sample Collections

The examples reference sample Postman collection files. You can create these collections in Postman and export them, or create them programmatically:

### Basic Collection Structure

```json
{
  "info": {
    "name": "Sample API Collection",
    "description": "Example collection for python-postman"
  },
  "variable": [
    { "key": "base_url", "value": "https://jsonplaceholder.typicode.com" },
    { "key": "api_version", "value": "v1" }
  ],
  "item": [
    {
      "name": "Get Users",
      "request": {
        "method": "GET",
        "url": "{{base_url}}/users",
        "header": [{ "key": "Accept", "value": "application/json" }]
      }
    }
  ]
}
```

### Authentication Collection Structure

```json
{
  "info": {
    "name": "Auth API Collection"
  },
  "auth": {
    "type": "bearer",
    "bearer": [{ "key": "token", "value": "{{bearer_token}}" }]
  },
  "variable": [{ "key": "api_base", "value": "https://api.example.com" }],
  "item": [
    {
      "name": "Get Protected Resource",
      "request": {
        "method": "GET",
        "url": "{{api_base}}/protected"
      }
    }
  ]
}
```

## Common Patterns

### 1. Basic Request Execution Pattern

```python
import asyncio
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

async def execute_request():
    collection = PythonPostman.from_file("collection.json")

    async with RequestExecutor() as executor:
        context = ExecutionContext(
            environment_variables={"base_url": "https://api.example.com"}
        )

        request = collection.get_request_by_name("API Call")
        result = await executor.execute_request(request, context)

        return result.success, result.response.status_code

success, status = asyncio.run(execute_request())
```

### 2. Collection Execution Pattern

```python
async def execute_collection():
    collection = PythonPostman.from_file("collection.json")

    async with RequestExecutor() as executor:
        result = await executor.execute_collection(
            collection,
            parallel=True,
            stop_on_error=False
        )

        return {
            "total": result.total_requests,
            "successful": result.successful_requests,
            "failed": result.failed_requests,
            "time_ms": result.total_time_ms
        }
```

### 3. Variable Management Pattern

```python
def setup_execution_context():
    return ExecutionContext(
        environment_variables={
            "env": "production",
            "base_url": "https://api.example.com"
        },
        collection_variables={
            "api_version": "v1",
            "timeout": "30"
        }
    )

# Use in request execution
context = setup_execution_context()
context.set_variable("session_token", "abc123", "environment")
```

### 4. Request Extension Pattern

```python
from python_postman.execution import RequestExtensions

def create_debug_extensions():
    return RequestExtensions(
        header_extensions={
            "X-Debug": "true",
            "X-Request-ID": "{{$timestamp}}"
        },
        param_extensions={
            "debug": "1",
            "trace": "true"
        }
    )

# Use in request execution
extensions = create_debug_extensions()
result = await executor.execute_request(request, context, extensions=extensions)
```

## Best Practices

1. **Resource Management**: Always use context managers or explicitly close executors
2. **Error Handling**: Check `result.success` and handle specific exception types
3. **Variable Scoping**: Use appropriate variable scopes for different use cases
4. **Parallel Execution**: Use parallel execution for independent requests
5. **Authentication**: Store sensitive credentials in environment variables
6. **Testing**: Use test scripts in collections for automated validation

## Troubleshooting

### Common Issues

1. **httpx not installed**: Install with `pip install httpx`
2. **SSL verification errors**: Set `verify=False` in client_config (not recommended for production)
3. **Variable resolution errors**: Check variable names and scoping
4. **Authentication failures**: Verify auth configuration and credentials
5. **Timeout errors**: Increase timeout values in client_config

### Debug Tips

1. Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. Check variable resolution:

```python
resolved = context.resolve_variables("{{your_variable}}")
print(f"Resolved: {resolved}")
```

3. Inspect request preparation:

```python
# Add debug prints in your execution flow
print(f"Request URL: {request.url}")
print(f"Request headers: {request.headers}")
```

## Contributing

If you have additional examples or improvements to existing ones, please feel free to contribute by submitting a pull request.

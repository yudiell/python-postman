# Variable Scoping and Introspection

This guide explains how variables work in Postman collections and how to use the python-postman library's variable introspection features to analyze and debug variable usage.

## Table of Contents

- [Variable Scopes](#variable-scopes)
- [Variable Precedence](#variable-precedence)
- [Variable Introspection](#variable-introspection)
- [Common Use Cases](#common-use-cases)
- [Best Practices](#best-practices)

## Variable Scopes

Postman collections support multiple variable scopes, each with different visibility and precedence:

### 1. Environment Scope

Environment variables are defined outside the collection and can be shared across multiple collections. They have the lowest precedence.

```python
from python_postman.execution import ExecutionContext

context = ExecutionContext(
    environment_variables={
        "base_url": "https://api.example.com",
        "api_version": "v1"
    }
)
```

### 2. Collection Scope

Collection-level variables are defined in the collection and available to all requests and folders within that collection.

```python
from python_postman.models import Collection, Variable

collection = Collection(
    info=...,
    variables=[
        Variable(key="api_key", value="secret_key_123"),
        Variable(key="timeout", value="30")
    ]
)
```

### 3. Folder Scope

Folder-level variables are defined in a folder and available to all requests within that folder and its subfolders.

```python
from python_postman.models import Folder, Variable

folder = Folder(
    name="User API",
    items=[...],
    variables=[
        Variable(key="endpoint", value="/users"),
        Variable(key="resource_type", value="user")
    ]
)
```

### 4. Request Scope

Request-level variables are specific to a single request execution and have the highest precedence. These are typically set dynamically during execution.

```python
context = ExecutionContext(
    request_variables={
        "user_id": "12345",
        "timestamp": "2024-01-15T10:30:00Z"
    }
)
```

## Variable Precedence

When multiple scopes define the same variable, the following precedence order applies (highest to lowest):

1. **Request** - Highest precedence
2. **Folder** - Overrides collection and environment
3. **Collection** - Overrides environment
4. **Environment** - Lowest precedence

### Example: Variable Shadowing

```python
from python_postman.models import Collection, Folder, Variable
from python_postman.execution import ExecutionContext

# Define the same variable at multiple levels
collection = Collection(
    info=...,
    variables=[Variable(key="timeout", value="60")],  # Collection: 60
    items=[
        Folder(
            name="API Tests",
            variables=[Variable(key="timeout", value="30")],  # Folder: 30
            items=[...]
        )
    ]
)

# Request-level override
context = ExecutionContext(
    collection_variables={"timeout": "60"},
    folder_variables={"timeout": "30"},
    request_variables={"timeout": "10"}  # Request: 10 (wins!)
)

# The effective value will be "10" (request scope)
print(context.get_variable("timeout"))  # Output: "10"
```

## Variable Introspection

The `VariableTracer` class provides powerful tools for analyzing variable usage in your collections.

### Basic Usage

```python
from python_postman import PythonPostman
from python_postman.introspection import VariableTracer

# Parse a collection
parser = PythonPostman("my_collection.json")
collection = parser.collection

# Create a tracer
tracer = VariableTracer(collection)
```

### Tracing Variable Definitions

Find all places where a variable is defined:

```python
# Trace all definitions of a variable
references = tracer.trace_variable("api_key")

for ref in references:
    print(f"Scope: {ref.scope.value}")
    print(f"Value: {ref.value}")
    print(f"Location: {ref.location}")
    print("---")
```

Output:

```
Scope: request
Value: override_key_789
Location: request context
---
Scope: folder
Value: folder_key_456
Location: folder 'Authentication > OAuth'
---
Scope: collection
Value: collection_key_123
Location: collection 'My API Tests'
---
```

### Finding Shadowed Variables

Detect variables defined in multiple scopes (which can lead to confusion):

```python
# Find all shadowed variables
shadowed = tracer.find_shadowed_variables()

for var_name, references in shadowed.items():
    print(f"Variable '{var_name}' is defined in {len(references)} scopes:")
    for ref in references:
        print(f"  - {ref.scope.value}: {ref.value} at {ref.location}")
```

Output:

```
Variable 'timeout' is defined in 3 scopes:
  - collection: 60 at collection 'My API Tests'
  - folder: 30 at folder 'Performance Tests'
  - folder: 10 at folder 'Performance Tests > Load Tests'
```

### Finding Undefined References

Detect variables that are referenced but never defined:

```python
# Find undefined variable references
undefined = tracer.find_undefined_references()

if undefined:
    print("⚠️  Undefined variables found:")
    for var in undefined:
        print(f"  - {var}")
else:
    print("✓ All variables are defined")
```

Output:

```
⚠️  Undefined variables found:
  - user_email
  - session_token
  - api_endpoint
```

### Finding Variable Usage

Find all locations where a variable is used:

```python
# Find all usage locations
usage = tracer.find_variable_usage("api_key")

print(f"Variable 'api_key' is used in {len(usage)} locations:")
for location in usage:
    print(f"  - {location}")
```

Output:

```
Variable 'api_key' is used in 5 locations:
  - Get User > URL
  - Get User > Header 'Authorization'
  - Create User > Header 'X-API-Key'
  - Update User > Auth parameter 'token'
  - Delete User > prerequest script
```

## Common Use Cases

### 1. Validating Collection Before Execution

```python
from python_postman import PythonPostman
from python_postman.introspection import VariableTracer

# Parse collection
parser = PythonPostman("api_tests.json")
collection = parser.collection

# Create tracer
tracer = VariableTracer(collection)

# Check for undefined variables
undefined = tracer.find_undefined_references()
if undefined:
    print("❌ Cannot execute collection - undefined variables:")
    for var in undefined:
        print(f"  - {var}")
    exit(1)

print("✓ All variables are defined - ready to execute")
```

### 2. Debugging Variable Resolution

```python
from python_postman.introspection import VariableTracer
from python_postman.execution import ExecutionContext

# Create tracer
tracer = VariableTracer(collection)

# Create execution context
context = ExecutionContext(
    environment_variables={"env": "prod"},
    collection_variables={"base_url": "https://{{env}}.api.example.com"},
    request_variables={"user_id": "12345"}
)

# Trace a specific variable
references = tracer.trace_variable("base_url", context)

print("Variable resolution chain:")
for ref in references:
    print(f"  {ref.scope.value}: {ref.value}")

# The actual resolved value
resolved = context.resolve_variables("{{base_url}}")
print(f"\nResolved value: {resolved}")
```

### 3. Detecting Configuration Issues

```python
from python_postman.introspection import VariableTracer

tracer = VariableTracer(collection)

# Find shadowed variables (potential configuration issues)
shadowed = tracer.find_shadowed_variables()

if shadowed:
    print("⚠️  Warning: Variables defined in multiple scopes")
    print("This may lead to unexpected behavior:")
    for var_name, refs in shadowed.items():
        print(f"\n  Variable: {var_name}")
        for ref in refs:
            print(f"    - {ref.scope.value}: {ref.value}")
```

### 4. Generating Variable Documentation

```python
from python_postman.introspection import VariableTracer

tracer = VariableTracer(collection)

# Get all defined variables
all_vars = {}
for var in collection.variables:
    all_vars[var.key] = {
        "value": var.value,
        "description": var.description,
        "usage": tracer.find_variable_usage(var.key)
    }

# Generate documentation
print("# Collection Variables\n")
for var_name, info in all_vars.items():
    print(f"## {var_name}")
    print(f"- **Value**: `{info['value']}`")
    if info['description']:
        print(f"- **Description**: {info['description']}")
    print(f"- **Used in {len(info['usage'])} locations**:")
    for location in info['usage']:
        print(f"  - {location}")
    print()
```

### 5. Migration and Refactoring

```python
from python_postman.introspection import VariableTracer

tracer = VariableTracer(collection)

# Find all usages of a variable you want to rename
old_var = "api_key"
new_var = "auth_token"

usage = tracer.find_variable_usage(old_var)

print(f"To rename '{old_var}' to '{new_var}', update:")
for location in usage:
    print(f"  - {location}")

print(f"\nTotal locations to update: {len(usage)}")
```

## Best Practices

### 1. Minimize Variable Shadowing

Avoid defining the same variable at multiple levels unless intentional:

```python
# ❌ Bad: Confusing shadowing
collection.variables = [Variable(key="timeout", value="60")]
folder.variables = [Variable(key="timeout", value="30")]  # Shadows collection

# ✓ Good: Use distinct names
collection.variables = [Variable(key="default_timeout", value="60")]
folder.variables = [Variable(key="api_timeout", value="30")]
```

### 2. Use Descriptive Variable Names

```python
# ❌ Bad: Unclear names
Variable(key="url", value="https://api.example.com")
Variable(key="key", value="abc123")

# ✓ Good: Clear, descriptive names
Variable(key="base_url", value="https://api.example.com")
Variable(key="api_key", value="abc123")
```

### 3. Document Your Variables

```python
# ✓ Good: Include descriptions
Variable(
    key="api_key",
    value="your_key_here",
    description="API authentication key - obtain from developer portal"
)
```

### 4. Validate Before Execution

```python
# Always check for undefined variables before running tests
tracer = VariableTracer(collection)
undefined = tracer.find_undefined_references()

if undefined:
    raise ValueError(f"Undefined variables: {', '.join(undefined)}")
```

### 5. Use Environment Variables for Secrets

```python
# ✓ Good: Sensitive data in environment (not committed to repo)
context = ExecutionContext(
    environment_variables={
        "api_key": os.getenv("API_KEY"),
        "db_password": os.getenv("DB_PASSWORD")
    }
)

# ❌ Bad: Secrets in collection (committed to repo)
collection.variables = [
    Variable(key="api_key", value="secret_key_123")  # Don't do this!
]
```

## Advanced Topics

### Variable Resolution with Context

When executing requests, variables are resolved using the execution context:

```python
from python_postman.execution import ExecutionContext

# Create context with multiple scopes
context = ExecutionContext(
    environment_variables={"env": "staging"},
    collection_variables={"base_url": "https://{{env}}.api.example.com"},
    folder_variables={"endpoint": "/users"},
    request_variables={"user_id": "12345"}
)

# Variables are resolved recursively
url = context.resolve_variables("{{base_url}}{{endpoint}}/{{user_id}}")
print(url)  # Output: https://staging.api.example.com/users/12345
```

### Tracing with Runtime Context

Combine static analysis with runtime context:

```python
# Static analysis (from collection definition)
tracer = VariableTracer(collection)
static_refs = tracer.trace_variable("api_key")

# Runtime analysis (with execution context)
context = ExecutionContext(request_variables={"api_key": "runtime_override"})
runtime_refs = tracer.trace_variable("api_key", context)

print(f"Static definitions: {len(static_refs)}")
print(f"Runtime definitions: {len(runtime_refs)}")
```

## See Also

- [Execution Context Documentation](../architecture/execution-layer.md)
- [Variable Model API Reference](../../python_postman/models/variable.py)
- [Variable Tracer API Reference](../../python_postman/introspection/variable_tracer.py)

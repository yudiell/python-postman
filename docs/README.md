# python-postman Documentation

Welcome to the python-postman documentation! This guide will help you understand and use the library effectively.

## Documentation Structure

### Architecture Documentation

Learn about the library's internal structure and design:

- **[Overview](architecture/overview.md)** - High-level architecture and design principles
- **[Model Layer](architecture/model-layer.md)** - Parsing and representing collections
- **[Execution Layer](architecture/execution-layer.md)** - Runtime request execution
- **[Layer Interaction](architecture/layer-interaction.md)** - How layers work together

### Guides

Practical guides for common tasks:

- **[Decision Tree](guides/decision-tree.md)** - Choose the right features for your use case
- **[Optional Dependencies](guides/optional-dependencies.md)** - Understanding dependency groups
- **[Variable Scoping](guides/variable-scoping.md)** - Understanding variable scopes and resolution
- **[Description Fields](guides/description-fields.md)** - Using description fields effectively
- **[Troubleshooting](guides/troubleshooting.md)** - Diagnose and fix common issues

### Examples

Complete working examples:

- **[Parse → Inspect → Modify → Execute](examples/parse-inspect-modify-execute.py)** - Complete workflow example
- **[Generate Documentation](examples/generate-documentation.py)** - Generate API docs from collections
- **[Variable Introspection](examples/variable-introspection.py)** - Trace and analyze variable usage
- **[Description Usage](examples/description-usage.py)** - Working with description fields

## Quick Start

### Installation

For core functionality (parsing, validation, transformation):

```bash
pip install python-postman
```

For API testing (includes HTTP execution):

```bash
pip install python-postman[execution]
```

### Basic Usage

#### Parse and Analyze Collection

```python
from python_postman import PythonPostman

# Parse collection
parser = PythonPostman()
collection = parser.parse("collection.json")

# Analyze
print(f"Collection: {collection.info.name}")
print(f"Requests: {len(list(collection.get_requests()))}")

# Validate
result = collection.validate()
if result.is_valid:
    print("✓ Collection is valid")
```

#### Execute Requests

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse collection
parser = PythonPostman()
collection = parser.parse("collection.json")

# Setup execution
executor = RequestExecutor()
context = ExecutionContext()
context.set_variable("api_key", "your-key")

# Execute
results = await executor.execute_collection(collection, context=context)

# Check results
for result in results:
    print(f"{result.request.name}: {result.response.status_code}")
```

## Common Use Cases

### 1. API Documentation Generation

**Goal:** Generate markdown/HTML documentation from Postman collections

**Approach:** Use Model Layer only

**Guide:** [Generate Documentation Example](examples/generate-documentation.py)

**Key Features:**

- Collection parsing
- Request introspection
- Example responses
- Custom formatting

---

### 2. API Testing

**Goal:** Automated API testing in CI/CD

**Approach:** Use Model + Execution Layer

**Guide:** [Parse → Inspect → Modify → Execute](examples/parse-inspect-modify-execute.py)

**Key Features:**

- Request execution
- Test scripts
- Variable management
- Result validation

---

### 3. Collection Validation

**Goal:** Validate collection structure before deployment

**Approach:** Use Model Layer + optional execution

**Key Features:**

- Schema validation
- Structure validation
- Optional smoke testing

**Example:**

```python
collection = parser.parse("collection.json")

# Validate structure
result = collection.validate()
if not result.is_valid:
    for error in result.errors:
        print(f"Error: {error}")
    exit(1)

# Optional: Execute critical requests
critical = collection.search().by_folder("Critical").execute()
for search_result in critical:
    result = await executor.execute_request(search_result.request, context)
    if not result.success:
        exit(1)
```

---

### 4. Environment Switching

**Goal:** Transform collections for different environments

**Approach:** Use Model Layer only

**Key Features:**

- URL transformation
- Variable updates
- Serialization

**Example:**

```python
collection = parser.parse("staging_collection.json")

# Update URLs
for request in collection.get_requests():
    request.url.host = request.url.host.replace("staging", "production")

# Save
with open("production_collection.json", "w") as f:
    f.write(collection.to_json(indent=2))
```

---

### 5. Collection Analysis

**Goal:** Analyze collection structure and complexity

**Approach:** Use Model Layer + Introspection

**Key Features:**

- Search and filtering
- Authentication resolution
- Statistics collection

**Example:**

```python
from python_postman.introspection import AuthResolver

collection = parser.parse("collection.json")

# Analyze authentication
for request in collection.get_requests():
    resolved_auth = AuthResolver.resolve_auth(request, None, collection)
    print(f"{request.name}: {resolved_auth.source.value}")

# Find requests without auth
no_auth = [r for r in collection.get_requests() if not r.has_auth()]
print(f"Requests without auth: {len(no_auth)}")
```

---

## Feature Matrix

| Feature               | Model Layer | Execution Layer |
| --------------------- | ----------- | --------------- |
| Parse collections     | ✓           | ✓               |
| Validate structure    | ✓           | ✓               |
| Search/filter         | ✓           | ✓               |
| Transform collections | ✓           | ✓               |
| Generate docs         | ✓           | ✓               |
| Execute HTTP requests | ✗           | ✓               |
| Run scripts           | ✗           | ✓               |
| Variable resolution   | ✗           | ✓               |
| Authentication        | ✗           | ✓               |
| Test execution        | ✗           | ✓               |

## Decision Flow

```
Need to execute HTTP requests?
│
├─ NO → Install: pip install python-postman
│   └─ Use: Model Layer
│       ├─ Documentation generation
│       ├─ Collection validation
│       ├─ Collection transformation
│       └─ Static analysis
│
└─ YES → Install: pip install python-postman[execution]
    └─ Use: Model + Execution Layer
        ├─ API testing
        ├─ Integration testing
        ├─ Automated workflows
        └─ CI/CD pipelines
```

See [Decision Tree Guide](guides/decision-tree.md) for detailed decision flow.

## Key Concepts

### Collections

A Postman collection is a hierarchical structure:

```
Collection
├── Info (metadata)
├── Auth (optional)
├── Variables
└── Items
    ├── Requests
    └── Folders (containing more items)
```

### Layers

**Model Layer (Core):**

- No external dependencies
- Parse and represent collections
- Validate and transform
- Search and filter

**Execution Layer (Optional):**

- Requires httpx
- Execute HTTP requests
- Run scripts
- Manage variables

### Variables

Variables can be defined at multiple levels:

1. Collection variables
2. Environment variables
3. Global variables
4. Request variables (set in scripts)

**Precedence:** Request > Environment > Collection > Global

### Authentication

Authentication can be defined at:

1. Request level (highest priority)
2. Folder level
3. Collection level (lowest priority)

Use `AuthResolver` to determine effective authentication.

## API Reference

### Core Classes

- **PythonPostman** - Entry point for parsing
- **Collection** - Represents a collection
- **Request** - Represents an HTTP request
- **Folder** - Represents a folder
- **Url** - Represents a URL
- **Auth** - Represents authentication
- **Body** - Represents request body
- **Response** - Represents example response

### Execution Classes

- **RequestExecutor** - Executes requests
- **ExecutionContext** - Manages execution state
- **ExecutionResult** - Contains execution results
- **ExecutionResponse** - HTTP response

### Introspection Classes

- **AuthResolver** - Resolves authentication
- **VariableTracer** - Traces variables
- **RequestQuery** - Search builder

## Best Practices

1. **Always validate collections:**

   ```python
   result = collection.validate()
   if not result.is_valid:
       handle_errors(result.errors)
   ```

2. **Use ExecutionContext for variables:**

   ```python
   context = ExecutionContext()
   context.set_variable("api_key", api_key)
   ```

3. **Reuse executor instances:**

   ```python
   executor = RequestExecutor()
   for request in requests:
       result = await executor.execute_request(request, context)
   ```

4. **Handle errors appropriately:**

   ```python
   if not result.success:
       print(f"Error: {result.error}")
   ```

5. **Use search for filtering:**
   ```python
   requests = collection.search().by_method("POST").execute()
   ```

## Performance Tips

1. **Use iterators for large collections:**

   ```python
   for request in collection.get_requests():
       process(request)
   ```

2. **Execute requests concurrently:**

   ```python
   results = await asyncio.gather(*[
       executor.execute_request(req, context)
       for req in requests
   ])
   ```

3. **Cache search results:**
   ```python
   post_requests = collection.search().by_method("POST").execute()
   # Reuse post_requests
   ```

## Troubleshooting

Common issues and solutions:

- **Import errors** → Check installation and dependencies
- **Parsing errors** → Validate JSON format
- **Execution timeouts** → Increase timeout setting
- **SSL errors** → Check certificates or disable verification (dev only)
- **Variable not resolving** → Check ExecutionContext

See [Troubleshooting Guide](guides/troubleshooting.md) for detailed solutions.

## Contributing

Contributions are welcome! To contribute:

1. Install development dependencies:

   ```bash
   pip install python-postman[dev]
   ```

2. Run tests:

   ```bash
   pytest
   ```

3. Check types:

   ```bash
   mypy python_postman
   ```

4. Format code:
   ```bash
   black python_postman
   ```

## Support

- **Documentation:** You're reading it!
- **Examples:** See [examples/](examples/) directory
- **Issues:** Report bugs on GitHub
- **Discussions:** Ask questions in GitHub Discussions

## License

python-postman is released under the MIT License.

## Next Steps

- **New users:** Start with [Decision Tree](guides/decision-tree.md)
- **API testing:** Read [Execution Layer](architecture/execution-layer.md)
- **Documentation generation:** See [Generate Documentation Example](examples/generate-documentation.py)
- **Having issues:** Check [Troubleshooting Guide](guides/troubleshooting.md)

# Decision Tree: Choosing the Right Features

## Overview

This guide helps you decide which features and layers of python-postman to use based on your specific needs. Follow the decision tree to find the right approach for your use case.

## Quick Decision Tree

```
Do you need to execute HTTP requests?
│
├─ NO → Use Model Layer Only
│   │
│   ├─ Need to analyze collection structure? → Use Introspection
│   ├─ Need to search/filter requests? → Use Search API
│   ├─ Need to validate collections? → Use Validation
│   ├─ Need to generate documentation? → Use Model Layer + Custom Logic
│   └─ Need to transform collections? → Use Model Layer + Serialization
│
└─ YES → Use Model Layer + Execution Layer
    │
    ├─ Need to execute all requests? → Use execute_collection()
    ├─ Need to execute specific requests? → Use Search + execute_request()
    ├─ Need to chain requests? → Use ExecutionContext + Variables
    ├─ Need to run tests? → Use Test Scripts + TestResults
    └─ Need custom execution logic? → Extend RequestExecutor
```

## Detailed Decision Guide

### Question 1: What is your primary goal?

#### A. Analyze or Document Collections

**Use Case:** Generate API documentation, analyze collection structure, create reports

**Recommended Approach:** Model Layer Only

**Features to Use:**

- Collection parsing
- Request/Folder traversal
- Search and filtering
- Introspection (auth resolution, variable tracing)

**Example:**

```python
from python_postman import PythonPostman

parser = PythonPostman()
collection = parser.parse("collection.json")

# Analyze structure
print(f"Total requests: {len(collection.get_requests())}")
print(f"Total folders: {len(collection.get_folders())}")

# Generate documentation
for request in collection.get_requests():
    print(f"## {request.name}")
    print(f"Method: {request.method}")
    print(f"URL: {request.url.to_string()}")
```

**Installation:**

```bash
pip install python-postman
```

---

#### B. Test APIs

**Use Case:** Run automated API tests, validate API responses, integration testing

**Recommended Approach:** Model Layer + Execution Layer

**Features to Use:**

- Collection parsing
- Request execution
- Test scripts
- Variable management
- Authentication handling

**Example:**

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

parser = PythonPostman()
collection = parser.parse("collection.json")

executor = RequestExecutor()
context = ExecutionContext()
context.set_variable("api_key", "your-key")

results = await executor.execute_collection(collection, context=context)

# Check test results
for result in results:
    if result.test_results:
        print(f"{result.request.name}: {result.test_results.passed} passed")
```

**Installation:**

```bash
pip install python-postman[execution]
```

---

#### C. Transform or Modify Collections

**Use Case:** Update URLs, add headers, merge collections, environment switching

**Recommended Approach:** Model Layer + Serialization

**Features to Use:**

- Collection parsing
- Request/Folder modification
- Serialization (to_dict, to_json)

**Example:**

```python
from python_postman import PythonPostman

parser = PythonPostman()
collection = parser.parse("collection.json")

# Modify all requests
for request in collection.get_requests():
    request.url.host = "production.example.com"
    request.headers.append(Header(key="X-Environment", value="prod"))

# Save modified collection
with open("modified_collection.json", "w") as f:
    f.write(collection.to_json(indent=2))
```

**Installation:**

```bash
pip install python-postman
```

---

#### D. Validate Collections

**Use Case:** CI/CD validation, pre-deployment checks, collection quality assurance

**Recommended Approach:** Model Layer + Optional Execution

**Features to Use:**

- Collection parsing
- Validation
- Schema version checking
- Optional: Smoke testing with execution

**Example:**

```python
from python_postman import PythonPostman

parser = PythonPostman()
collection = parser.parse("collection.json")

# Validate structure
result = collection.validate()
if not result.is_valid:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
    exit(1)

print("Collection is valid!")
```

**Installation:**

```bash
pip install python-postman
```

---

### Question 2: Do you need to execute requests?

#### NO → Model Layer Only

**When to choose:**

- Static analysis
- Documentation generation
- Collection transformation
- Validation only
- No network calls needed

**Advantages:**

- No external dependencies
- Faster installation
- Lighter weight
- No network requirements

**Limitations:**

- Cannot execute HTTP requests
- Cannot run scripts
- Cannot test actual API responses

---

#### YES → Model Layer + Execution Layer

**When to choose:**

- API testing
- Integration testing
- Automated workflows
- Request chaining
- Script execution needed

**Advantages:**

- Full functionality
- Execute real HTTP requests
- Run pre-request and test scripts
- Variable resolution
- Authentication handling

**Limitations:**

- Requires httpx dependency
- Requires network access
- Slower than model-only operations

---

### Question 3: How many requests do you need to execute?

#### A. All Requests in Collection

**Use:** `execute_collection()`

```python
executor = RequestExecutor()
context = ExecutionContext()
results = await executor.execute_collection(collection, context=context)
```

**Best for:**

- Full test suite execution
- Complete API validation
- Comprehensive testing

---

#### B. All Requests in Folder

**Use:** `execute_folder()`

```python
folder = collection.items[0]  # Get specific folder
results = await executor.execute_folder(folder, context=context)
```

**Best for:**

- Testing specific feature areas
- Modular test execution
- Folder-based organization

---

#### C. Specific Requests Only

**Use:** Search + `execute_request()`

```python
# Find specific requests
post_requests = collection.search().by_method("POST").execute()

# Execute only those
for search_result in post_requests:
    result = await executor.execute_request(
        search_result.request,
        context=context
    )
```

**Best for:**

- Smoke testing
- Targeted testing
- Conditional execution
- Performance testing specific endpoints

---

#### D. Single Request

**Use:** `execute_request()`

```python
request = collection.items[0]
result = await executor.execute_request(request, context=context)
```

**Best for:**

- Debugging
- Manual testing
- Request chaining
- Custom workflows

---

### Question 4: Do you need to chain requests?

#### YES → Use ExecutionContext + Variables

**Pattern:**

```python
context = ExecutionContext()

# First request - login
login_result = await executor.execute_request(login_request, context=context)
token = login_result.response.json()["token"]

# Store token for next request
context.set_variable("auth_token", token)

# Second request - use token
user_result = await executor.execute_request(user_request, context=context)
```

**Best for:**

- Authentication flows
- Multi-step workflows
- Dependent requests
- Session management

---

#### NO → Execute Independently

**Pattern:**

```python
results = await executor.execute_collection(collection, context=context)
```

**Best for:**

- Independent tests
- Parallel execution
- Simple validation

---

### Question 5: Do you need custom execution logic?

#### YES → Extend RequestExecutor

**Pattern:**

```python
from python_postman.execution import RequestExecutor

class CustomExecutor(RequestExecutor):
    async def execute_request(self, request, context=None):
        # Custom pre-processing
        print(f"Executing: {request.name}")

        # Call parent implementation
        result = await super().execute_request(request, context)

        # Custom post-processing
        if result.success:
            self.log_success(result)

        return result
```

**Best for:**

- Custom logging
- Custom metrics
- Special error handling
- Integration with other tools

---

#### NO → Use Standard RequestExecutor

**Pattern:**

```python
executor = RequestExecutor(
    timeout=30.0,
    follow_redirects=True,
    verify_ssl=True
)
```

**Best for:**

- Standard use cases
- Simple execution
- Quick setup

---

## Feature Comparison Matrix

| Feature                 | Model Layer Only | Model + Execution |
| ----------------------- | ---------------- | ----------------- |
| Parse collections       | ✓                | ✓                 |
| Validate structure      | ✓                | ✓                 |
| Search/filter requests  | ✓                | ✓                 |
| Modify collections      | ✓                | ✓                 |
| Generate documentation  | ✓                | ✓                 |
| Execute HTTP requests   | ✗                | ✓                 |
| Run scripts             | ✗                | ✓                 |
| Variable resolution     | ✗                | ✓                 |
| Authentication handling | ✗                | ✓                 |
| Test execution          | ✗                | ✓                 |
| External dependencies   | None             | httpx             |

## Installation Guide

### Model Layer Only

```bash
pip install python-postman
```

### Model + Execution Layer

```bash
pip install python-postman[execution]
```

### Development Installation

```bash
pip install python-postman[dev]
```

## Common Use Case Recommendations

### Use Case: CI/CD Pipeline Testing

**Recommendation:** Model + Execution Layer

**Approach:**

1. Parse collection
2. Validate structure
3. Execute critical requests
4. Check test results
5. Report status

```python
collection = parser.parse("collection.json")

# Validate
if not collection.validate().is_valid:
    exit(1)

# Execute
results = await executor.execute_collection(collection, context)

# Report
failed = sum(1 for r in results if not r.success)
if failed > 0:
    print(f"{failed} tests failed")
    exit(1)
```

---

### Use Case: API Documentation Generation

**Recommendation:** Model Layer Only

**Approach:**

1. Parse collection
2. Extract request information
3. Generate markdown/HTML
4. Include example responses

```python
collection = parser.parse("collection.json")

for request in collection.get_requests():
    generate_doc_section(request)
```

---

### Use Case: Collection Maintenance

**Recommendation:** Model Layer Only

**Approach:**

1. Parse collection
2. Analyze structure
3. Find issues (missing auth, broken URLs)
4. Modify and save

```python
collection = parser.parse("collection.json")

# Find requests without auth
for request in collection.get_requests():
    if not request.has_auth():
        print(f"Warning: {request.name} has no auth")
```

---

### Use Case: Performance Testing

**Recommendation:** Model + Execution Layer

**Approach:**

1. Parse collection
2. Filter performance-critical requests
3. Execute with timing
4. Analyze response times

```python
critical_requests = collection.search() \
    .by_folder("Critical") \
    .execute()

for search_result in critical_requests:
    result = await executor.execute_request(search_result.request, context)
    if result.duration_ms > 1000:
        print(f"Slow: {search_result.request.name} - {result.duration_ms}ms")
```

---

### Use Case: Environment Switching

**Recommendation:** Model Layer Only

**Approach:**

1. Parse collection
2. Update URLs/variables
3. Save new collection

```python
collection = parser.parse("staging_collection.json")

for request in collection.get_requests():
    request.url.host = request.url.host.replace("staging", "production")

with open("production_collection.json", "w") as f:
    f.write(collection.to_json(indent=2))
```

## Next Steps

Based on your decision:

- **Model Layer Only** → Read [Model Layer Documentation](../architecture/model-layer.md)
- **Model + Execution** → Read [Execution Layer Documentation](../architecture/execution-layer.md)
- **Need Examples** → See [Complete Examples](../examples/)
- **Having Issues** → Check [Troubleshooting Guide](troubleshooting.md)

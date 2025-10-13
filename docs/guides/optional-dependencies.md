# Optional Dependencies Guide

## Overview

python-postman is designed with a modular architecture that allows you to install only the dependencies you need. This guide explains the different dependency groups and when to use them.

## Dependency Groups

### Core (No Optional Dependencies)

The core library has no external dependencies beyond Python's standard library.

**Installation:**

```bash
pip install python-postman
```

**What's Included:**

- Collection parsing
- Model classes (Request, Folder, Collection, etc.)
- Validation
- Search and filtering
- Introspection tools
- Serialization (to_dict, to_json)

**What's NOT Included:**

- HTTP request execution
- Script execution
- Runtime variable resolution

**Use Cases:**

- Static analysis
- Documentation generation
- Collection transformation
- Validation only
- CI/CD validation

**Example:**

```python
from python_postman import PythonPostman

# Parse and analyze collection
parser = PythonPostman()
collection = parser.parse("collection.json")

# Validate
result = collection.validate()

# Search
requests = collection.search().by_method("POST").execute()

# Transform
for request in collection.get_requests():
    request.url.host = "production.example.com"

# Save
with open("output.json", "w") as f:
    f.write(collection.to_json(indent=2))
```

---

### Execution Dependencies

Adds HTTP request execution capabilities.

**Installation:**

```bash
pip install python-postman[execution]
```

**Additional Dependencies:**

- `httpx` - Modern HTTP client for Python
- `httpx[http2]` - HTTP/2 support (optional)

**What's Added:**

- RequestExecutor
- ExecutionContext
- AuthHandler
- VariableResolver
- ScriptRunner
- Response handling

**Use Cases:**

- API testing
- Integration testing
- Automated workflows
- Request chaining
- CI/CD testing

**Example:**

```python
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext

# Parse collection
parser = PythonPostman()
collection = parser.parse("collection.json")

# Execute requests
executor = RequestExecutor()
context = ExecutionContext()
context.set_variable("api_key", "your-key")

results = await executor.execute_collection(collection, context=context)
```

---

### Development Dependencies

Adds tools for development and testing.

**Installation:**

```bash
pip install python-postman[dev]
```

**Additional Dependencies:**

- `pytest` - Testing framework
- `pytest-asyncio` - Async test support
- `pytest-cov` - Coverage reporting
- `mypy` - Type checking
- `black` - Code formatting
- `flake8` - Linting
- `isort` - Import sorting

**Use Cases:**

- Contributing to python-postman
- Running tests
- Type checking
- Code quality checks

**Example:**

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=python_postman

# Type check
mypy python_postman

# Format code
black python_postman

# Lint
flake8 python_postman
```

---

### All Dependencies

Install everything.

**Installation:**

```bash
pip install python-postman[all]
```

Equivalent to:

```bash
pip install python-postman[execution,dev]
```

---

## Dependency Details

### httpx

**Purpose:** HTTP client for request execution

**Version:** >= 0.24.0

**Features:**

- Async/sync support
- HTTP/2 support
- Connection pooling
- Timeout handling
- SSL/TLS support
- Redirect handling

**Why httpx?**

- Modern, well-maintained
- Excellent async support
- Similar API to requests
- Better performance
- HTTP/2 support

**Alternatives:**
If you prefer a different HTTP client, you can extend RequestExecutor:

```python
from python_postman.execution import RequestExecutor
import requests  # or aiohttp, etc.

class CustomExecutor(RequestExecutor):
    async def execute_request(self, request, context=None):
        # Use your preferred HTTP client
        response = requests.request(
            method=request.method,
            url=request.url.to_string(),
            headers={h.key: h.value for h in request.headers}
        )
        # Convert to ExecutionResult
        return self._create_result(response)
```

---

## Installation Scenarios

### Scenario 1: Documentation Generation Only

**Need:** Parse collections and generate docs

**Install:**

```bash
pip install python-postman
```

**Why:** No execution needed, core is sufficient

---

### Scenario 2: API Testing

**Need:** Execute requests and run tests

**Install:**

```bash
pip install python-postman[execution]
```

**Why:** Need HTTP execution capabilities

---

### Scenario 3: CI/CD Pipeline

**Need:** Validate and test collections

**Install:**

```bash
pip install python-postman[execution]
```

**Why:** Need both validation and execution

---

### Scenario 4: Contributing to Library

**Need:** Development and testing

**Install:**

```bash
pip install python-postman[dev]
# or
pip install python-postman[all]
```

**Why:** Need all development tools

---

### Scenario 5: Collection Analysis Tool

**Need:** Analyze collection structure

**Install:**

```bash
pip install python-postman
```

**Why:** Core functionality is sufficient

---

## Checking Installed Dependencies

### Check if execution is available

```python
try:
    from python_postman.execution import RequestExecutor
    print("Execution layer available")
except ImportError:
    print("Execution layer not available")
    print("Install with: pip install python-postman[execution]")
```

### Check httpx version

```python
try:
    import httpx
    print(f"httpx version: {httpx.__version__}")
except ImportError:
    print("httpx not installed")
```

### List all installed packages

```bash
pip list | grep -E "(python-postman|httpx)"
```

---

## Upgrading Dependencies

### Upgrade python-postman

```bash
pip install --upgrade python-postman
```

### Upgrade with execution dependencies

```bash
pip install --upgrade python-postman[execution]
```

### Upgrade specific dependency

```bash
pip install --upgrade httpx
```

---

## Dependency Conflicts

### Issue: httpx version conflict

**Symptom:**

```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**Solution:**

1. Check installed versions:

   ```bash
   pip list | grep httpx
   ```

2. Upgrade httpx:

   ```bash
   pip install --upgrade httpx
   ```

3. If conflict persists, use virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install python-postman[execution]
   ```

---

### Issue: Multiple HTTP clients installed

**Symptom:**
Confusion about which client is being used

**Solution:**

python-postman uses httpx by default. If you have other HTTP clients installed (requests, aiohttp), they won't interfere unless you explicitly use them.

To verify:

```python
from python_postman.execution import RequestExecutor
import inspect

# Check what RequestExecutor uses
print(inspect.getsource(RequestExecutor.execute_request))
```

---

## Virtual Environments

### Why use virtual environments?

- Isolate dependencies
- Avoid conflicts
- Reproducible environments
- Easy cleanup

### Create virtual environment

```bash
# Create
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install
pip install python-postman[execution]

# Deactivate
deactivate
```

---

## Requirements Files

### For core usage

```txt
# requirements.txt
python-postman>=1.0.0
```

### For execution

```txt
# requirements.txt
python-postman[execution]>=1.0.0
```

### Pinned versions

```txt
# requirements.txt
python-postman==1.0.0
httpx==0.24.1
```

### Generate from environment

```bash
pip freeze > requirements.txt
```

---

## Docker Usage

### Minimal image (core only)

```dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN pip install python-postman

COPY . .

CMD ["python", "analyze.py"]
```

### With execution

```dockerfile
FROM python:3.9-slim

WORKDIR /app

RUN pip install python-postman[execution]

COPY . .

CMD ["python", "test.py"]
```

---

## Performance Considerations

### Core Library

- **Size:** ~100KB
- **Dependencies:** 0
- **Import time:** <100ms
- **Memory:** Minimal

### With Execution

- **Size:** ~5MB (including httpx)
- **Dependencies:** 1 (httpx)
- **Import time:** ~200ms
- **Memory:** Moderate (connection pooling)

### Optimization Tips

1. **Import only what you need:**

   ```python
   # Good
   from python_postman import PythonPostman

   # Avoid if not needed
   from python_postman.execution import *
   ```

2. **Lazy imports:**

   ```python
   def execute_requests():
       from python_postman.execution import RequestExecutor
       executor = RequestExecutor()
       # ...
   ```

3. **Reuse executor instances:**

   ```python
   # Good - reuses connection pool
   executor = RequestExecutor()
   for request in requests:
       result = await executor.execute_request(request)

   # Bad - creates new connection pool each time
   for request in requests:
       executor = RequestExecutor()
       result = await executor.execute_request(request)
   ```

---

## Security Considerations

### Dependency Security

1. **Keep dependencies updated:**

   ```bash
   pip install --upgrade python-postman[execution]
   ```

2. **Check for vulnerabilities:**

   ```bash
   pip install safety
   safety check
   ```

3. **Use dependency scanning in CI/CD:**
   ```yaml
   # .github/workflows/security.yml
   - name: Check dependencies
     run: |
       pip install safety
       safety check
   ```

### Minimal Dependencies = Smaller Attack Surface

Using core-only installation reduces:

- Number of dependencies
- Potential vulnerabilities
- Attack surface

---

## Troubleshooting

### "No module named 'httpx'"

**Solution:**

```bash
pip install python-postman[execution]
```

### "No module named 'python_postman.execution'"

**Solution:**

```bash
pip install python-postman[execution]
```

### Import works but execution fails

**Check httpx is installed:**

```python
import httpx
print(httpx.__version__)
```

**Reinstall if needed:**

```bash
pip uninstall python-postman httpx
pip install python-postman[execution]
```

---

## Best Practices

1. **Use extras syntax for clarity:**

   ```bash
   # Clear intent
   pip install python-postman[execution]

   # Less clear
   pip install python-postman httpx
   ```

2. **Document dependencies in README:**

   ````markdown
   ## Installation

   For core functionality:

   ```bash
   pip install python-postman
   ```
   ````

   For API testing:

   ```bash
   pip install python-postman[execution]
   ```

   ```

   ```

3. **Use virtual environments:**
   Always use virtual environments for projects

4. **Pin versions in production:**

   ```txt
   python-postman[execution]==1.0.0
   ```

5. **Keep dependencies updated:**
   Regularly update dependencies for security and features

---

## Next Steps

- [Installation Guide](installation.md)
- [Quick Start](quickstart.md)
- [Architecture Overview](../architecture/overview.md)
- [Troubleshooting](troubleshooting.md)

# Troubleshooting Guide

## Overview

This guide helps you diagnose and resolve common issues when using python-postman. Issues are organized by category with symptoms, causes, and solutions.

## Installation Issues

### Issue: Cannot import python_postman

**Symptoms:**

```python
ImportError: No module named 'python_postman'
```

**Causes:**

- Package not installed
- Wrong Python environment

**Solutions:**

1. Install the package:

   ```bash
   pip install python-postman
   ```

2. Verify installation:

   ```bash
   pip list | grep python-postman
   ```

3. Check Python environment:

   ```bash
   which python
   pip --version
   ```

4. If using virtual environment, ensure it's activated:
   ```bash
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

---

### Issue: Cannot import execution module

**Symptoms:**

```python
ImportError: No module named 'httpx'
ModuleNotFoundError: No module named 'python_postman.execution'
```

**Causes:**

- Execution dependencies not installed
- Missing httpx library

**Solutions:**

1. Install with execution extras:

   ```bash
   pip install python-postman[execution]
   ```

2. Or install httpx separately:

   ```bash
   pip install httpx
   ```

3. Verify httpx installation:
   ```bash
   pip show httpx
   ```

---

## Parsing Issues

### Issue: FileNotFoundError when parsing collection

**Symptoms:**

```python
FileNotFoundError: [Errno 2] No such file or directory: 'collection.json'
```

**Causes:**

- File doesn't exist
- Wrong file path
- Wrong working directory

**Solutions:**

1. Check file exists:

   ```bash
   ls collection.json
   ```

2. Use absolute path:

   ```python
   import os
   file_path = os.path.abspath("collection.json")
   collection = parser.parse(file_path)
   ```

3. Check working directory:
   ```python
   import os
   print(f"Current directory: {os.getcwd()}")
   ```

---

### Issue: JSON parsing error

**Symptoms:**

```python
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)
ValueError: Invalid JSON format
```

**Causes:**

- Malformed JSON file
- Empty file
- Wrong file format

**Solutions:**

1. Validate JSON file:

   ```bash
   python -m json.tool collection.json
   ```

2. Check file is not empty:

   ```bash
   cat collection.json
   ```

3. Verify it's a Postman collection:

   ```python
   import json
   with open("collection.json") as f:
       data = json.load(f)
       print(data.get("info", {}).get("schema"))
   ```

4. Re-export from Postman:
   - Open Postman
   - Right-click collection
   - Export → Collection v2.1

---

### Issue: Unsupported schema version

**Symptoms:**

```python
SchemaVersionError: Unsupported schema version: v1.0.0
```

**Causes:**

- Old Postman collection format
- Unsupported schema version

**Solutions:**

1. Check schema version:

   ```python
   print(collection.info.schema)
   ```

2. Supported versions:

   - v2.0.0
   - v2.1.0

3. Update collection in Postman:
   - Open collection in Postman
   - Export as Collection v2.1
   - Use the new export

---

## Validation Issues

### Issue: Collection validation fails

**Symptoms:**

```python
result = collection.validate()
# result.is_valid == False
```

**Causes:**

- Missing required fields
- Invalid URLs
- Malformed data

**Solutions:**

1. Check validation errors:

   ```python
   result = collection.validate()
   if not result.is_valid:
       for error in result.errors:
           print(f"Error: {error}")
       for warning in result.warnings:
           print(f"Warning: {warning}")
   ```

2. Common validation issues:

   - Missing request name
   - Invalid URL format
   - Missing HTTP method
   - Invalid authentication configuration

3. Fix issues in Postman and re-export

---

## Execution Issues

### Issue: Request execution fails with timeout

**Symptoms:**

```python
result.success == False
result.error_type == "timeout"
```

**Causes:**

- Request takes too long
- Server not responding
- Network issues

**Solutions:**

1. Increase timeout:

   ```python
   executor = RequestExecutor(timeout=60.0)  # 60 seconds
   ```

2. Check server is accessible:

   ```bash
   curl -I https://api.example.com
   ```

3. Test with longer timeout:
   ```python
   executor = RequestExecutor(timeout=120.0)
   result = await executor.execute_request(request, context)
   ```

---

### Issue: SSL certificate verification fails

**Symptoms:**

```python
result.error_type == "ssl"
SSLError: certificate verify failed
```

**Causes:**

- Self-signed certificate
- Expired certificate
- Certificate mismatch

**Solutions:**

1. Disable SSL verification (development only):

   ```python
   executor = RequestExecutor(verify_ssl=False)
   ```

2. Provide custom CA bundle:

   ```python
   import httpx
   executor = RequestExecutor()
   # Configure httpx client with custom CA
   ```

3. Fix certificate on server (production)

**Warning:** Never disable SSL verification in production!

---

### Issue: Variables not resolving

**Symptoms:**

```python
# URL contains {{variable}} instead of actual value
result.response.url == "https://api.example.com/{{user_id}}"
```

**Causes:**

- Variable not set in context
- Wrong variable name
- Missing ExecutionContext

**Solutions:**

1. Set variables in context:

   ```python
   context = ExecutionContext()
   context.set_variable("user_id", "123")
   result = await executor.execute_request(request, context=context)
   ```

2. Check variable names:

   ```python
   # In collection: {{user_id}}
   # In code: context.set_variable("user_id", "123")
   ```

3. Debug variable resolution:

   ```python
   print(f"Variables: {context._variables}")
   ```

4. Check variable scope:
   - Collection variables
   - Environment variables
   - Global variables

---

### Issue: Authentication not working

**Symptoms:**

```python
result.response.status_code == 401  # Unauthorized
result.response.status_code == 403  # Forbidden
```

**Causes:**

- Missing authentication
- Wrong credentials
- Authentication not applied

**Solutions:**

1. Check authentication is configured:

   ```python
   if request.has_auth():
       print(f"Auth type: {request.auth.type}")
   else:
       print("No authentication configured")
   ```

2. Verify authentication inheritance:

   ```python
   from python_postman.introspection import AuthResolver

   resolved_auth = AuthResolver.resolve_auth(request, None, collection)
   print(f"Auth from: {resolved_auth.source}")
   print(f"Auth type: {resolved_auth.auth.type if resolved_auth.auth else None}")
   ```

3. Set authentication variables:

   ```python
   context.set_variable("api_key", "your-api-key")
   context.set_variable("token", "your-token")
   ```

4. Check authentication parameters:
   ```python
   if request.auth:
       for param in request.auth.parameters:
           print(f"{param.key}: {param.value}")
   ```

---

### Issue: Connection refused

**Symptoms:**

```python
result.error_type == "connection"
ConnectionRefusedError: [Errno 61] Connection refused
```

**Causes:**

- Server not running
- Wrong host/port
- Firewall blocking connection

**Solutions:**

1. Verify server is running:

   ```bash
   curl https://api.example.com
   ```

2. Check URL is correct:

   ```python
   print(request.url.to_string())
   ```

3. Test connectivity:

   ```bash
   ping api.example.com
   telnet api.example.com 443
   ```

4. Check firewall settings

---

## Script Execution Issues

### Issue: Pre-request script fails

**Symptoms:**

```python
result.error_type == "script"
# Script execution error
```

**Causes:**

- JavaScript syntax error
- Undefined variables
- Unsupported JavaScript features

**Solutions:**

1. Check script syntax in Postman

2. Verify script uses supported features:

   - `pm.variables.set()`
   - `pm.environment.set()`
   - `pm.request`

3. Debug script:

   ```javascript
   console.log("Debug: variable value", pm.variables.get("var"));
   ```

4. Simplify script to isolate issue

---

### Issue: Test script fails

**Symptoms:**

```python
result.test_results.failed > 0
```

**Causes:**

- Assertion failures
- Wrong expected values
- Response format mismatch

**Solutions:**

1. Check test results:

   ```python
   for test in result.test_results.tests:
       if not test.passed:
           print(f"Failed: {test.name}")
           print(f"Error: {test.error}")
   ```

2. Verify response format:

   ```python
   print(result.response.text)
   print(result.response.json())
   ```

3. Update test expectations

4. Debug in Postman first

---

## Performance Issues

### Issue: Slow collection parsing

**Symptoms:**

- Parsing takes a long time
- High memory usage

**Causes:**

- Very large collection
- Many nested folders
- Large example responses

**Solutions:**

1. Use streaming for large collections:

   ```python
   # Process requests one at a time
   for request in collection.get_requests():
       process_request(request)
   ```

2. Limit example response size in Postman

3. Split large collections into smaller ones

4. Use search to filter before processing:
   ```python
   # Only process specific requests
   requests = collection.search().by_folder("Critical").execute()
   ```

---

### Issue: Slow request execution

**Symptoms:**

- Requests take a long time
- High latency

**Causes:**

- Slow server
- Network latency
- Sequential execution

**Solutions:**

1. Use async for concurrent execution:

   ```python
   import asyncio

   results = await asyncio.gather(*[
       executor.execute_request(req, context)
       for req in requests
   ])
   ```

2. Check server performance:

   ```bash
   time curl https://api.example.com
   ```

3. Use connection pooling (automatic with httpx)

4. Optimize server-side performance

---

## Type Checking Issues

### Issue: mypy type errors

**Symptoms:**

```
error: Argument 1 to "execute_request" has incompatible type "str"; expected "Request"
```

**Causes:**

- Wrong type passed
- Missing type hints
- Type checker configuration

**Solutions:**

1. Use correct types:

   ```python
   from python_postman.models import Request

   request: Request = collection.items[0]
   result = await executor.execute_request(request, context)
   ```

2. Add type hints:

   ```python
   from typing import List
   from python_postman.models import Request

   def process_requests(requests: List[Request]) -> None:
       pass
   ```

3. Configure mypy:
   ```ini
   # mypy.ini
   [mypy]
   ignore_missing_imports = True
   ```

---

## Common Error Messages

### "Invalid HTTP method"

**Cause:** Using unsupported HTTP method

**Solution:**

```python
from python_postman.types.http_methods import HttpMethod

# Use enum
request.method = HttpMethod.GET

# Or valid string
request.method = "GET"  # Must be uppercase
```

---

### "Cannot instantiate abstract class 'Item'"

**Cause:** Trying to create Item directly

**Solution:**

```python
# Don't do this
item = Item(name="test")

# Do this instead
request = Request(name="test", method="GET", url=url)
# Or
folder = Folder(name="test")
```

---

### "Variable not found"

**Cause:** Variable not set in context

**Solution:**

```python
context = ExecutionContext()
context.set_variable("variable_name", "value")
```

---

## Debugging Tips

### Enable Debug Logging

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("python_postman")
logger.setLevel(logging.DEBUG)
```

### Inspect Request Before Execution

```python
print(f"Method: {request.method}")
print(f"URL: {request.url.to_string()}")
print(f"Headers: {request.headers}")
print(f"Body: {request.body.raw if request.has_body() else None}")
print(f"Auth: {request.auth.type if request.has_auth() else None}")
```

### Inspect Response After Execution

```python
if result.success:
    print(f"Status: {result.response.status_code}")
    print(f"Headers: {result.response.headers}")
    print(f"Body: {result.response.text}")
    print(f"Duration: {result.duration_ms}ms")
else:
    print(f"Error: {result.error}")
    print(f"Error type: {result.error_type}")
```

### Use Python Debugger

```python
import pdb

# Set breakpoint
pdb.set_trace()

# Or use breakpoint() in Python 3.7+
breakpoint()
```

## Getting Help

If you're still experiencing issues:

1. **Check Documentation**

   - [Architecture Overview](../architecture/overview.md)
   - [Model Layer](../architecture/model-layer.md)
   - [Execution Layer](../architecture/execution-layer.md)

2. **Search Issues**

   - Check GitHub issues for similar problems
   - Search Stack Overflow

3. **Create Issue**

   - Provide minimal reproducible example
   - Include error messages
   - Include Python version and library version
   - Include collection structure (sanitized)

4. **Community Support**
   - Ask in discussions
   - Join community chat

## Version-Specific Issues

### Python Version Compatibility

**Minimum Python Version:** 3.7+

**Recommended:** Python 3.9+

Check your Python version:

```bash
python --version
```

### Library Version

Check installed version:

```bash
pip show python-postman
```

Upgrade to latest:

```bash
pip install --upgrade python-postman
```

## Next Steps

- [Architecture Overview](../architecture/overview.md)
- [Decision Tree](decision-tree.md)
- [Complete Examples](../examples/)

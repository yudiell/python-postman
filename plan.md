# Plan: Sync Code & Documentation, Validate with Real Collections

## What This Project Is

python-postman is a Python library for programmatically working with Postman collection.json files. It has two layers:

1. **Model layer (core, zero dependencies)** — parse collections into Python objects, search, validate, transform, serialize.
2. **Execution layer (optional, requires httpx)** — execute HTTP requests, resolve variables, handle auth, run scripts.

## What's Wrong

The documentation and source code have drifted apart significantly. The docs describe APIs that don't exist (`parser.parse()`, `SyncRequestExecutor`, `response.cookies`), use wrong parameter names, show incorrect constructor patterns, and misrepresent the dependency structure. The application itself works — it just isn't accurately documented.

## What This Plan Does

1. Fix code gaps where docs promise useful functionality that should exist
2. Test everything against 9 real-world Postman collections
3. Update all documentation to match reality
4. Update all example Python files to match reality

---

## Phase 1: Fix Code Gaps

### 1.1 Add `Collection.to_json()` method

**File:** `python_postman/models/collection.py`

Docs reference `collection.to_json(indent=2)` but only `to_dict()` exists. Add this method after `to_dict()`:

```python
def to_json(self, indent: int = None) -> str:
    """Serialize collection to JSON string.

    Args:
        indent: JSON indentation level (None for compact)

    Returns:
        JSON string representation of the collection
    """
    import json
    return json.dumps(self.to_dict(), indent=indent)
```

### 1.2 Fix version in `__init__.py`

**File:** `python_postman/__init__.py`

Change `__version__ = "0.8.0"` to `__version__ = "0.9.0"` (line 93). Must match `pyproject.toml` which already says `0.9.0`.

### 1.3 Fix Python version classifiers in `pyproject.toml`

**File:** `pyproject.toml`

The `requires-python = ">=3.9"` is correct. Fix these inconsistencies:

- Remove `"Programming Language :: Python :: 3.8"` from classifiers
- Change `[tool.black]` `target-version` from `["py38"]` to `["py39"]`
- Change `[tool.mypy]` `python_version` from `"3.8"` to `"3.9"`

### 1.4 Make httpx truly optional

**File:** `pyproject.toml`

Currently `httpx>=0.28.1` is in the core `dependencies` list, but the entire architecture is designed around httpx being optional (try/except import guard in `__init__.py`, conditional `__all__` extension, `is_execution_available()` function). Move it:

**Before:**
```toml
dependencies = [
    "httpx>=0.28.1",
]

[project.optional-dependencies]
execution = [
    "python-dotenv>=1.0.0",
]
```

**After:**
```toml
dependencies = []

[project.optional-dependencies]
execution = [
    "httpx>=0.28.1",
    "python-dotenv>=1.0.0",
]
```

**Impact on tests:** 11 test files import execution classes unconditionally. These will still work because the dev/test environment has httpx installed. But if you want to be thorough, the following test files should have a skip guard added at the top:

```python
import pytest
try:
    from python_postman import is_execution_available
    if not is_execution_available():
        pytest.skip("httpx not installed", allow_module_level=True)
except ImportError:
    pytest.skip("httpx not installed", allow_module_level=True)
```

**Files needing the guard (only if httpx is not in the test environment):**
- `tests/test_auth_handler.py`
- `tests/test_executor.py`
- `tests/test_execution_context.py`
- `tests/test_execution_exceptions.py`
- `tests/test_extensions.py`
- `tests/test_script_runner.py`
- `tests/test_variable_resolver.py`
- `tests/test_variable_tracer.py`
- `tests/test_execution_reporter.py`
- `tests/execution_tests/test_cftc_comprehensive.py`
- `tests/execution_tests/example_cftc_usage.py`

**Files already guarded (no changes needed):**
- `tests/test_imports.py` — uses `if is_execution_available():`
- `tests/test_request_execution.py` — uses `patch.dict("sys.modules", ...)`
- `tests/test_collection.py` — uses `pytest.importorskip("httpx")`

### 1.5 Add `[all]` extras group

**File:** `pyproject.toml`

Add after the existing `execution` and `dev` groups:

```toml
all = [
    "httpx>=0.28.1",
    "python-dotenv>=1.0.0",
    "pytest>=8.4.2",
    "pytest-cov>=4.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "isort>=5.12.0",
    "mypy>=1.0.0",
]
```

---

## Phase 2: Test with Real-World Collections

### 2.1 Copy collections into test data

Copy 9 Postman collections from `~/Downloads/examples/` to `tests/test_data/real_world/`. Rename to remove spaces:

```bash
mkdir -p tests/test_data/real_world
cp ~/Downloads/examples/ArgusWS.postman_collection.json tests/test_data/real_world/
cp ~/Downloads/examples/EIA\ APIv2.postman_collection.json tests/test_data/real_world/EIA_APIv2.postman_collection.json
cp ~/Downloads/examples/EIA\ Bulk\ Files.postman_collection.json tests/test_data/real_world/EIA_Bulk_Files.postman_collection.json
cp ~/Downloads/examples/Genscape\ Oil\ Production\ and\ Forecasting.postman_collection.json tests/test_data/real_world/Genscape_Oil_Production.postman_collection.json
cp ~/Downloads/examples/Genscape\ Oil\ Refineries.postman_collection.json tests/test_data/real_world/Genscape_Oil_Refineries.postman_collection.json
cp ~/Downloads/examples/Genscape\ Oil\ Storage.postman_collection.json tests/test_data/real_world/Genscape_Oil_Storage.postman_collection.json
cp ~/Downloads/examples/Genscape\ Oil\ Transportation.postman_collection.json tests/test_data/real_world/Genscape_Oil_Transportation.postman_collection.json
cp ~/Downloads/examples/Per\ Security\ Requests.postman_collection.json tests/test_data/real_world/Per_Security_Requests.postman_collection.json
cp ~/Downloads/examples/Petroleum.gov.gy.postman_collection.json tests/test_data/real_world/Petroleum_gov_gy.postman_collection.json
```

**Collection characteristics (for writing targeted tests):**

| Collection | Schema | Folders | Auth | Variables | Events | Responses | Special Features |
|---|---|---|---|---|---|---|---|
| ArgusWS | v2.1.0 | Yes (1) | SOAP headers | 2 | Yes (test scripts) | Yes | SOAP/XML bodies, example responses |
| EIA APIv2 | v2.1.0 | Deep (5+ levels) | API Key (query) | Minimal | No | Yes | Path params `:route1` `:facet_id`, largest file (37K lines) |
| EIA Bulk Files | v2.1.0 | No | None | 2 | Yes (empty) | No | Simplest collection, path param `:bulk_file_name` |
| Genscape Oil Production | v2.1.0 | Yes (3+ levels) | API Key (header) | 1 | No | No | Complex query params with enums |
| Genscape Oil Refineries | v2.1.0 | Yes (2) | API Key (header) | 3 | No | No | Disabled query params (`"disabled": true`) |
| Genscape Oil Storage | v2.1.0 | Yes (nested) | API Key (header) | 1 | No | Yes | Detailed descriptions |
| Genscape Oil Transportation | v2.1.0 | Yes (2+ levels) | API Key (header) | 1 | No | Yes | Multiple endpoints |
| Per Security Requests | v2.1.0 | No | Custom headers | 2 | Yes (test assertion) | No | JSON POST body, `pm.test()` script |
| Petroleum.gov.gy | v2.1.0 | No | None | 1 | Yes (empty) | No | Google Sheets URLs, `?output=csv` |

### 2.2 Create test file

**File:** `tests/test_real_world_collections.py`

Write a parametrized pytest suite that loads each collection and tests:

1. **Parsing**: `PythonPostman.from_file(path)` succeeds without error
2. **Info**: `collection.info.name` is a non-empty string, `collection.info.schema` contains "v2.1.0"
3. **Schema detection**: `collection.schema_version` is `SchemaVersion.V2_1_0`
4. **Validation**: `collection.validate().is_valid` is `True`
5. **Requests**: `list(collection.get_requests())` is non-empty
6. **list_requests**: `collection.list_requests()` returns a list of strings
7. **get_variables**: `collection.get_variables()` returns a dict
8. **to_dict roundtrip**: `Collection.from_dict(collection.to_dict())` produces an equivalent object (same info.name, same request count)
9. **to_json roundtrip**: `json.loads(collection.to_json())` is valid JSON and re-parseable
10. **Search**: `collection.search().by_method("GET").execute()` returns a list
11. **Statistics**: `collection.get_statistics().collect()` returns a dict with `"total_requests"` key
12. **Request properties**: every request has non-empty `name`, non-empty `method`, and a `url` object

**Targeted tests (not parametrized — specific to certain collections):**

13. **Deep folder navigation** (EIA APIv2): `collection.get_folder_by_name(...)` finds a nested folder
14. **Auth on collection** (Genscape Oil Refineries): `collection.auth` is not None or requests have auth headers
15. **Events/scripts** (Per Security Requests): at least one request has `request.has_test_script() == True`
16. **Example responses** (ArgusWS): at least one request has `len(request.responses) > 0`
17. **Variables** (Genscape Oil Refineries): `collection.get_variables()` returns a non-empty dict with `"baseUrl"` key
18. **Large collection perf** (EIA APIv2): parsing completes in under 5 seconds

### 2.3 Run full test suite and fix failures

```bash
pytest tests/ -v --tb=short
```

Real-world collections may surface edge cases. Common ones to watch for:
- `protocolProfileBehavior` fields in items (should be ignored by parser)
- Disabled query parameters (`"disabled": true` on query params)
- Empty event scripts (event exists but `script.exec` is `[]`)
- Path parameters in URL strings (`:paramName`)
- Missing `"request"` key in folder items (the parser uses this to distinguish requests from folders — verify it handles all 9 files)

---

## Phase 3: Update Documentation

**Global rule**: Never use line numbers to locate changes — they shift. Use the **searchable text** to find what to change.

### 3.1 `README.md`

**Change A** — Fix Python version requirement:
- Find: `Python 3.8+`
- Replace with: `Python 3.9+`

**Change B** — Fix changelog version:
- Find: `### 0.8.0 (Updated version)`
- Replace with: `### 0.9.0 (Updated version)`

**Change C** — Fix auth access pattern. Find this block:
```python
if collection.auth.type == "bearer":
    token = collection.auth.bearer.get("token")
    print(f"Bearer Token: {token}")
elif collection.auth.type == "basic":
    username = collection.auth.basic.get("username")
    print(f"Basic Auth Username: {username}")
```
Replace with:
```python
if collection.auth.type == "bearer":
    token = collection.auth.get_bearer_token()
    print(f"Bearer Token: {token}")
elif collection.auth.type == "basic":
    credentials = collection.auth.get_basic_credentials()
    print(f"Basic Auth Username: {credentials['username']}")
```

**Do NOT change:** `folder.get_subfolders()` on line 116 — this method exists and is correct.

### 3.2 `docs/README.md`

**Change A** — Fix ALL occurrences of the stale parser pattern. Search for every instance of `parser = PythonPostman()` and `parser.parse(`. Replace the pattern:
```python
# OLD (wrong)
parser = PythonPostman()
collection = parser.parse("collection.json")

# NEW (correct)
collection = PythonPostman.from_file("collection.json")
```

This appears in the Quick Start section, Execute Requests section, Collection Validation section, Environment Switching section, and Collection Analysis section. Fix all of them.

**Change B** — Fix execute_collection iteration. Find:
```python
results = await executor.execute_collection(collection, context=context)

# Check results
for result in results:
    print(f"{result.request.name}: {result.response.status_code}")
```
Replace with:
```python
collection_result = await executor.execute_collection(collection, context=context)

# Check results
for result in collection_result.results:
    print(f"{result.request.name}: {result.response.status_code}")
```

**Change C** — Fix variable precedence. Find:
```
**Precedence:** Request > Environment > Collection > Global
```
Replace with:
```
**Precedence:** Request > Folder > Collection > Environment
```

**Change D** — Fix the variable scope list. Find:
```
1. Collection variables
2. Environment variables
3. Global variables
4. Request variables (set in scripts)
```
Replace with:
```
1. Request variables (highest precedence)
2. Folder variables
3. Collection variables
4. Environment variables (lowest precedence)
```

### 3.3 `docs/architecture/overview.md`

**Change A** — Fix Strategy Pattern example. Find:
```python
SchemaValidator.get_parser_for_version(version)
```
Replace with:
```python
SchemaValidator.detect_version(schema_url)
```

**Change B** — Fix Visitor Pattern example. Find:
```python
collection.traverse(visitor_function)
```
Replace with:
```python
for request in collection.get_requests():
    process(request)
```

### 3.4 `docs/architecture/model-layer.md`

**Change A** — Fix PythonPostman usage in Key Classes section. Find:
```python
# Parse from file
parser = PythonPostman()
collection = parser.parse("collection.json")

# Parse from dictionary
collection = parser.parse_dict(json_data)
```
Replace with:
```python
# Parse from file
collection = PythonPostman.from_file("collection.json")

# Parse from dictionary
collection = PythonPostman.from_dict(json_data)
```

**Change B** — Fix Key Methods list. Find:
```
- `parse(file_path)` - Parse collection from file
- `parse_dict(data)` - Parse collection from dictionary
- `validate(collection)` - Validate collection structure
```
Replace with:
```
- `from_file(file_path)` - Parse collection from file (classmethod)
- `from_json(json_string)` - Parse collection from JSON string (classmethod)
- `from_dict(data)` - Parse collection from dictionary (classmethod)
- `create_collection(name, description)` - Create new empty collection (classmethod)
- `validate_collection_dict(data)` - Quick validation without creating Collection (classmethod)
```

**Change C** — Fix best practices example. Find any `parser.parse("collection.json")` and replace with `PythonPostman.from_file("collection.json")`.

### 3.5 `docs/architecture/execution-layer.md`

This file has the most issues. Fix all of the following:

**Change A** — Fix PythonPostman usage (appears multiple times). Search and replace all `parser = PythonPostman()` / `parser.parse(` with `PythonPostman.from_file()`.

**Change B** — Fix RequestExecutor constructor docs. Find:
```python
executor = RequestExecutor(
    timeout=30.0,           # Request timeout in seconds
    follow_redirects=True,  # Follow HTTP redirects
    verify_ssl=True,        # Verify SSL certificates
    max_redirects=10        # Maximum redirect hops
)
```
Replace with:
```python
executor = RequestExecutor(
    client_config={"timeout": 30.0, "verify": True, "follow_redirects": True},
    global_headers={"User-Agent": "python-postman/1.0"},
    variable_overrides={"base_url": "https://api.example.com"},
    script_timeout=30.0,    # Script execution timeout in seconds
    request_delay=0.0       # Delay between requests in seconds
)
```

**Change C** — Fix execute_request signature. Find:
```
- `execute_request(request, context=None)` - Execute single request
```
Replace with:
```
- `execute_request(request, context)` - Execute single request (async)
- `execute_request_sync(request, context)` - Execute single request (sync)
```
Also fix any examples showing `executor.execute_request(request)` without context — context is required.

**Change D** — Fix ExecutionContext methods. Find:
```
- `set_variable(key, value)` - Set global variable
- `get_variable(key)` - Get variable value
- `set_environment_variable(key, value)` - Set environment variable
- `get_environment_variable(key)` - Get environment variable
- `clear_variables()` - Clear all variables
```
Replace with:
```
- `set_variable(key, value, scope)` - Set variable in scope ("request", "folder", "collection", "environment")
- `get_variable(key)` - Get variable value (follows precedence)
- `has_variable(key)` - Check if variable exists in any scope
- `get_all_variables()` - Get all variables merged with precedence
- `clear_scope(scope)` - Clear all variables in a scope
- `create_child_context(request_variables)` - Create child context for request execution
```

**Change E** — Fix variable precedence. Find:
```
1. Request variables (set in scripts)
2. Environment variables
3. Collection variables
4. Global variables
```
Replace with:
```
1. Request variables (highest precedence)
2. Folder variables
3. Collection variables
4. Environment variables (lowest precedence)
```

**Change F** — Fix ExecutionResponse docs. Find `response.json()` and replace with `response.json` (it's a property, not a method). Remove any references to `response.reason`, `response.cookies`, and `raise_for_status()` — these don't exist. The actual properties are:
- `status_code` - HTTP status code
- `headers` - Response headers (dict)
- `text` - Response body as text
- `content` - Response body as bytes
- `json` - Response body parsed as JSON (property, not method)
- `elapsed_ms` - Response time in milliseconds
- `elapsed_seconds` - Response time in seconds
- `url` - Final URL (after redirects)
- `request_method` - HTTP method used
- `is_success()`, `is_redirect()`, `is_client_error()`, `is_server_error()` - Status checks
- `to_dict()` - Convert to dictionary

**Change G** — Fix ExecutionResult docs. Find `result.duration_ms` and replace with `result.execution_time_ms`. Remove references to `result.error_type` — it doesn't exist. The `error` field is `Optional[Exception]`. The actual attributes are:
- `request` - Original Request object
- `response` - ExecutionResponse (or None)
- `error` - Exception (or None)
- `test_results` - ScriptResults (or None)
- `execution_time_ms` - Execution duration in milliseconds
- `success` - Property: True if no error and response exists
- `status_code` - Property: HTTP status code or None

**Change H** — Fix test results class. Find all references to `TestResults` and replace with `ScriptResults`. Find `.tests` attribute and replace with `.assertions`. Remove `.all_passed` — doesn't exist. The actual attributes are:
- `passed` - Number of passed assertions
- `failed` - Number of failed assertions
- `assertions` - List of `ScriptAssertion` objects (each has `.name`, `.passed`, `.error`)
- `total` - Property: total assertion count
- `success_rate` - Property: 0.0 to 1.0

**Change I** — Fix execute_collection iteration. Find any `for result in results:` after `execute_collection` and fix to use `collection_result.results`. The return type is `CollectionExecutionResult` with attributes:
- `collection_name` - Name of the collection
- `results` - List of `ExecutionResult`
- `total_time_ms` - Total execution time
- `total_requests`, `successful_requests`, `failed_requests` - Properties
- `success_rate` - Property

**Change J** — Remove `SyncRequestExecutor`. Find:
```python
from python_postman.execution import SyncRequestExecutor

# Create synchronous executor
executor = SyncRequestExecutor()

# Execute synchronously (no await)
result = executor.execute_request(request, context=context)
```
Replace with:
```python
from python_postman.execution import RequestExecutor, ExecutionContext

# Synchronous execution uses the same RequestExecutor class
with RequestExecutor() as executor:
    context = ExecutionContext()
    result = executor.execute_request_sync(request, context)
    print(f"Status: {result.response.status_code}")
```

**Change K** — Remove request hooks section. Find the "Request Hooks" section that documents `before_request_hook` and `after_response_hook`. Remove the entire section — these are not implemented.

**Change L** — Fix custom configuration example. Find:
```python
executor = RequestExecutor(
    timeout=60.0,
    follow_redirects=False,
    verify_ssl=False
)
```
Replace with:
```python
executor = RequestExecutor(
    client_config={"timeout": 60.0, "follow_redirects": False, "verify": False}
)
```

### 3.6 `docs/guides/optional-dependencies.md`

**Change A** — Fix all `parser = PythonPostman()` / `parser.parse()` → `PythonPostman.from_file()`.

**Change B** — Fix execution dependencies list. Find:
```
- `httpx` - Modern HTTP client for Python
- `httpx[http2]` - HTTP/2 support (optional)
```
Replace with:
```
- `httpx` >= 0.28.1 - Modern HTTP client for Python
- `python-dotenv` >= 1.0.0 - Environment variable loading from .env files
```

**Change C** — Remove `flake8` from dev dependency list. It's not in pyproject.toml.

**Change D** — Fix httpx version. Find `>= 0.24.0` and replace with `>= 0.28.1`.

**Change E** — Fix broken links at bottom. Find links to `installation.md` and `quickstart.md`. Replace with links to existing docs (e.g., `../architecture/overview.md` and `../README.md`).

### 3.7 `docs/guides/troubleshooting.md`

Search for `parser = PythonPostman()` and `parser.parse(` patterns. Replace with `PythonPostman.from_file()`. Also check variable precedence references and fix to: request > folder > collection > environment.

### 3.8 `docs/architecture/layer-interaction.md`

Search for `parser = PythonPostman()` and `parser.parse(` patterns. Replace with `PythonPostman.from_file()`.

### 3.9 `docs/guides/decision-tree.md`

Search for `parser = PythonPostman()` and `parser.parse(` patterns. Replace with `PythonPostman.from_file()`.

### 3.10 `docs/guides/variable-scoping.md`

Verify variable precedence matches code: request > folder > collection > environment. Fix any references to "Global" scope — the code uses "environment" as the lowest scope.

### 3.11 `docs/guides/description-fields.md`

Search for `parser.parse(` pattern and fix if present.

### 3.12 Example Python files in `docs/examples/`

**File: `docs/examples/generate-documentation.py`**
- Find `parser = PythonPostman()` and `collection = parser.parse("collection.json")`
- Replace with `collection = PythonPostman.from_file("collection.json")`

**File: `docs/examples/parse-inspect-modify-execute.py`**
- Find `parser = PythonPostman()` and `collection = parser.parse("collection.json")`
- Replace with `collection = PythonPostman.from_file("collection.json")`
- Find `result.duration_ms` (appears twice, lines ~242 and ~279)
- Replace with `result.execution_time_ms`

### 3.13 Example Python files in `examples/` (root)

**File: `examples/advanced_execution.py`**
- Find `result.response.json()` (method call)
- Replace with `result.response.json` (property access)

**Do NOT change:** `examples/complete_workflow.py` line ~96 contains `pm.response.json()` — this is JavaScript inside a Postman test script string, not Python. Leave it as-is.

### 3.14 `python_postman/statistics/collector.py`

Contains `parser.parse()` in a docstring. Fix the docstring to use `PythonPostman.from_file()`.

---

## Phase 4: Final Validation

### 4.1 Run full test suite

```bash
pytest tests/ -v --tb=short
```

All existing tests + new real-world collection tests must pass.

### 4.2 Grep for stale patterns

Run these commands. **All should return zero results:**

```bash
# Old parser pattern
grep -rn "parser = PythonPostman()" docs/ examples/ python_postman/
grep -rn "parser\.parse(" docs/ examples/ python_postman/
grep -rn "parser\.parse_dict(" docs/ examples/ python_postman/

# Non-existent classes/methods
grep -rn "SyncRequestExecutor" docs/ examples/
grep -rn "get_environment_variable" docs/
grep -rn "set_environment_variable" docs/
grep -rn "clear_variables" docs/
grep -rn "raise_for_status" docs/

# Wrong attribute names
grep -rn "duration_ms" docs/ examples/
grep -rn "error_type" docs/ examples/

# Wrong class names
grep -rn "TestResults" docs/ examples/

# Wrong property access (should be .json not .json())
grep -rn "response\.json()" docs/ examples/

# Non-existent response attributes
grep -rn "response\.reason" docs/
grep -rn "response\.cookies" docs/

# Wrong Python version
grep -rn "Python 3\.8" docs/ README.md pyproject.toml

# Wrong httpx version
grep -rn "0\.24\.0" docs/

# Non-existent hooks
grep -rn "before_request_hook\|after_response_hook" docs/
```

**Exceptions (greps that are OK to have results):**
- `response.json()` in `examples/complete_workflow.py` — that's JavaScript inside a string, not Python
- `python_postman/execution/response.py` may reference `.json()` internally to call httpx's method — that's correct internal implementation

### 4.3 Things that are correct — do NOT "fix" these

These were investigated and confirmed to be accurate in the docs:

- `Folder.get_subfolders()` — exists on the Folder class (README.md line 116)
- `collection.search().by_method("POST").execute()` — works as documented
- `collection.get_statistics()` — works as documented
- `AuthResolver.resolve_auth(request, folder, collection)` — works as documented
- `request.execute()` and `request.execute_sync()` — exist on Request class
- `collection.execute()` — exists on Collection class
- `RequestExtensions` — exists and works as documented in README.md
- `collection.create_executor()` — exists on Collection class

---

## Execution Order

```
Phase 1 (Code Fixes) ─────────────────────────────────────
  1.1  Add Collection.to_json()
  1.2  Fix __version__ to "0.9.0"
  1.3  Fix pyproject.toml classifiers/tool versions
  1.4  Move httpx to optional deps
  1.5  Add [all] extras group
                    │
Phase 2 (Test with Real Collections) ─────────────────────
  2.1  Copy 9 collections to tests/test_data/real_world/
  2.2  Write tests/test_real_world_collections.py
  2.3  Run full test suite, fix any failures
                    │
Phase 3 (Update Docs & Examples) ─────────────────────────
  3.1   README.md (auth pattern, version, Python version)
  3.2   docs/README.md (parser pattern, precedence, iteration)
  3.3   docs/architecture/overview.md (fake methods)
  3.4   docs/architecture/model-layer.md (parser pattern, methods list)
  3.5   docs/architecture/execution-layer.md (biggest — 12 changes)
  3.6   docs/guides/optional-dependencies.md (deps, versions, links)
  3.7   docs/guides/troubleshooting.md (parser pattern scan)
  3.8   docs/architecture/layer-interaction.md (parser pattern scan)
  3.9   docs/guides/decision-tree.md (parser pattern scan)
  3.10  docs/guides/variable-scoping.md (precedence check)
  3.11  docs/guides/description-fields.md (parser pattern scan)
  3.12  docs/examples/*.py (parser pattern, duration_ms)
  3.13  examples/advanced_execution.py (response.json())
  3.14  python_postman/statistics/collector.py (docstring)
                    │
Phase 4 (Final Validation) ───────────────────────────────
  4.1  Run full test suite
  4.2  Grep for stale patterns (all must be clean)
  4.3  Confirm "do not change" list is untouched
```

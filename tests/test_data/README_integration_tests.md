# Integration Test Collections

This directory contains test collections specifically designed for integration testing of the HTTP request execution functionality.

## Test Collections

### 1. execution_collection.json

- **Purpose**: Basic execution testing with variables, auth, and scripts
- **Features**:
  - Variable substitution in URLs, headers, and body
  - Bearer token authentication
  - Pre-request and test scripts
  - Collection-level and request-level events
- **Requests**: 4 requests covering GET, POST, authenticated, and error scenarios

### 2. nested_execution_collection.json

- **Purpose**: Testing nested folder structures and variable scoping
- **Features**:
  - Multi-level folder hierarchy
  - Folder-level variable scoping
  - Authentication inheritance
  - Complex variable chains across requests
- **Structure**: Authentication folder + User Management folder with subfolders

### 3. auth_execution_collection.json

- **Purpose**: Testing various authentication types
- **Features**:
  - Basic authentication
  - Bearer token authentication
  - API key authentication (header and query)
  - Collection-level auth inheritance
- **Requests**: 6 requests covering all auth types

### 4. performance_collection.json

- **Purpose**: Performance and parallel execution testing
- **Features**:
  - Multiple fast requests for parallel execution
  - Variable chaining across requests
  - Performance timing validation
- **Requests**: 8 requests including variable chain scenarios

### 5. error_scenarios_collection.json

- **Purpose**: Error handling and edge case testing
- **Features**:
  - Network errors (connection refused)
  - HTTP errors (404, 500)
  - Timeout scenarios
  - Variable resolution errors
  - Authentication errors
  - Script execution errors
- **Requests**: 8 requests covering various error scenarios

## Integration Test Structure

The integration tests are organized into several test classes:

### TestSingleRequestExecution

- Tests individual request execution scenarios
- Covers variable substitution, authentication, extensions
- Tests both async and sync execution patterns

### TestCollectionExecution

- Tests full collection execution
- Covers parallel vs sequential execution
- Tests error handling strategies (stop vs continue on error)

### TestScriptExecution

- Tests pre-request and test script execution
- Validates script environment and variable updates

### TestErrorHandling

- Tests various error scenarios
- Validates graceful error handling and reporting

### TestPerformanceAndParallelExecution

- Tests performance characteristics
- Validates parallel execution capabilities
- Tests large collection handling

### TestVariableStateManagement

- Tests variable state across request execution
- Validates variable scoping and inheritance

### TestRequestModelIntegration

- Tests integration with Request and Collection model methods
- Validates convenience methods for execution

## Test Server

The integration tests include a built-in HTTP test server that:

- Handles various HTTP methods (GET, POST, PUT)
- Supports different authentication types
- Simulates various response scenarios (success, error, slow)
- Provides realistic API endpoints for testing

## Running Integration Tests

```bash
# Run all integration tests
python -m pytest tests/test_execution_integration.py -v

# Run specific test class
python -m pytest tests/test_execution_integration.py::TestSingleRequestExecution -v

# Run with coverage
python -m pytest tests/test_execution_integration.py --cov=python_postman.execution

# Skip integration tests if httpx not available
python -m pytest tests/test_execution_integration.py -v -m "not integration"
```

## Requirements

Integration tests require:

- httpx >= 0.25.0 (install with `pip install -e ".[execution]"`)
- pytest-asyncio for async test support

## Test Coverage

The integration tests cover:

- ✅ Single request execution (sync and async)
- ✅ Variable substitution and resolution
- ✅ Authentication handling (Bearer, Basic, API Key)
- ✅ Request extensions and modifications
- ✅ Collection-level execution
- ✅ Error handling and recovery
- ✅ Performance and parallel execution
- ✅ Variable state management
- ✅ Model integration (Request.execute(), Collection.execute())
- ⚠️ Script execution (basic implementation, may need enhancement)
- ⚠️ Complex nested folder execution (needs port updates)

## Known Issues

1. **Script Execution**: The JavaScript script execution has syntax issues that need to be resolved
2. **Port Configuration**: Some tests still use hardcoded ports and need dynamic port updates
3. **Complex Collections**: Some complex collection scenarios may need additional test server endpoints

## Future Enhancements

1. Add more realistic test server endpoints
2. Implement proper JavaScript script execution environment
3. Add WebSocket and streaming request tests
4. Add file upload/download tests
5. Add certificate and SSL testing scenarios

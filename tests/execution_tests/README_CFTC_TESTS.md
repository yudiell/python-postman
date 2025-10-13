# CFTC Collection Comprehensive Test Suite

A comprehensive, self-contained test suite for validating the CFTC (Commodity Futures Trading Commission) Postman collection execution functionality.

## Overview

This test suite provides extensive testing of the `cftc.gov.postman_collection.json` collection, covering:

1. **Collection Loading & Validation** - Verifies collection structure and metadata
2. **Variable Resolution & Scoping** - Tests variable substitution at different scopes
3. **Authentication Configuration** - Validates API key authentication setup
4. **Single Request Execution** - Tests executing individual requests with parameters
5. **Multiple Dataset Execution** - Tests batch execution across multiple datasets
6. **Error Handling & Edge Cases** - Validates error scenarios and edge cases
7. **Performance & Timing** - Measures and validates execution timing
8. **Response Validation** - Verifies response structure and JSON parsing

## Features

- **Self-contained**: No external dependencies beyond `python_postman` library
- **Flexible execution modes**: Run validation-only tests or full API execution tests
- **Detailed reporting**: Comprehensive test results with timing information
- **Verbose mode**: Optional detailed output for debugging
- **Real API testing**: Execute actual requests against CFTC API endpoints

## Usage

### Basic Usage

Run all validation tests (no API calls required):

```bash
python tests/execution_tests/test_cftc_comprehensive.py --validation-only
```

### Full Test Suite (Requires API Token)

To run the complete test suite including actual API execution:

1. Get a CFTC API token from https://dev.socrata.com/foundry/publicreporting.cftc.gov/
2. Set the environment variable:

```bash
export CFTC_API_TOKEN=your_token_here
```

3. Run the full test suite:

```bash
python tests/execution_tests/test_cftc_comprehensive.py
```

### Verbose Mode

Enable detailed output for debugging:

```bash
python tests/execution_tests/test_cftc_comprehensive.py --validation-only --verbose
```

### Command-Line Options

- `--validation-only`: Run only validation tests (no API calls)
- `--verbose`: Enable detailed output showing test progress and results

## Test Categories

### 1. Collection Loading & Validation (5 tests)

Tests basic collection structure and metadata:

- ✅ Collection file exists
- ✅ Collection loads successfully
- ✅ Collection has expected structure
- ✅ Collection has required variables
- ✅ Collection has authentication

**Example output:**

```
📦 Category 1: Collection Loading & Validation
✅ PASS | Collection file exists (0.01ms)
✅ PASS | Collection loads successfully (0.25ms)
✅ PASS | Collection has expected structure (0.08ms)
✅ PASS | Collection has required variables (0.06ms)
✅ PASS | Collection has authentication (0.06ms)
```

### 2. Variable Resolution & Scoping (4 tests)

Tests variable substitution and scoping:

- ✅ Basic variable resolution
- ✅ Variable override with environment
- ✅ URL variable resolution
- ✅ Authentication variable resolution

**Example output:**

```
🔧 Category 2: Variable Resolution & Scoping
✅ PASS | Basic variable resolution (0.19ms)
✅ PASS | Variable override with environment (0.07ms)
✅ PASS | URL variable resolution (0.08ms)
✅ PASS | Authentication variable resolution (0.06ms)
```

### 3. Authentication Configuration (2 tests)

Tests authentication setup and handling:

- ✅ Authentication configuration
- ✅ Missing token handling

### 4. Single Request Execution (3 tests) _Requires API token_

Tests executing individual requests:

- ✅ Execute with default dataset (kh3c-gbw2)
- ✅ Execute with alternate dataset (yw9f-hn96)
- ✅ Execute with custom parameters

### 5. Multiple Dataset Execution (1 test) _Requires API token_

Tests batch execution:

- ✅ Execute multiple datasets

### 6. Error Handling & Edge Cases (2 tests) _Requires API token_

Tests error scenarios:

- ✅ Invalid dataset ID
- ✅ Missing request handling

### 7. Performance & Timing (1 test) _Requires API token_

Tests execution timing:

- ✅ Execution timing capture

### 8. Response Validation (2 tests) _Requires API token_

Tests response handling:

- ✅ Response structure
- ✅ Response JSON parsing

## CFTC Datasets

The test suite works with two CFTC datasets:

### Dataset 1: kh3c-gbw2

- **Name**: Disaggregated Futures-and-Options
- **Description**: Disaggregated Futures-and-Options Combined data
- **Endpoint**: `https://publicreporting.cftc.gov/resource/kh3c-gbw2`

### Dataset 2: yw9f-hn96

- **Name**: Traders in Financial Futures
- **Description**: Traders in Financial Futures- Futures-and-Options Combined data
- **Endpoint**: `https://publicreporting.cftc.gov/resource/yw9f-hn96`

## Example Output

### Validation-Only Mode

```
================================================================================
CFTC Collection Comprehensive Test Suite
================================================================================

⚠️  Running in VALIDATION ONLY mode (no API calls)
Verbose: False
================================================================================

📦 Category 1: Collection Loading & Validation
--------------------------------------------------------------------------------
✅ PASS | Collection file exists (0.01ms)
✅ PASS | Collection loads successfully (0.25ms)
✅ PASS | Collection has expected structure (0.08ms)
✅ PASS | Collection has required variables (0.06ms)
✅ PASS | Collection has authentication (0.06ms)

🔧 Category 2: Variable Resolution & Scoping
--------------------------------------------------------------------------------
✅ PASS | Basic variable resolution (0.19ms)
✅ PASS | Variable override with environment (0.07ms)
✅ PASS | URL variable resolution (0.08ms)
✅ PASS | Authentication variable resolution (0.06ms)

🔐 Category 3: Authentication Configuration
--------------------------------------------------------------------------------
✅ PASS | Authentication configuration (0.06ms)
✅ PASS | Missing token handling (0.06ms)

================================================================================
Test Summary
================================================================================

Total Tests: 11
Passed: 11 ✅
Failed: 0 ❌

Total Execution Time: 0.98ms
================================================================================

🎉 All tests passed!
```

### Full Test Suite (with API token)

When run with a valid API token, the test suite executes all 20 tests including actual API calls:

```
================================================================================
CFTC Collection Comprehensive Test Suite
================================================================================

🚀 Running full test suite (includes API calls)
Verbose: False
================================================================================

[... validation tests ...]

🚀 Category 4: Single Request Execution
--------------------------------------------------------------------------------
✅ PASS | Execute with default dataset (1234.56ms)
✅ PASS | Execute with alternate dataset (987.65ms)
✅ PASS | Execute with custom parameters (876.54ms)

🔄 Category 5: Multiple Dataset Execution
--------------------------------------------------------------------------------
✅ PASS | Execute multiple datasets (2345.67ms)

⚠️  Category 6: Error Handling & Edge Cases
--------------------------------------------------------------------------------
✅ PASS | Invalid dataset ID (543.21ms)
✅ PASS | Missing request handling (0.05ms)

⏱️  Category 7: Performance & Timing
--------------------------------------------------------------------------------
✅ PASS | Execution timing capture (765.43ms)

✅ Category 8: Response Validation
--------------------------------------------------------------------------------
✅ PASS | Response structure (654.32ms)
✅ PASS | Response JSON parsing (543.21ms)

================================================================================
Test Summary
================================================================================

Total Tests: 20
Passed: 20 ✅
Failed: 0 ❌

Total Execution Time: 8765.43ms
================================================================================

🎉 All tests passed!
```

## Implementation Details

### Self-Contained Design

The test script is completely self-contained and includes:

- **CFTCExecutor class**: Lightweight executor for CFTC collection
- **TestResult dataclass**: Captures test execution results
- **CFTCTestSuite class**: Orchestrates test execution
- **DatasetInfo dataclass**: Metadata about CFTC datasets

### No External Dependencies

The script only depends on:

- `python_postman` library (core functionality)
- Standard library modules (`asyncio`, `os`, `sys`, `time`, `pathlib`, `typing`, `dataclasses`)

### Test Isolation

Each test is isolated and can be run independently. Tests use async context managers to ensure proper resource cleanup.

## Troubleshooting

### Missing API Token

If you see this error:

```
❌ FAIL | Execute with default dataset
      CFTC_API_TOKEN not configured in environment
```

Solution: Set the `CFTC_API_TOKEN` environment variable:

```bash
export CFTC_API_TOKEN=your_token_here
```

### Collection File Not Found

If you see this error:

```
❌ FAIL | Collection file exists
      Collection file not found: /path/to/cftc.gov.postman_collection.json
```

Solution: Ensure you're running the script from the project root directory, or that the collection file exists at `tests/test_data/cftc.gov.postman_collection.json`.

### Import Errors

If you see import errors, ensure the `python_postman` package is installed:

```bash
pip install -e .
```

## Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed
- `130`: Test execution interrupted by user (Ctrl+C)

## Integration with CI/CD

The test script is designed to work in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run CFTC validation tests
  run: python tests/execution_tests/test_cftc_comprehensive.py --validation-only

- name: Run CFTC full tests
  env:
    CFTC_API_TOKEN: ${{ secrets.CFTC_API_TOKEN }}
  run: python tests/execution_tests/test_cftc_comprehensive.py
```

## Contributing

When adding new tests:

1. Add the test method to the appropriate category
2. Follow the naming convention: `test_<category>_<description>`
3. Use `self.log()` for verbose output
4. Use `assert` statements for validation
5. Add `if self.validation_only` checks for tests requiring API calls
6. Update this README with the new test description

## License

This test suite is part of the python-postman project and follows the same license.

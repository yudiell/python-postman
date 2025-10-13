# CFTC Test Suite - Quick Start Guide

## 🚀 Quick Start

### Run Validation Tests (No API Token Required)

```bash
python tests/execution_tests/test_cftc_comprehensive.py --validation-only
```

This runs 11 tests that validate collection structure, variable resolution, and authentication configuration without making any API calls.

### Run Full Test Suite (Requires API Token)

```bash
# 1. Get your API token from https://dev.socrata.com/foundry/publicreporting.cftc.gov/
# 2. Set the environment variable
export CFTC_API_TOKEN=your_token_here

# 3. Run all tests
python tests/execution_tests/test_cftc_comprehensive.py
```

This runs all 20 tests including actual API execution against CFTC endpoints.

### Enable Verbose Output

```bash
python tests/execution_tests/test_cftc_comprehensive.py --validation-only --verbose
```

Shows detailed test progress and results.

## 📊 What Gets Tested

### Without API Token (11 tests)

- ✅ Collection file structure
- ✅ Variable resolution
- ✅ Authentication configuration
- ✅ URL template resolution

### With API Token (20 tests)

All of the above, plus:

- ✅ Real API request execution
- ✅ Multiple dataset handling
- ✅ Error handling
- ✅ Response validation
- ✅ Performance timing

## 🎯 Expected Results

### Validation-Only Mode

```
Total Tests: 11
Passed: 11 ✅
Failed: 0 ❌
Total Execution Time: ~1ms
```

### Full Test Suite

```
Total Tests: 20
Passed: 20 ✅
Failed: 0 ❌
Total Execution Time: ~8-10 seconds
```

## 🔧 Troubleshooting

**Problem**: `CFTC_API_TOKEN not configured in environment`

**Solution**:

```bash
export CFTC_API_TOKEN=your_token_here
```

**Problem**: `Collection file not found`

**Solution**: Run from project root directory:

```bash
cd /path/to/python-postman
python tests/execution_tests/test_cftc_comprehensive.py --validation-only
```

**Problem**: Import errors

**Solution**: Install the package:

```bash
pip install -e .
```

## 📝 Test Categories

| Category            | Tests | Requires Token |
| ------------------- | ----- | -------------- |
| Collection Loading  | 5     | ❌             |
| Variable Resolution | 4     | ❌             |
| Authentication      | 2     | ❌             |
| Single Request      | 3     | ✅             |
| Multiple Datasets   | 1     | ✅             |
| Error Handling      | 2     | ✅             |
| Performance         | 1     | ✅             |
| Response Validation | 2     | ✅             |

## 🌐 CFTC Datasets Tested

1. **kh3c-gbw2**: Disaggregated Futures-and-Options Combined data
2. **yw9f-hn96**: Traders in Financial Futures Combined data

## 💡 Tips

- Use `--validation-only` for quick checks during development
- Use `--verbose` when debugging test failures
- Run full suite before committing changes
- Tests are isolated and can be run repeatedly

## 📚 More Information

See [README_CFTC_TESTS.md](README_CFTC_TESTS.md) for complete documentation.

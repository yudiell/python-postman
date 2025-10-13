#!/usr/bin/env python3
"""
Comprehensive CFTC Collection Execution Tests

This script provides a comprehensive test suite for the CFTC collection,
demonstrating all key functionality with real API execution capabilities.

Test Categories:
1. Collection Loading & Validation
2. Variable Resolution & Scoping
3. Authentication Configuration
4. Single Request Execution
5. Multiple Dataset Execution
6. Error Handling & Edge Cases
7. Performance & Timing
8. Response Validation

Usage:
    # Run all tests (requires API token for execution tests)
    python test_cftc_comprehensive.py

    # Run only validation tests (no API token required)
    python test_cftc_comprehensive.py --validation-only

    # Run with custom API token
    CFTC_API_TOKEN=your_token python test_cftc_comprehensive.py

    # Run with verbose output
    python test_cftc_comprehensive.py --verbose
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from python_postman import PythonPostman, RequestExecutor, ExecutionContext, ExecutionResult
from python_postman.models.collection import Collection


@dataclass
class TestResult:
    """Result of a test execution."""
    name: str
    passed: bool
    duration_ms: float
    message: str
    details: Optional[str] = None


@dataclass
class DatasetInfo:
    """Information about a CFTC dataset."""
    dataset_id: str
    name: str
    description: str


class CFTCExecutor:
    """Self-contained executor for CFTC collection tests."""

    # Known CFTC datasets
    DATASETS = {
        "kh3c-gbw2": DatasetInfo(
            dataset_id="kh3c-gbw2",
            name="Disaggregated Futures-and-Options",
            description="Disaggregated Futures-and-Options Combined data"
        ),
        "yw9f-hn96": DatasetInfo(
            dataset_id="yw9f-hn96",
            name="Traders in Financial Futures",
            description="Traders in Financial Futures- Futures-and-Options Combined data"
        ),
    }

    def __init__(self, collection_path: Path, api_token: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """Initialize CFTC executor."""
        self.collection_path = collection_path
        self.api_token = api_token or os.getenv("CFTC_API_TOKEN", "")
        self.config = config or {}
        self.collection: Optional[Collection] = None
        self.executor: Optional[RequestExecutor] = None

    def load_collection(self) -> Collection:
        """Load the CFTC collection."""
        self.collection = PythonPostman.from_file(self.collection_path)
        return self.collection

    def setup_execution_context(
        self,
        dataset_id: Optional[str] = None,
        additional_variables: Optional[Dict[str, str]] = None
    ) -> ExecutionContext:
        """Create execution context with proper variable scoping."""
        # Start with collection variables
        collection_vars = {}
        if self.collection and self.collection.variables:
            for var in self.collection.variables:
                if dataset_id and var.key == "datasetId":
                    continue
                collection_vars[var.key] = var.value

        # Environment variables (higher precedence)
        env_vars = {
            "cftc-X-App-Token": self.api_token,
        }

        # Override dataset if specified
        if dataset_id:
            env_vars["datasetId"] = dataset_id

        # Add additional variables
        if additional_variables:
            env_vars.update(additional_variables)

        context = ExecutionContext(
            collection_variables=collection_vars,
            environment_variables=env_vars
        )

        # Store collection reference for auth inheritance
        if self.collection:
            context._collection = self.collection

        return context

    async def execute_single_request(
        self,
        dataset_id: str,
        offset: int = 0,
        limit: int = 10,
        order: str = "report_date_as_yyyy_mm_dd"
    ) -> ExecutionResult:
        """Execute a single request with specified parameters."""
        if self.collection is None:
            self.load_collection()

        request = self.collection.get_request_by_name("getApiData")
        if not request:
            raise ValueError("Request 'getApiData' not found in collection")

        if self.collection.auth and not self.api_token:
            raise ValueError("Missing required API token for authenticated collection")

        # Create execution context
        context = self.setup_execution_context(dataset_id=dataset_id)

        # Create executor if needed
        if self.executor is None:
            timeout = self.config.get("request_timeout", 30.0)
            verify_ssl = self.config.get("verify_ssl", True)
            request_delay = self.config.get("request_delay", 0.0)

            self.executor = RequestExecutor(
                client_config={
                    "timeout": timeout,
                    "verify": verify_ssl,
                    "follow_redirects": True,
                },
                request_delay=request_delay,
            )

        # Execute the request
        result = await self.executor.execute_request(request, context)
        return result

    async def execute_multiple_datasets(
        self,
        datasets: Optional[List[str]] = None,
        limit: int = 10
    ) -> Dict[str, ExecutionResult]:
        """Execute requests for multiple datasets."""
        if datasets is None:
            datasets = list(self.DATASETS.keys())

        results = {}
        for dataset_id in datasets:
            result = await self.execute_single_request(
                dataset_id=dataset_id,
                limit=limit
            )
            results[dataset_id] = result

            # Small delay between requests
            if len(datasets) > 1:
                await asyncio.sleep(0.5)

        return results

    async def close(self) -> None:
        """Close executor and clean up resources."""
        if self.executor:
            await self.executor.aclose()
            self.executor = None

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


class CFTCTestSuite:
    """Comprehensive test suite for CFTC collection."""

    def __init__(self, validation_only: bool = False, verbose: bool = False):
        """
        Initialize test suite.

        Args:
            validation_only: If True, only run validation tests (no API calls)
            verbose: If True, print detailed output
        """
        self.validation_only = validation_only
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.executor: Optional[CFTCExecutor] = None
        
        # Get collection path
        test_data_path = Path(__file__).parent.parent / "test_data"
        self.collection_path = test_data_path / "cftc.gov.postman_collection.json"
        
        # Get API token from environment
        self.api_token = os.getenv("CFTC_API_TOKEN")

    def log(self, message: str, force: bool = False) -> None:
        """Log message if verbose mode is enabled."""
        if self.verbose or force:
            print(message)

    def add_result(self, result: TestResult) -> None:
        """Add test result and display it."""
        self.results.append(result)
        status = "✅ PASS" if result.passed else "❌ FAIL"
        self.log(f"{status} | {result.name} ({result.duration_ms:.2f}ms)", force=True)
        if not result.passed:
            self.log(f"      {result.message}", force=True)
        if result.details and self.verbose:
            self.log(f"      {result.details}")

    async def run_test(self, name: str, test_func) -> TestResult:
        """
        Run a single test and capture result.

        Args:
            name: Test name
            test_func: Async test function to execute

        Returns:
            TestResult object
        """
        self.log(f"\n🧪 Running: {name}")
        start_time = time.time()

        try:
            await test_func()
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=name,
                passed=True,
                duration_ms=duration_ms,
                message="Test passed"
            )
        except AssertionError as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=name,
                passed=False,
                duration_ms=duration_ms,
                message=str(e)
            )
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            return TestResult(
                name=name,
                passed=False,
                duration_ms=duration_ms,
                message=f"Unexpected error: {type(e).__name__}: {str(e)}"
            )

    # ========================================================================
    # Test Category 1: Collection Loading & Validation
    # ========================================================================

    async def test_collection_exists(self) -> None:
        """Test that CFTC collection file exists."""
        assert self.collection_path.exists(), f"Collection file not found: {self.collection_path}"
        assert self.collection_path.is_file(), f"Collection path is not a file: {self.collection_path}"

        self.log(f"   ✓ Collection file exists: {self.collection_path}")

    async def test_collection_loads(self) -> None:
        """Test that collection can be loaded and parsed."""
        collection = PythonPostman.from_file(self.collection_path)

        assert collection is not None, "Collection is None"
        assert collection.info is not None, "Collection info is None"
        assert collection.info.name == "cftc.gov", f"Unexpected collection name: {collection.info.name}"

        self.log(f"   ✓ Collection loaded: {collection.info.name}")

    async def test_collection_structure(self) -> None:
        """Test that collection has expected structure."""
        collection = PythonPostman.from_file(self.collection_path)

        # Check for requests
        requests = list(collection.get_requests())
        assert len(requests) > 0, "Collection has no requests"

        # Check for specific request
        get_api_data = collection.get_request_by_name("getApiData")
        assert get_api_data is not None, "Request 'getApiData' not found"
        assert get_api_data.method == "GET", f"Unexpected method: {get_api_data.method}"

        self.log(f"   ✓ Collection has {len(requests)} request(s)")
        self.log(f"   ✓ Found request: {get_api_data.name}")

    async def test_collection_variables(self) -> None:
        """Test that collection has required variables."""
        collection = PythonPostman.from_file(self.collection_path)

        assert collection.variables is not None, "Collection has no variables"

        # Check for required variables
        var_dict = {var.key: var.value for var in collection.variables}

        required_vars = ["baseURL", "datasetId"]
        for var_name in required_vars:
            assert var_name in var_dict, f"Required variable '{var_name}' not found"

        self.log(f"   ✓ Collection has {len(var_dict)} variable(s)")
        for key, value in var_dict.items():
            self.log(f"     - {key} = {value}")

    async def test_collection_authentication(self) -> None:
        """Test that collection has authentication configured."""
        collection = PythonPostman.from_file(self.collection_path)

        assert collection.auth is not None, "Collection has no authentication"
        assert collection.auth.type == "apikey", f"Unexpected auth type: {collection.auth.type}"

        config = collection.auth.get_api_key_config()
        assert config is not None, "API key configuration is None"
        assert config.get("key") == "X-App-Token", f"Unexpected key name: {config.get('key')}"

        self.log(f"   ✓ Authentication type: {collection.auth.type}")
        self.log(f"   ✓ API key name: {config.get('key')}")

    # ========================================================================
    # Test Category 2: Variable Resolution & Scoping
    # ========================================================================

    async def test_variable_resolution_basic(self) -> None:
        """Test basic variable resolution."""
        async with CFTCExecutor(self.collection_path, api_token="test_token_12345") as executor:
            executor.load_collection()

            context = executor.setup_execution_context()

            # Test collection variable resolution
            base_url = context.get_variable("baseURL")
            assert base_url is not None, "baseURL not resolved"
            assert "publicreporting.cftc.gov" in base_url, f"Unexpected baseURL: {base_url}"

            self.log(f"   ✓ baseURL resolved: {base_url}")

    async def test_variable_resolution_override(self) -> None:
        """Test variable override with environment scope."""
        async with CFTCExecutor(self.collection_path, api_token="test_token_12345") as executor:
            executor.load_collection()

            # Create context with default dataset
            context1 = executor.setup_execution_context()
            dataset1 = context1.get_variable("datasetId")

            # Create context with overridden dataset
            context2 = executor.setup_execution_context(dataset_id="yw9f-hn96")
            dataset2 = context2.get_variable("datasetId")

            assert dataset1 != dataset2, "Dataset override did not work"
            assert dataset2 == "yw9f-hn96", f"Unexpected dataset: {dataset2}"

            self.log(f"   ✓ Default dataset: {dataset1}")
            self.log(f"   ✓ Override dataset: {dataset2}")

    async def test_variable_resolution_url(self) -> None:
        """Test URL variable resolution."""
        async with CFTCExecutor(self.collection_path, api_token="test_token_12345") as executor:
            executor.load_collection()

            request = executor.collection.get_request_by_name("getApiData")
            assert request is not None, "Request not found"
            assert request.url is not None, "Request has no URL"

            context = executor.setup_execution_context(dataset_id="kh3c-gbw2")
            resolved_url = context.resolve_variables(request.url.raw)

            assert "{{" not in resolved_url, f"URL still has unresolved variables: {resolved_url}"
            assert "kh3c-gbw2" in resolved_url, f"Dataset not in URL: {resolved_url}"

            self.log(f"   ✓ Original URL: {request.url.raw}")
            self.log(f"   ✓ Resolved URL: {resolved_url}")

    async def test_variable_resolution_auth(self) -> None:
        """Test authentication variable resolution."""
        async with CFTCExecutor(self.collection_path, api_token="test_token_12345") as executor:
            executor.load_collection()

            context = executor.setup_execution_context()

            # Get auth token variable
            token = context.get_variable("cftc-X-App-Token")
            assert token is not None, "Auth token not resolved"
            assert token == "test_token_12345", f"Unexpected token: {token}"

            self.log(f"   ✓ Auth token resolved: {token[:8]}...")

    # ========================================================================
    # Test Category 3: Authentication Configuration
    # ========================================================================

    async def test_auth_configuration(self) -> None:
        """Test authentication configuration."""
        async with CFTCExecutor(self.collection_path, api_token="test_token_12345") as executor:
            executor.load_collection()

            assert executor.collection.auth is not None, "No authentication configured"
            assert executor.collection.auth.type == "apikey", "Wrong auth type"

            config_dict = executor.collection.auth.get_api_key_config()
            assert config_dict is not None, "No API key config"
            assert config_dict.get("key") == "X-App-Token", "Wrong key name"

            self.log(f"   ✓ Auth type: {executor.collection.auth.type}")
            self.log(f"   ✓ Key name: {config_dict.get('key')}")

    async def test_auth_missing_token(self) -> None:
        """Test behavior when API token is missing."""
        async with CFTCExecutor(self.collection_path, api_token=None) as executor:
            executor.load_collection()

            # Should not raise error during setup
            context = executor.setup_execution_context()

            # Token should be empty or None
            token = context.get_variable("cftc-X-App-Token")
            assert token == "" or token is None, f"Expected empty token, got: {token}"

            self.log(f"   ✓ Missing token handled correctly")

    # ========================================================================
    # Test Category 4: Single Request Execution (requires API token)
    # ========================================================================

    async def test_execute_single_request_default_dataset(self) -> None:
        """Test executing single request with default dataset."""
        if self.validation_only:
            self.log("   ⊘ Skipped (validation only mode)")
            return

        if not self.api_token:
            raise AssertionError("CFTC_API_TOKEN not configured in environment")

        async with CFTCExecutor(self.collection_path, api_token=self.api_token) as executor:
            executor.load_collection()

            result = await executor.execute_single_request(
                dataset_id="kh3c-gbw2",
                limit=5
            )

            assert result is not None, "Result is None"
            assert result.success, f"Request failed: {result.error}"
            assert result.response is not None, "Response is None"
            assert result.response.status_code == 200, f"Unexpected status: {result.response.status_code}"

            self.log(f"   ✓ Request succeeded")
            self.log(f"   ✓ Status: {result.response.status_code}")
            self.log(f"   ✓ Execution time: {result.execution_time_ms:.2f}ms")

    async def test_execute_single_request_alternate_dataset(self) -> None:
        """Test executing single request with alternate dataset."""
        if self.validation_only:
            self.log("   ⊘ Skipped (validation only mode)")
            return

        if not self.api_token:
            raise AssertionError("CFTC_API_TOKEN not configured in environment")

        async with CFTCExecutor(self.collection_path, api_token=self.api_token) as executor:
            executor.load_collection()

            result = await executor.execute_single_request(
                dataset_id="yw9f-hn96",
                limit=5
            )

            assert result is not None, "Result is None"
            assert result.success, f"Request failed: {result.error}"
            assert result.response is not None, "Response is None"
            assert result.response.status_code == 200, f"Unexpected status: {result.response.status_code}"

            self.log(f"   ✓ Request succeeded")
            self.log(f"   ✓ Status: {result.response.status_code}")

    async def test_execute_with_parameters(self) -> None:
        """Test executing request with custom parameters."""
        if self.validation_only:
            self.log("   ⊘ Skipped (validation only mode)")
            return

        if not self.api_token:
            raise AssertionError("CFTC_API_TOKEN not configured in environment")

        async with CFTCExecutor(self.collection_path, api_token=self.api_token) as executor:
            executor.load_collection()

            result = await executor.execute_single_request(
                dataset_id="kh3c-gbw2",
                offset=10,
                limit=3,
                order="report_date_as_yyyy_mm_dd"
            )

            assert result.success, f"Request failed: {result.error}"

            # Verify response has expected number of records
            if result.response and result.response.json:
                data = result.response.json
                if isinstance(data, list):
                    assert len(data) <= 3, f"Expected max 3 records, got {len(data)}"
                    self.log(f"   ✓ Received {len(data)} records (limit=3)")

    # ========================================================================
    # Test Category 5: Multiple Dataset Execution
    # ========================================================================

    async def test_execute_multiple_datasets(self) -> None:
        """Test executing multiple datasets."""
        if self.validation_only:
            self.log("   ⊘ Skipped (validation only mode)")
            return

        if not self.api_token:
            raise AssertionError("CFTC_API_TOKEN not configured in environment")

        async with CFTCExecutor(self.collection_path, api_token=self.api_token) as executor:
            executor.load_collection()

            datasets = ["kh3c-gbw2", "yw9f-hn96"]
            results = await executor.execute_multiple_datasets(
                datasets=datasets,
                limit=3
            )

            assert len(results) == 2, f"Expected 2 results, got {len(results)}"

            for dataset_id, result in results.items():
                assert result.success, f"Request for {dataset_id} failed: {result.error}"
                self.log(f"   ✓ {dataset_id}: {result.response.status_code}")

    # ========================================================================
    # Test Category 6: Error Handling & Edge Cases
    # ========================================================================

    async def test_invalid_dataset_id(self) -> None:
        """Test handling of invalid dataset ID."""
        if self.validation_only:
            self.log("   ⊘ Skipped (validation only mode)")
            return

        if not self.api_token:
            raise AssertionError("CFTC_API_TOKEN not configured in environment")

        async with CFTCExecutor(self.collection_path, api_token=self.api_token) as executor:
            executor.load_collection()

            result = await executor.execute_single_request(
                dataset_id="invalid-dataset-id",
                limit=5
            )

            # Should not succeed with invalid dataset
            assert not result.success or result.response.status_code != 200, \
                "Request should fail with invalid dataset ID"

            self.log(f"   ✓ Invalid dataset handled correctly")

    async def test_missing_request(self) -> None:
        """Test handling of missing request."""
        async with CFTCExecutor(self.collection_path, api_token="test_token") as executor:
            executor.load_collection()

            # Try to get non-existent request
            request = executor.collection.get_request_by_name("nonExistentRequest")
            assert request is None, "Should return None for non-existent request"

            self.log(f"   ✓ Missing request handled correctly")

    # ========================================================================
    # Test Category 7: Performance & Timing
    # ========================================================================

    async def test_execution_timing(self) -> None:
        """Test that execution timing is captured."""
        if self.validation_only:
            self.log("   ⊘ Skipped (validation only mode)")
            return

        if not self.api_token:
            raise AssertionError("CFTC_API_TOKEN not configured in environment")

        async with CFTCExecutor(self.collection_path, api_token=self.api_token) as executor:
            executor.load_collection()

            result = await executor.execute_single_request(
                dataset_id="kh3c-gbw2",
                limit=1
            )

            assert result.execution_time_ms > 0, "Execution time not captured"
            assert result.execution_time_ms < 30000, f"Execution took too long: {result.execution_time_ms}ms"

            self.log(f"   ✓ Execution time: {result.execution_time_ms:.2f}ms")

    # ========================================================================
    # Test Category 8: Response Validation
    # ========================================================================

    async def test_response_structure(self) -> None:
        """Test that response has expected structure."""
        if self.validation_only:
            self.log("   ⊘ Skipped (validation only mode)")
            return

        if not self.api_token:
            raise AssertionError("CFTC_API_TOKEN not configured in environment")

        async with CFTCExecutor(self.collection_path, api_token=self.api_token) as executor:
            executor.load_collection()

            result = await executor.execute_single_request(
                dataset_id="kh3c-gbw2",
                limit=5
            )

            assert result.response is not None, "Response is None"
            assert result.response.status_code == 200, f"Unexpected status: {result.response.status_code}"
            assert result.response.headers is not None, "Response headers are None"
            assert result.response.content is not None, "Response content is None"

            self.log(f"   ✓ Response structure valid")

    async def test_response_json_parsing(self) -> None:
        """Test that response JSON can be parsed."""
        if self.validation_only:
            self.log("   ⊘ Skipped (validation only mode)")
            return

        if not self.api_token:
            raise AssertionError("CFTC_API_TOKEN not configured in environment")

        async with CFTCExecutor(self.collection_path, api_token=self.api_token) as executor:
            executor.load_collection()

            result = await executor.execute_single_request(
                dataset_id="kh3c-gbw2",
                limit=5
            )

            assert result.response.json is not None, "JSON parsing failed"
            assert isinstance(result.response.json, list), f"Expected list, got {type(result.response.json)}"

            if len(result.response.json) > 0:
                first_record = result.response.json[0]
                assert isinstance(first_record, dict), "Record is not a dictionary"
                self.log(f"   ✓ Parsed {len(result.response.json)} records")

    # ========================================================================
    # Test Execution
    # ========================================================================

    async def run_all_tests(self) -> None:
        """Run all tests in the suite."""
        print("\n" + "="*80)
        print("CFTC Collection Comprehensive Test Suite")
        print("="*80)

        if self.validation_only:
            print("\n⚠️  Running in VALIDATION ONLY mode (no API calls)")
        else:
            print("\n🚀 Running full test suite (includes API calls)")

        print(f"Verbose: {self.verbose}")
        print("="*80)

        # Category 1: Collection Loading & Validation
        print("\n📦 Category 1: Collection Loading & Validation")
        print("-" * 80)
        self.add_result(await self.run_test("Collection file exists", self.test_collection_exists))
        self.add_result(await self.run_test("Collection loads successfully", self.test_collection_loads))
        self.add_result(await self.run_test("Collection has expected structure", self.test_collection_structure))
        self.add_result(await self.run_test("Collection has required variables", self.test_collection_variables))
        self.add_result(await self.run_test("Collection has authentication", self.test_collection_authentication))

        # Category 2: Variable Resolution & Scoping
        print("\n🔧 Category 2: Variable Resolution & Scoping")
        print("-" * 80)
        self.add_result(await self.run_test("Basic variable resolution", self.test_variable_resolution_basic))
        self.add_result(await self.run_test("Variable override with environment", self.test_variable_resolution_override))
        self.add_result(await self.run_test("URL variable resolution", self.test_variable_resolution_url))
        self.add_result(await self.run_test("Authentication variable resolution", self.test_variable_resolution_auth))

        # Category 3: Authentication Configuration
        print("\n🔐 Category 3: Authentication Configuration")
        print("-" * 80)
        self.add_result(await self.run_test("Authentication configuration", self.test_auth_configuration))
        self.add_result(await self.run_test("Missing token handling", self.test_auth_missing_token))

        if not self.validation_only:
            # Category 4: Single Request Execution
            print("\n🚀 Category 4: Single Request Execution")
            print("-" * 80)
            self.add_result(await self.run_test("Execute with default dataset", self.test_execute_single_request_default_dataset))
            self.add_result(await self.run_test("Execute with alternate dataset", self.test_execute_single_request_alternate_dataset))
            self.add_result(await self.run_test("Execute with custom parameters", self.test_execute_with_parameters))

            # Category 5: Multiple Dataset Execution
            print("\n🔄 Category 5: Multiple Dataset Execution")
            print("-" * 80)
            self.add_result(await self.run_test("Execute multiple datasets", self.test_execute_multiple_datasets))

            # Category 6: Error Handling & Edge Cases
            print("\n⚠️  Category 6: Error Handling & Edge Cases")
            print("-" * 80)
            self.add_result(await self.run_test("Invalid dataset ID", self.test_invalid_dataset_id))
            self.add_result(await self.run_test("Missing request handling", self.test_missing_request))

            # Category 7: Performance & Timing
            print("\n⏱️  Category 7: Performance & Timing")
            print("-" * 80)
            self.add_result(await self.run_test("Execution timing capture", self.test_execution_timing))

            # Category 8: Response Validation
            print("\n✅ Category 8: Response Validation")
            print("-" * 80)
            self.add_result(await self.run_test("Response structure", self.test_response_structure))
            self.add_result(await self.run_test("Response JSON parsing", self.test_response_json_parsing))

        # Print summary
        self.print_summary()

    def print_summary(self) -> None:
        """Print test execution summary."""
        print("\n" + "="*80)
        print("Test Summary")
        print("="*80)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"\nTotal Tests: {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")

        if failed > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if not result.passed:
                    print(f"   - {result.name}")
                    print(f"     {result.message}")

        total_time = sum(r.duration_ms for r in self.results)
        print(f"\nTotal Execution Time: {total_time:.2f}ms")

        print("="*80)

        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {failed} test(s) failed")

        print()


async def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Comprehensive CFTC Collection Test Suite"
    )
    parser.add_argument(
        "--validation-only",
        action="store_true",
        help="Run only validation tests (no API calls)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )

    args = parser.parse_args()

    # Create and run test suite
    suite = CFTCTestSuite(
        validation_only=args.validation_only,
        verbose=args.verbose
    )

    try:
        await suite.run_all_tests()

        # Exit with appropriate code
        failed = sum(1 for r in suite.results if not r.passed)
        sys.exit(0 if failed == 0 else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Common Usage Patterns

This example demonstrates common patterns and best practices
for using the python-postman execution features.
"""

import asyncio
import time
from typing import Dict, Any, List
from python_postman import PythonPostman
from python_postman.execution import (
    RequestExecutor,
    ExecutionContext,
    RequestExtensions,
    ExecutionResult,
    CollectionExecutionResult,
)


class APITestSuite:
    """Example class showing how to structure API testing with python-postman."""

    def __init__(self, collection_path: str, base_url: str):
        self.collection = PythonPostman.from_file(collection_path)
        self.base_url = base_url
        self.executor = None
        self.session_data = {}

    async def setup(self):
        """Initialize the test suite."""
        self.executor = RequestExecutor(
            client_config={"timeout": 30.0, "verify": True, "follow_redirects": True},
            global_headers={
                "User-Agent": "python-postman-test-suite/1.0",
                "Accept": "application/json",
            },
        )
        print("✅ Test suite initialized")

    async def teardown(self):
        """Clean up resources."""
        if self.executor:
            await self.executor.aclose()
        print("✅ Test suite cleaned up")

    async def authenticate(self) -> bool:
        """Perform authentication and store session data."""
        context = ExecutionContext(
            environment_variables={
                "base_url": self.base_url,
                "username": "test_user",
                "password": "test_password",
            }
        )

        login_request = self.collection.get_request_by_name("Login")
        if not login_request:
            print("❌ Login request not found")
            return False

        result = await self.executor.execute_request(login_request, context)

        if result.success:
            # Extract session data from response
            try:
                response_data = result.response.json
                self.session_data["token"] = response_data.get("token")
                self.session_data["user_id"] = response_data.get("user_id")
                print("✅ Authentication successful")
                return True
            except Exception as e:
                print(f"❌ Failed to parse auth response: {e}")
                return False
        else:
            print(f"❌ Authentication failed: {result.error}")
            return False

    async def run_smoke_tests(self) -> Dict[str, Any]:
        """Run smoke tests on critical endpoints."""
        print("\n=== Running Smoke Tests ===")

        context = ExecutionContext(
            environment_variables={
                "base_url": self.base_url,
                "auth_token": self.session_data.get("token", ""),
                "user_id": self.session_data.get("user_id", ""),
            }
        )

        smoke_test_requests = ["Health Check", "Get User Profile", "List Resources"]

        results = {}
        for request_name in smoke_test_requests:
            request = self.collection.get_request_by_name(request_name)
            if request:
                result = await self.executor.execute_request(request, context)
                results[request_name] = {
                    "success": result.success,
                    "status_code": (
                        result.response.status_code if result.response else None
                    ),
                    "response_time_ms": (
                        result.response.elapsed_ms if result.response else None
                    ),
                    "error": str(result.error) if result.error else None,
                }

                status = "✅" if result.success else "❌"
                print(f"  {status} {request_name}: {results[request_name]}")
            else:
                print(f"  ⚠️  {request_name}: Request not found")

        return results

    async def run_load_test(
        self, concurrent_users: int = 5, duration_seconds: int = 30
    ) -> Dict[str, Any]:
        """Run a simple load test."""
        print(
            f"\n=== Running Load Test ({concurrent_users} users, {duration_seconds}s) ==="
        )

        context = ExecutionContext(
            environment_variables={
                "base_url": self.base_url,
                "auth_token": self.session_data.get("token", ""),
            }
        )

        load_test_request = self.collection.get_request_by_name("Load Test Endpoint")
        if not load_test_request:
            print("❌ Load test endpoint not found")
            return {}

        start_time = time.time()
        end_time = start_time + duration_seconds

        results = []
        tasks = []

        async def make_request():
            while time.time() < end_time:
                result = await self.executor.execute_request(load_test_request, context)
                results.append(
                    {
                        "timestamp": time.time(),
                        "success": result.success,
                        "response_time_ms": (
                            result.response.elapsed_ms if result.response else None
                        ),
                        "status_code": (
                            result.response.status_code if result.response else None
                        ),
                    }
                )
                await asyncio.sleep(0.1)  # Small delay between requests

        # Start concurrent users
        for _ in range(concurrent_users):
            tasks.append(asyncio.create_task(make_request()))

        # Wait for all tasks to complete
        await asyncio.gather(*tasks)

        # Calculate statistics
        successful_requests = sum(1 for r in results if r["success"])
        total_requests = len(results)
        avg_response_time = (
            sum(r["response_time_ms"] or 0 for r in results) / total_requests
            if total_requests > 0
            else 0
        )

        load_test_results = {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": total_requests - successful_requests,
            "success_rate": (
                (successful_requests / total_requests * 100)
                if total_requests > 0
                else 0
            ),
            "avg_response_time_ms": avg_response_time,
            "requests_per_second": total_requests / duration_seconds,
        }

        print(f"  📊 Results: {load_test_results}")
        return load_test_results


async def demonstrate_error_handling():
    """Show comprehensive error handling patterns."""
    print("\n=== Error Handling Patterns ===")

    collection = PythonPostman.from_file("error_test_collection.json")

    async with RequestExecutor() as executor:
        # Pattern 1: Basic error checking
        context = ExecutionContext(
            environment_variables={"base_url": "https://httpbin.org"}
        )

        request = collection.get_request_by_name("Test Request")
        if request:
            result = await executor.execute_request(request, context)

            if result.success:
                print("✅ Request successful")
                if result.response.is_success():
                    print("  📊 HTTP success status")
                elif result.response.is_client_error():
                    print(f"  ⚠️  Client error: {result.response.status_code}")
                elif result.response.is_server_error():
                    print(f"  🚨 Server error: {result.response.status_code}")
            else:
                print(f"❌ Request failed: {result.error}")

        # Pattern 2: Handling specific error types
        from python_postman.execution import (
            VariableResolutionError,
            AuthenticationError,
            RequestExecutionError,
        )

        try:
            # This might fail due to missing variables
            bad_context = ExecutionContext()
            result = await executor.execute_request(request, bad_context)
        except VariableResolutionError as e:
            print(f"🔧 Variable error (expected): {e}")
        except AuthenticationError as e:
            print(f"🔐 Auth error: {e}")
        except RequestExecutionError as e:
            print(f"🌐 Request error: {e}")
        except Exception as e:
            print(f"❓ Unexpected error: {e}")


async def demonstrate_performance_patterns():
    """Show performance optimization patterns."""
    print("\n=== Performance Optimization Patterns ===")

    collection = PythonPostman.from_file("performance_collection.json")

    # Pattern 1: Connection pooling and reuse
    executor = RequestExecutor(
        client_config={
            "limits": {"max_connections": 20, "max_keepalive_connections": 10},
            "timeout": 30.0,
        }
    )

    context = ExecutionContext(
        environment_variables={"base_url": "https://httpbin.org"}
    )

    # Pattern 2: Parallel execution for independent requests
    print("🚀 Testing parallel vs sequential execution...")

    # Sequential execution
    start_time = time.time()
    sequential_result = await executor.execute_collection(collection, parallel=False)
    sequential_time = time.time() - start_time

    # Parallel execution
    start_time = time.time()
    parallel_result = await executor.execute_collection(collection, parallel=True)
    parallel_time = time.time() - start_time

    print(f"  📈 Sequential: {sequential_time:.2f}s")
    print(f"  📈 Parallel: {parallel_time:.2f}s")
    print(f"  📊 Speedup: {sequential_time/parallel_time:.2f}x")

    await executor.aclose()


async def demonstrate_testing_patterns():
    """Show patterns for automated testing."""
    print("\n=== Automated Testing Patterns ===")

    collection = PythonPostman.from_file("test_collection.json")

    async with RequestExecutor() as executor:
        context = ExecutionContext(
            environment_variables={
                "base_url": "https://jsonplaceholder.typicode.com",
                "expected_user_count": "10",
            }
        )

        # Pattern 1: Test result validation
        test_request = collection.get_request_by_name("Get Users Test")
        if test_request:
            result = await executor.execute_request(test_request, context)

            if result.test_results:
                print(f"🧪 Test Results:")
                print(f"  ✅ Passed: {result.test_results.passed}")
                print(f"  ❌ Failed: {result.test_results.failed}")

                # Show failed assertions
                for assertion in result.test_results.assertions:
                    if not assertion.passed:
                        print(f"    ❌ {assertion.name}: {assertion.error}")

        # Pattern 2: Collection-wide test execution
        collection_result = await executor.execute_collection(collection)

        if collection_result.test_results:
            total_tests = (
                collection_result.test_results.passed
                + collection_result.test_results.failed
            )
            success_rate = (
                (collection_result.test_results.passed / total_tests * 100)
                if total_tests > 0
                else 0
            )

            print(f"📊 Collection Test Summary:")
            print(f"  Total tests: {total_tests}")
            print(f"  Success rate: {success_rate:.1f}%")


async def main():
    """Run all usage pattern demonstrations."""
    print("🚀 Python Postman Usage Patterns Demo")
    print("=" * 50)

    # Demonstrate structured API testing
    print("\n=== Structured API Testing ===")
    try:
        test_suite = APITestSuite(
            "api_collection.json", "https://jsonplaceholder.typicode.com"
        )
        await test_suite.setup()

        # Run authentication
        if await test_suite.authenticate():
            # Run smoke tests
            smoke_results = await test_suite.run_smoke_tests()

            # Run load test (commented out for demo)
            # load_results = await test_suite.run_load_test(concurrent_users=3, duration_seconds=10)

        await test_suite.teardown()
    except Exception as e:
        print(f"⚠️  Test suite demo skipped (collection not found): {e}")

    # Demonstrate other patterns
    await demonstrate_error_handling()
    await demonstrate_performance_patterns()
    await demonstrate_testing_patterns()

    print("\n✅ All usage pattern demonstrations completed!")


if __name__ == "__main__":
    asyncio.run(main())

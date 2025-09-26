#!/usr/bin/env python3
"""
Synchronous Request Execution Example

This example demonstrates how to execute requests synchronously
for simpler use cases or when async is not needed.
"""

from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext


def main():
    """Demonstrate synchronous request execution."""

    # Load collection
    collection = PythonPostman.from_file("simple_collection.json")

    print(f"Loaded collection: {collection.info.name}")

    # Create executor
    with RequestExecutor() as executor:
        # Create execution context
        context = ExecutionContext(
            environment_variables={
                "base_url": "https://httpbin.org",
                "user_agent": "python-postman-sync",
            }
        )

        # Execute requests synchronously
        for request in collection.get_all_requests():
            print(f"\nExecuting: {request.name}")

            # Execute synchronously
            result = executor.execute_request_sync(request, context)

            if result.success:
                print(f"  ✅ Status: {result.response.status_code}")
                print(f"  ⏱️  Time: {result.response.elapsed_ms:.2f}ms")

                # Show test results if available
                if result.test_results:
                    print(
                        f"  🧪 Tests: {result.test_results.passed} passed, {result.test_results.failed} failed"
                    )

                    # Show failed assertions
                    for assertion in result.test_results.assertions:
                        if not assertion.passed:
                            print(f"    ❌ {assertion.name}: {assertion.error}")
            else:
                print(f"  ❌ Failed: {result.error}")

        print(
            f"\nCompleted execution of {len(list(collection.get_all_requests()))} requests"
        )


def demonstrate_request_methods():
    """Demonstrate using request execution methods directly."""

    # Load collection
    collection = PythonPostman.from_file("api_collection.json")

    # Get a specific request
    request = collection.get_request_by_name("Health Check")
    if not request:
        print("Request 'Health Check' not found")
        return

    # Method 1: Execute with default executor
    print("=== Method 1: Default Executor ===")
    result = request.execute_sync()

    if result.success:
        print(f"✅ Health check passed: {result.response.status_code}")
    else:
        print(f"❌ Health check failed: {result.error}")

    # Method 2: Execute with custom executor
    print("\n=== Method 2: Custom Executor ===")
    executor = RequestExecutor(
        client_config={"timeout": 10.0}, global_headers={"X-Client": "python-postman"}
    )

    context = ExecutionContext(
        environment_variables={"api_url": "https://api.example.com"}
    )

    result = request.execute_sync(executor=executor, context=context)

    if result.success:
        print(f"✅ Request successful: {result.response.status_code}")
        print(f"Response headers: {dict(result.response.headers)}")
    else:
        print(f"❌ Request failed: {result.error}")

    executor.close()


def demonstrate_collection_methods():
    """Demonstrate using collection execution methods."""

    # Load collection
    collection = PythonPostman.from_file("test_suite.json")

    print(f"Executing collection: {collection.info.name}")

    # Create a configured executor for the collection
    executor = collection.create_executor(
        client_config={"timeout": 30.0, "verify": True},
        global_headers={"X-Test-Suite": "python-postman"},
    )

    # Execute the collection (this would be async in real usage)
    # For sync demo, we'll show the setup
    print("Collection executor created with custom configuration")
    print(f"Ready to execute {len(list(collection.get_all_requests()))} requests")

    executor.close()


if __name__ == "__main__":
    print("=== Synchronous Execution Demo ===")
    main()

    print("\n" + "=" * 50)
    print("=== Request Method Demo ===")
    demonstrate_request_methods()

    print("\n" + "=" * 50)
    print("=== Collection Method Demo ===")
    demonstrate_collection_methods()

#!/usr/bin/env python3
"""
Advanced Request Execution Example

This example demonstrates advanced features like variable substitution,
request extensions, authentication, and parallel execution.
"""

import asyncio
from python_postman import PythonPostman
from python_postman.execution import (
    RequestExecutor,
    ExecutionContext,
    RequestExtensions,
)


async def main():
    """Demonstrate advanced execution features."""

    # Load collection
    collection = PythonPostman.from_file("api_collection.json")

    # Create executor with advanced configuration
    executor = RequestExecutor(
        client_config={
            "timeout": 60.0,
            "verify": True,
            "follow_redirects": True,
            "limits": {"max_connections": 10, "max_keepalive_connections": 5},
        },
        global_headers={
            "User-Agent": "python-postman/1.0",
            "Accept": "application/json",
        },
        request_delay=0.1,  # 100ms delay between requests
    )

    # Create execution context with multiple variable scopes
    context = ExecutionContext(
        environment_variables={
            "base_url": "https://api.example.com",
            "version": "v1",
            "timeout": "30",
        },
        collection_variables={"api_key": "{{env_api_key}}", "user_id": "12345"},
    )

    # Example 1: Execute with runtime substitutions
    print("=== Example 1: Runtime Variable Substitutions ===")

    request = collection.get_request_by_name("Get User Profile")
    if request:
        # Runtime variable substitutions
        substitutions = {
            "env_api_key": "sk-live-abc123def456",
            "user_id": "67890",
            "include_details": "true",
        }

        result = await executor.execute_request(
            request, context, substitutions=substitutions
        )

        if result.success:
            print(f"✅ User profile retrieved")
            print(f"Status: {result.response.status_code}")
            # Access response data
            if result.response.headers.get("content-type", "").startswith(
                "application/json"
            ):
                try:
                    data = result.response.json()
                    print(f"User name: {data.get('name', 'N/A')}")
                except:
                    print("Response is not valid JSON")
        else:
            print(f"❌ Failed: {result.error}")

    # Example 2: Execute with request extensions
    print("\n=== Example 2: Request Extensions ===")

    request = collection.get_request_by_name("Create User")
    if request:
        # Define request extensions
        extensions = RequestExtensions(
            header_extensions={
                "X-Request-ID": "req-{{$timestamp}}",
                "X-Client-Version": "1.2.3",
            },
            param_extensions={"source": "python-client", "debug": "true"},
            body_extensions={
                "metadata": {
                    "created_by": "python-postman",
                    "timestamp": "{{$timestamp}}",
                }
            },
        )

        result = await executor.execute_request(request, context, extensions=extensions)

        if result.success:
            print(f"✅ User created successfully")
            print(f"Status: {result.response.status_code}")
        else:
            print(f"❌ Failed: {result.error}")

    # Example 3: Parallel collection execution
    print("\n=== Example 3: Parallel Collection Execution ===")

    # Execute collection in parallel
    start_time = asyncio.get_event_loop().time()

    collection_result = await executor.execute_collection(
        collection, parallel=True, stop_on_error=False
    )

    end_time = asyncio.get_event_loop().time()
    parallel_time = (end_time - start_time) * 1000

    print(f"Parallel execution completed in {parallel_time:.2f}ms")
    print(
        f"Results: {collection_result.successful_requests}/{collection_result.total_requests} successful"
    )

    # Example 4: Sequential execution for comparison
    print("\n=== Example 4: Sequential Collection Execution ===")

    start_time = asyncio.get_event_loop().time()

    collection_result = await executor.execute_collection(
        collection, parallel=False, stop_on_error=False
    )

    end_time = asyncio.get_event_loop().time()
    sequential_time = (end_time - start_time) * 1000

    print(f"Sequential execution completed in {sequential_time:.2f}ms")
    print(
        f"Results: {collection_result.successful_requests}/{collection_result.total_requests} successful"
    )

    # Example 5: Folder execution with variable inheritance
    print("\n=== Example 5: Folder Execution ===")

    auth_folder = collection.get_folder_by_name("Authentication")
    if auth_folder:
        # Create folder-specific context
        folder_context = ExecutionContext(
            environment_variables=context.environment_variables,
            collection_variables=context.collection_variables,
            folder_variables={
                "auth_endpoint": "/auth/login",
                "grant_type": "client_credentials",
            },
        )

        folder_result = await executor.execute_folder(
            auth_folder, folder_context, parallel=False, stop_on_error=True
        )

        print(
            f"Folder execution: {folder_result.successful_requests}/{folder_result.total_requests} successful"
        )

        # Check test results
        if folder_result.test_results:
            print(
                f"Tests: {folder_result.test_results.passed} passed, {folder_result.test_results.failed} failed"
            )

    # Clean up
    await executor.aclose()


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Basic Request Execution Example

This example demonstrates how to execute HTTP requests from a Postman collection
using the python-postman library with httpx integration.
"""

import asyncio
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext


async def main():
    """Demonstrate basic request execution."""

    # Load a Postman collection
    collection = PythonPostman.from_file("sample_collection.json")

    print(f"Loaded collection: {collection.info.name}")
    print(f"Total requests: {len(list(collection.get_all_requests()))}")

    # Create an executor with basic configuration
    executor = RequestExecutor(
        client_config={"timeout": 30.0, "verify": True, "follow_redirects": True}
    )

    # Execute a single request
    request = collection.get_request_by_name("Get Users")
    if request:
        print(f"\nExecuting request: {request.name}")

        # Create execution context
        context = ExecutionContext(
            environment_variables={
                "base_url": "https://jsonplaceholder.typicode.com",
                "api_key": "your-api-key-here",
            }
        )

        # Execute the request
        result = await executor.execute_request(request, context)

        if result.success:
            print(f"✅ Request successful!")
            print(f"Status: {result.response.status_code}")
            print(f"Response time: {result.response.elapsed_ms:.2f}ms")
            print(f"Response size: {len(result.response.text)} bytes")
        else:
            print(f"❌ Request failed: {result.error}")

    # Execute entire collection
    print(f"\nExecuting entire collection...")
    collection_result = await executor.execute_collection(collection)

    print(f"Collection execution completed:")
    print(f"  Total requests: {collection_result.total_requests}")
    print(f"  Successful: {collection_result.successful_requests}")
    print(f"  Failed: {collection_result.failed_requests}")
    print(f"  Total time: {collection_result.total_time_ms:.2f}ms")

    # Clean up
    await executor.aclose()


if __name__ == "__main__":
    asyncio.run(main())

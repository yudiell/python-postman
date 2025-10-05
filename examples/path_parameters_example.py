#!/usr/bin/env python3
"""
Path Parameters Example

This example demonstrates how to use path parameters (like :datasetId, :userId)
in URLs alongside traditional Postman variables (like {{baseURL}}).
"""

import asyncio
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext


def create_sample_collection():
    """Create a sample collection with path parameters."""

    collection_data = {
        "info": {
            "name": "Path Parameters API Collection",
            "description": "Demonstrates path parameter usage",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [
            {"key": "baseURL", "value": "https://api.example.com"},
            {"key": "apiVersion", "value": "v1"},
        ],
        "item": [
            {
                "name": "Get User by ID",
                "request": {
                    "method": "GET",
                    "url": {
                        "raw": "{{baseURL}}/{{apiVersion}}/users/:userId",
                        "host": ["{{baseURL}}"],
                        "path": ["{{apiVersion}}", "users", ":userId"],
                    },
                },
            },
            {
                "name": "Get User Posts",
                "request": {
                    "method": "GET",
                    "url": {
                        "raw": "{{baseURL}}/{{apiVersion}}/users/:userId/posts/:postId",
                        "host": ["{{baseURL}}"],
                        "path": [
                            "{{apiVersion}}",
                            "users",
                            ":userId",
                            "posts",
                            ":postId",
                        ],
                    },
                },
            },
            {
                "name": "CFTC Dataset Example",
                "request": {
                    "method": "GET",
                    "url": {
                        "raw": "{{baseURL}}/:datasetId?$offset=0&$limit=10&$order=report_date_as_yyyy_mm_dd",
                        "host": ["{{baseURL}}"],
                        "path": [":datasetId"],
                        "query": [
                            {"key": "$offset", "value": "0"},
                            {"key": "$limit", "value": "10"},
                            {"key": "$order", "value": "report_date_as_yyyy_mm_dd"},
                        ],
                    },
                },
            },
            {
                "name": "Complex Path Parameters",
                "request": {
                    "method": "PUT",
                    "url": {
                        "raw": "{{baseURL}}/{{apiVersion}}/organizations/:orgId/projects/:projectId/datasets/:datasetId/records/:recordId",
                        "host": ["{{baseURL}}"],
                        "path": [
                            "{{apiVersion}}",
                            "organizations",
                            ":orgId",
                            "projects",
                            ":projectId",
                            "datasets",
                            ":datasetId",
                            "records",
                            ":recordId",
                        ],
                    },
                },
            },
        ],
    }

    return PythonPostman.from_dict(collection_data)


def demonstrate_path_parameter_resolution():
    """Demonstrate path parameter resolution without HTTP execution."""

    print("=== Path Parameter Resolution Demo ===")

    collection = create_sample_collection()

    # Create execution context with path parameter values
    context = ExecutionContext(
        environment_variables={
            "baseURL": "https://api.example.com",
            "apiVersion": "v2",
        },
        collection_variables={
            "userId": "12345",
            "postId": "67890",
            "datasetId": "kh3c-gbw2",
            "orgId": "org-abc",
            "projectId": "proj-123",
            "recordId": "rec-456",
        },
    )

    # Test each request
    for request in collection.get_requests():
        print(f"\n--- {request.name} ---")

        if request.url and request.url.raw:
            original_url = request.url.raw
            resolved_url = context.resolve_variables(original_url)

            print(f"Original:  {original_url}")
            print(f"Resolved:  {resolved_url}")

            # Show what path parameters were found
            import re

            path_params = re.findall(r":([a-zA-Z_][a-zA-Z0-9_]*)", original_url)
            if path_params:
                print(f"Path parameters found: {path_params}")
                for param in path_params:
                    value = context.get_variable(param)
                    print(f"  :{param} -> {value}")


async def demonstrate_full_execution():
    """Demonstrate full request execution with path parameters."""

    print("\n=== Full Request Execution Demo ===")

    # Create a simple collection for testing
    test_collection_data = {
        "info": {
            "name": "HTTPBin Path Parameters Test",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "variable": [{"key": "baseURL", "value": "https://httpbin.org"}],
        "item": [
            {
                "name": "Get Status Code",
                "request": {
                    "method": "GET",
                    "url": {
                        "raw": "{{baseURL}}/status/:statusCode",
                        "host": ["{{baseURL}}"],
                        "path": ["status", ":statusCode"],
                    },
                },
            },
            {
                "name": "Delay Request",
                "request": {
                    "method": "GET",
                    "url": {
                        "raw": "{{baseURL}}/delay/:seconds",
                        "host": ["{{baseURL}}"],
                        "path": ["delay", ":seconds"],
                    },
                },
            },
        ],
    }

    collection = PythonPostman.from_dict(test_collection_data)

    try:
        # Create executor (this will fail if httpx is not installed)
        executor = RequestExecutor(client_config={"timeout": 10.0})

        # Create context with path parameter values
        context = ExecutionContext(
            environment_variables={
                "baseURL": "https://httpbin.org",
                "statusCode": "200",
                "seconds": "1",
            }
        )

        # Execute requests
        for request in collection.get_requests():
            print(f"\n--- Executing {request.name} ---")

            result = await executor.execute_request(request, context)

            if result.success:
                print(f"✅ Success: {result.response.status_code}")
                print(f"URL: {result.response.url}")
                print(f"Time: {result.response.elapsed_ms:.2f}ms")
            else:
                print(f"❌ Failed: {result.error}")

        await executor.aclose()

    except Exception as e:
        print(f"⚠️  HTTP execution not available: {e}")
        print("This is expected if httpx is not installed.")
        print("Path parameter resolution still works for URL building!")


def demonstrate_error_handling():
    """Demonstrate error handling for missing path parameters."""

    print("\n=== Error Handling Demo ===")

    context = ExecutionContext(
        environment_variables={"baseURL": "https://api.example.com"}
        # Note: missing userId parameter
    )

    test_url = "{{baseURL}}/users/:userId/profile"

    try:
        resolved_url = context.resolve_variables(test_url)
        print(f"Resolved: {resolved_url}")
    except Exception as e:
        print(f"✅ Correctly caught error: {e}")

    # Test with the parameter provided
    context.set_variable("userId", "12345", "environment")

    try:
        resolved_url = context.resolve_variables(test_url)
        print(f"✅ After adding parameter: {resolved_url}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def demonstrate_mixed_parameters():
    """Demonstrate mixing Postman variables and path parameters."""

    print("\n=== Mixed Parameters Demo ===")

    context = ExecutionContext(
        environment_variables={
            "protocol": "https",
            "domain": "api.example.com",
            "port": "443",
            "version": "v1",
        },
        collection_variables={"userId": "user123", "resourceId": "res456"},
    )

    # Complex URL with both types of variables
    complex_url = "{{protocol}}://{{domain}}:{{port}}/{{version}}/users/:userId/resources/:resourceId?format=json"

    print(f"Complex URL: {complex_url}")

    resolved_url = context.resolve_variables(complex_url)
    print(f"Resolved:    {resolved_url}")

    expected = (
        "https://api.example.com:443/v1/users/user123/resources/res456?format=json"
    )
    print(f"Expected:    {expected}")
    print(f"Match: {resolved_url == expected}")


async def main():
    """Run all demonstrations."""

    print("🚀 Path Parameters Feature Demo")
    print("=" * 50)

    print("Path parameters allow you to use :parameterName syntax in URLs")
    print("alongside traditional {{variable}} Postman variables.")
    print("Both are resolved using the same variable scoping rules.")

    # Run demonstrations
    demonstrate_path_parameter_resolution()
    await demonstrate_full_execution()
    demonstrate_error_handling()
    demonstrate_mixed_parameters()

    print("\n✅ Path parameters demo completed!")
    print("\nKey points:")
    print("- Use :parameterName for path parameters")
    print("- Use {{variableName}} for Postman variables")
    print(
        "- Both use the same variable scoping: request > folder > collection > environment"
    )
    print("- Path parameters are resolved after Postman variables")
    print("- Missing parameters will raise VariableResolutionError")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""
Authentication Examples

This example demonstrates various authentication methods
and how they are handled during request execution.
"""

import asyncio
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext


async def main():
    """Demonstrate authentication handling."""

    # Load collection with various auth types
    collection = PythonPostman.from_file("auth_collection.json")

    # Create executor
    executor = RequestExecutor()

    # Example 1: Bearer Token Authentication
    print("=== Example 1: Bearer Token Authentication ===")

    context = ExecutionContext(
        environment_variables={
            "bearer_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "api_base": "https://api.example.com",
        }
    )

    bearer_request = collection.get_request_by_name("Get Protected Resource")
    if bearer_request:
        result = await executor.execute_request(bearer_request, context)

        if result.success:
            print(f"✅ Bearer auth successful: {result.response.status_code}")
        else:
            print(f"❌ Bearer auth failed: {result.error}")

    # Example 2: Basic Authentication
    print("\n=== Example 2: Basic Authentication ===")

    context = ExecutionContext(
        environment_variables={
            "username": "admin",
            "password": "secret123",
            "api_base": "https://api.example.com",
        }
    )

    basic_request = collection.get_request_by_name("Admin Login")
    if basic_request:
        result = await executor.execute_request(basic_request, context)

        if result.success:
            print(f"✅ Basic auth successful: {result.response.status_code}")
        else:
            print(f"❌ Basic auth failed: {result.error}")

    # Example 3: API Key Authentication
    print("\n=== Example 3: API Key Authentication ===")

    context = ExecutionContext(
        environment_variables={
            "api_key": "sk-1234567890abcdef",
            "api_base": "https://api.example.com",
        }
    )

    apikey_request = collection.get_request_by_name("List Resources")
    if apikey_request:
        result = await executor.execute_request(apikey_request, context)

        if result.success:
            print(f"✅ API key auth successful: {result.response.status_code}")
        else:
            print(f"❌ API key auth failed: {result.error}")

    # Example 4: Collection-level vs Request-level Auth
    print("\n=== Example 4: Auth Inheritance ===")

    # Collection has default auth, but request can override
    context = ExecutionContext(
        environment_variables={
            "collection_token": "collection-level-token",
            "request_token": "request-specific-token",
            "api_base": "https://api.example.com",
        }
    )

    # Request with collection-level auth
    collection_auth_request = collection.get_request_by_name("Use Collection Auth")
    if collection_auth_request:
        result = await executor.execute_request(collection_auth_request, context)
        print(f"Collection auth result: {result.success}")

    # Request with its own auth (overrides collection)
    request_auth_request = collection.get_request_by_name("Use Request Auth")
    if request_auth_request:
        result = await executor.execute_request(request_auth_request, context)
        print(f"Request auth result: {result.success}")

    # Example 5: Dynamic Auth Token Refresh
    print("\n=== Example 5: Dynamic Auth Token ===")

    # Simulate getting a fresh token
    fresh_token = await get_fresh_auth_token()

    context = ExecutionContext(
        environment_variables={
            "dynamic_token": fresh_token,
            "api_base": "https://api.example.com",
        }
    )

    protected_request = collection.get_request_by_name("Protected Endpoint")
    if protected_request:
        result = await executor.execute_request(protected_request, context)

        if result.success:
            print(f"✅ Dynamic auth successful: {result.response.status_code}")
        else:
            print(f"❌ Dynamic auth failed: {result.error}")

    await executor.aclose()


async def get_fresh_auth_token() -> str:
    """Simulate getting a fresh authentication token."""
    # In real usage, this would make an API call to refresh the token
    await asyncio.sleep(0.1)  # Simulate network delay
    return "fresh-token-" + str(int(asyncio.get_event_loop().time()))


def demonstrate_auth_configuration():
    """Show how to configure authentication in collections."""

    print("=== Authentication Configuration Examples ===")

    # Example collection structure with different auth types
    auth_examples = {
        "bearer": {
            "type": "bearer",
            "bearer": [{"key": "token", "value": "{{bearer_token}}", "type": "string"}],
        },
        "basic": {
            "type": "basic",
            "basic": [
                {"key": "username", "value": "{{username}}", "type": "string"},
                {"key": "password", "value": "{{password}}", "type": "string"},
            ],
        },
        "apikey": {
            "type": "apikey",
            "apikey": [
                {"key": "key", "value": "X-API-Key", "type": "string"},
                {"key": "value", "value": "{{api_key}}", "type": "string"},
                {"key": "in", "value": "header", "type": "string"},
            ],
        },
    }

    for auth_type, config in auth_examples.items():
        print(f"\n{auth_type.upper()} Authentication:")
        print(f"  Type: {config['type']}")

        if auth_type == "bearer":
            print(f"  Token variable: {{{{bearer_token}}}}")
            print(f"  Header: Authorization: Bearer <token>")
        elif auth_type == "basic":
            print(f"  Username variable: {{{{username}}}}")
            print(f"  Password variable: {{{{password}}}}")
            print(f"  Header: Authorization: Basic <base64(username:password)>")
        elif auth_type == "apikey":
            print(f"  Key name: X-API-Key")
            print(f"  Key variable: {{{{api_key}}}}")
            print(f"  Location: header")


if __name__ == "__main__":
    print("Running authentication examples...")
    asyncio.run(main())

    print("\n" + "=" * 50)
    demonstrate_auth_configuration()

#!/usr/bin/env python3
"""
Variable Management Examples

This example demonstrates variable scoping, resolution,
and dynamic variable management during execution.
"""

import asyncio
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext


async def main():
    """Demonstrate variable management features."""

    # Load collection
    collection = PythonPostman.from_file("variable_collection.json")

    # Create executor
    executor = RequestExecutor()

    # Example 1: Variable Scoping and Precedence
    print("=== Example 1: Variable Scoping ===")

    context = ExecutionContext(
        environment_variables={
            "base_url": "https://env.example.com",
            "timeout": "30",
            "debug": "false",
        },
        collection_variables={
            "base_url": "https://collection.example.com",  # Overrides environment
            "api_version": "v1",
            "user_id": "12345",
        },
        folder_variables={
            "timeout": "60",  # Overrides collection and environment
            "endpoint": "/users",
        },
        request_variables={
            "debug": "true",  # Overrides all other scopes
            "format": "json",
        },
    )

    # Show variable resolution precedence
    print("Variable resolution (request > folder > collection > environment):")
    print(f"  base_url: {context.get_variable('base_url')}")  # collection value
    print(f"  timeout: {context.get_variable('timeout')}")  # folder value
    print(f"  debug: {context.get_variable('debug')}")  # request value
    print(f"  api_version: {context.get_variable('api_version')}")  # collection value

    # Example 2: Nested Variable Resolution
    print("\n=== Example 2: Nested Variable Resolution ===")

    context = ExecutionContext(
        environment_variables={
            "protocol": "https",
            "domain": "api.example.com",
            "port": "443",
        },
        collection_variables={
            "base_url": "{{protocol}}://{{domain}}:{{port}}",
            "full_endpoint": "{{base_url}}/{{api_version}}/{{resource}}",
            "api_version": "v2",
            "resource": "users",
        },
    )

    # Resolve nested variables
    resolved_url = context.resolve_variables("{{full_endpoint}}")
    print(f"Nested resolution: {{{{full_endpoint}}}} -> {resolved_url}")

    # Example 3: Dynamic Variable Updates During Execution
    print("\n=== Example 3: Dynamic Variable Updates ===")

    # Start with initial context
    context = ExecutionContext(
        environment_variables={
            "base_url": "https://api.example.com",
            "session_token": "",
        }
    )

    # Simulate login request that sets session token
    login_request = collection.get_request_by_name("Login")
    if login_request:
        result = await executor.execute_request(login_request, context)

        if result.success:
            # Simulate extracting token from response
            # In real usage, this would be done by test scripts
            mock_token = "session-abc123def456"
            context.set_variable("session_token", mock_token, "environment")
            print(f"✅ Login successful, token set: {mock_token[:20]}...")
        else:
            print(f"❌ Login failed: {result.error}")

    # Use the session token in subsequent requests
    protected_request = collection.get_request_by_name("Get Profile")
    if protected_request:
        result = await executor.execute_request(protected_request, context)

        if result.success:
            print(f"✅ Profile retrieved using session token")
        else:
            print(f"❌ Profile request failed: {result.error}")

    # Example 4: Variable Substitution in Different Request Components
    print("\n=== Example 4: Variable Substitution in Request Components ===")

    context = ExecutionContext(
        collection_variables={
            "api_host": "jsonplaceholder.typicode.com",
            "user_id": "1",
            "content_type": "application/json",
            "user_agent": "python-postman/1.0",
            "post_title": "My New Post",
            "post_body": "This is the content of my post",
        }
    )

    # Show how variables are used in different parts of requests
    print("Variables can be used in:")
    print("  URL: https://{{api_host}}/users/{{user_id}}")
    print("  Headers: Content-Type: {{content_type}}")
    print("  Headers: User-Agent: {{user_agent}}")
    print('  Body: {"title": "{{post_title}}", "body": "{{post_body}}"}')

    # Example 5: Error Handling for Missing Variables
    print("\n=== Example 5: Variable Error Handling ===")

    context = ExecutionContext(collection_variables={"existing_var": "value"})

    try:
        # This will raise an error because missing_var doesn't exist
        resolved = context.resolve_variables("{{existing_var}} and {{missing_var}}")
        print(f"Resolved: {resolved}")
    except Exception as e:
        print(f"❌ Variable resolution error: {e}")

    # Example 6: Circular Reference Protection
    print("\n=== Example 6: Circular Reference Protection ===")

    context = ExecutionContext(
        collection_variables={
            "var_a": "{{var_b}}",
            "var_b": "{{var_c}}",
            "var_c": "{{var_a}}",  # Creates circular reference
        }
    )

    try:
        resolved = context.resolve_variables("{{var_a}}")
        print(f"Resolved: {resolved}")
    except Exception as e:
        print(f"❌ Circular reference detected: {e}")

    await executor.aclose()


def demonstrate_variable_management():
    """Show variable management operations."""

    print("=== Variable Management Operations ===")

    # Create context
    context = ExecutionContext()

    # Set variables in different scopes
    context.set_variable("env_var", "environment_value", "environment")
    context.set_variable("collection_var", "collection_value", "collection")
    context.set_variable("folder_var", "folder_value", "folder")
    context.set_variable("request_var", "request_value", "request")

    print("Variables set in different scopes:")
    print(f"  Environment: {context.environment_variables}")
    print(f"  Collection: {context.collection_variables}")
    print(f"  Folder: {context.folder_variables}")
    print(f"  Request: {context.request_variables}")

    # Get all variables merged
    all_vars = context.get_all_variables()
    print(f"\nAll variables merged: {all_vars}")

    # Check variable existence
    print(f"\nVariable existence checks:")
    print(f"  'collection_var' exists: {context.has_variable('collection_var')}")
    print(f"  'nonexistent_var' exists: {context.has_variable('nonexistent_var')}")

    # Clear specific scope
    context.clear_scope("request")
    print(f"\nAfter clearing request scope: {context.request_variables}")

    # Create child context
    child_context = context.create_child_context({"child_var": "child_value"})
    print(f"\nChild context request variables: {child_context.request_variables}")


if __name__ == "__main__":
    print("Running variable management examples...")
    asyncio.run(main())

    print("\n" + "=" * 50)
    demonstrate_variable_management()

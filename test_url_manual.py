#!/usr/bin/env python3
"""Manual test script for URL components."""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from python_postman.models.url import Url, QueryParam

    print("✓ Successfully imported Url and QueryParam")

    # Test 1: Basic URL creation
    print("\n--- Test 1: Basic URL Creation ---")
    url = Url(raw="https://api.example.com/users?active=true")
    print(f"Raw URL: {url.raw}")
    print(f"Protocol: {url.protocol}")
    print(f"Host: {url.host}")
    print(f"Path: {url.path}")
    print(f"Query params: {len(url.query)}")
    if url.query:
        print(f"First query param: {url.query[0].key}={url.query[0].value}")

    # Test 2: URL construction from components
    print("\n--- Test 2: URL Construction from Components ---")
    url2 = Url(
        protocol="https",
        host=["api", "example", "com"],
        path=["v1", "users", "123"],
        query=[QueryParam("format", "json"), QueryParam("include", "profile")],
    )
    constructed_url = url2.get_url_string()
    print(f"Constructed URL: {constructed_url}")

    # Test 3: Variable resolution
    print("\n--- Test 3: Variable Resolution ---")
    url3 = Url(
        protocol="https",
        host=["{{baseUrl}}"],
        path=["api", "users", ":userId"],
        query=[QueryParam("token", "{{apiKey}}")],
    )
    variables = {"baseUrl": "api.example.com", "userId": "123", "apiKey": "secret123"}
    resolved_url = url3.get_url_string(
        resolve_variables=True, variable_context=variables
    )
    print(f"URL with variables: {url3.get_url_string()}")
    print(f"Resolved URL: {resolved_url}")

    # Test 4: Query parameter manipulation
    print("\n--- Test 4: Query Parameter Manipulation ---")
    url4 = Url(protocol="https", host=["example.com"])
    url4.add_query_param("page", "1")
    url4.add_query_param("limit", "10")
    print(f"URL with added params: {url4.get_url_string()}")

    found_param = url4.get_query_param("page")
    print(f"Found param 'page': {found_param.value if found_param else 'Not found'}")

    removed = url4.remove_query_param("limit")
    print(f"Removed 'limit' param: {removed}")
    print(f"URL after removal: {url4.get_url_string()}")

    # Test 5: Path variables extraction
    print("\n--- Test 5: Path Variables Extraction ---")
    url5 = Url(path=["api", ":version", "users", "{{userId}}", "posts"])
    path_vars = url5.get_path_variables()
    print(f"Path variables found: {path_vars}")

    # Test 6: Validation
    print("\n--- Test 6: Validation ---")
    try:
        url6 = Url(host=["example.com"])
        url6.validate()
        print("✓ Valid URL passed validation")
    except ValueError as e:
        print(f"✗ Validation failed: {e}")

    try:
        url7 = Url()  # No host or raw URL
        url7.validate()
        print("✗ Invalid URL should have failed validation")
    except ValueError as e:
        print(f"✓ Invalid URL correctly failed validation: {e}")

    print("\n🎉 All URL component tests completed successfully!")

except ImportError as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)
except Exception as e:
    print(f"✗ Test failed with error: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

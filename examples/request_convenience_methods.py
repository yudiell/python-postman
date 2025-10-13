"""
Example demonstrating Request convenience methods (REQ-007).

This example shows how to use the new convenience methods added to the Request class
to easily check request characteristics and properties.
"""

from python_postman.models.request import Request
from python_postman.models.url import Url
from python_postman.models.header import Header
from python_postman.models.body import Body
from python_postman.models.auth import Auth, AuthParameter
from python_postman.models.event import Event


def main():
    print("=" * 80)
    print("Request Convenience Methods Example")
    print("=" * 80)
    print()

    # Create a POST request with various attributes
    headers = [
        Header(key="Content-Type", value="application/json"),
        Header(key="Accept", value="application/json"),
    ]
    
    body = Body(mode="raw", raw='{"username": "john", "email": "john@example.com"}')
    
    auth = Auth(
        type="bearer",
        parameters=[AuthParameter(key="token", value="{{api_token}}")]
    )
    
    events = [
        Event(
            listen="prerequest",
            script={"exec": ["console.log('Setting up request...')"]}
        ),
        Event(
            listen="test",
            script={"exec": ["pm.test('Status code is 200', () => { pm.response.to.have.status(200); })"]}
        ),
    ]
    
    request = Request(
        name="Create User",
        method="POST",
        url=Url.from_string("https://api.example.com/users"),
        headers=headers,
        body=body,
        auth=auth,
        events=events,
    )

    # Demonstrate boolean check methods
    print("Boolean Check Methods:")
    print("-" * 80)
    print(f"has_body():              {request.has_body()}")
    print(f"has_auth():              {request.has_auth()}")
    print(f"has_headers():           {request.has_headers()}")
    print(f"has_prerequest_script(): {request.has_prerequest_script()}")
    print(f"has_test_script():       {request.has_test_script()}")
    print()

    # Demonstrate query methods
    print("Query Methods:")
    print("-" * 80)
    content_type = request.get_content_type()
    print(f"get_content_type():      {content_type}")
    print()

    # Demonstrate HTTP semantics methods
    print("HTTP Semantics Methods:")
    print("-" * 80)
    print(f"is_idempotent():         {request.is_idempotent()}")
    print(f"is_cacheable():          {request.is_cacheable()}")
    print(f"is_safe():               {request.is_safe()}")
    print()

    # Compare different HTTP methods
    print("HTTP Method Comparison:")
    print("-" * 80)
    methods = ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"]
    
    print(f"{'Method':<10} {'Idempotent':<12} {'Cacheable':<12} {'Safe':<12}")
    print("-" * 80)
    
    for method in methods:
        test_request = Request(
            name=f"Test {method}",
            method=method,
            url=Url.from_string("https://api.example.com/resource")
        )
        print(
            f"{method:<10} "
            f"{str(test_request.is_idempotent()):<12} "
            f"{str(test_request.is_cacheable()):<12} "
            f"{str(test_request.is_safe()):<12}"
        )
    print()

    # Practical usage example
    print("Practical Usage Example:")
    print("-" * 80)
    
    # Check if request needs authentication
    if request.has_auth():
        print("✓ Request has authentication configured")
    
    # Check if request has a body (important for certain HTTP methods)
    if request.has_body():
        print("✓ Request has a body")
        if request.get_content_type():
            print(f"  Content-Type: {request.get_content_type()}")
    
    # Check if request has test scripts
    if request.has_test_script():
        print("✓ Request has test scripts for validation")
    
    # Check if request is safe to retry
    if request.is_idempotent():
        print("✓ Request is idempotent - safe to retry on failure")
    else:
        print("⚠ Request is NOT idempotent - be careful with retries")
    
    # Check if response can be cached
    if request.is_cacheable():
        print("✓ Response can be cached")
    else:
        print("⚠ Response should not be cached")
    
    print()

    # Example: Conditional logic based on request characteristics
    print("Conditional Logic Example:")
    print("-" * 80)
    
    def should_retry_on_failure(req: Request) -> bool:
        """Determine if a request should be retried on failure."""
        # Only retry idempotent requests
        if not req.is_idempotent():
            return False
        
        # Don't retry if there's a body (even for idempotent methods like PUT)
        # unless you're sure the operation is truly idempotent
        if req.has_body():
            return False
        
        return True
    
    get_request = Request(
        name="Get User",
        method="GET",
        url=Url.from_string("https://api.example.com/users/123")
    )
    
    post_request = Request(
        name="Create User",
        method="POST",
        url=Url.from_string("https://api.example.com/users"),
        body=Body(mode="raw", raw='{"name": "John"}')
    )
    
    print(f"GET request should retry:  {should_retry_on_failure(get_request)}")
    print(f"POST request should retry: {should_retry_on_failure(post_request)}")
    print()

    print("=" * 80)
    print("Example completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()

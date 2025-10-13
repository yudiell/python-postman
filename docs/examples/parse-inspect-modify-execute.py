"""
Parse → Inspect → Modify → Execute Workflow Example

This example demonstrates a complete workflow:
1. Parse a Postman collection
2. Inspect its structure and configuration
3. Modify requests as needed
4. Execute the modified collection

Use Case: Preparing a collection for testing in a different environment
"""

import asyncio
from python_postman import PythonPostman
from python_postman.execution import RequestExecutor, ExecutionContext
from python_postman.models import Header, Auth, AuthParameter
from python_postman.introspection import AuthResolver


async def main():
    # ========================================
    # STEP 1: PARSE
    # ========================================
    print("=" * 60)
    print("STEP 1: PARSING COLLECTION")
    print("=" * 60)
    
    parser = PythonPostman()
    collection = parser.parse("collection.json")
    
    print(f"✓ Parsed collection: {collection.info.name}")
    print(f"  Description: {collection.info.description}")
    print(f"  Schema version: {collection.schema_version}")
    print()
    
    # ========================================
    # STEP 2: INSPECT
    # ========================================
    print("=" * 60)
    print("STEP 2: INSPECTING COLLECTION")
    print("=" * 60)
    
    # Count requests and folders
    all_requests = list(collection.get_requests())
    all_folders = list(collection.get_folders())
    
    print(f"Total requests: {len(all_requests)}")
    print(f"Total folders: {len(all_folders)}")
    print()
    
    # Validate collection structure
    print("Validating collection structure...")
    validation_result = collection.validate()
    
    if validation_result.is_valid:
        print("✓ Collection is valid")
    else:
        print("✗ Collection has validation errors:")
        for error in validation_result.errors:
            print(f"  - {error}")
        return
    
    if validation_result.warnings:
        print("⚠ Warnings:")
        for warning in validation_result.warnings:
            print(f"  - {warning}")
    print()
    
    # Analyze request methods
    print("Request breakdown by method:")
    method_counts = {}
    for request in all_requests:
        method_counts[request.method] = method_counts.get(request.method, 0) + 1
    
    for method, count in sorted(method_counts.items()):
        print(f"  {method}: {count}")
    print()
    
    # Analyze authentication
    print("Authentication analysis:")
    auth_requests = 0
    no_auth_requests = 0
    
    for request in all_requests:
        resolved_auth = AuthResolver.resolve_auth(request, None, collection)
        if resolved_auth.auth:
            auth_requests += 1
            print(f"  ✓ {request.name}: {resolved_auth.auth.type} (from {resolved_auth.source.value})")
        else:
            no_auth_requests += 1
            print(f"  ✗ {request.name}: No authentication")
    
    print(f"\nSummary: {auth_requests} with auth, {no_auth_requests} without auth")
    print()
    
    # Find requests with scripts
    print("Requests with scripts:")
    prerequest_count = 0
    test_count = 0
    
    for request in all_requests:
        if request.has_prerequest_script():
            prerequest_count += 1
            print(f"  Pre-request: {request.name}")
        if request.has_test_script():
            test_count += 1
            print(f"  Test: {request.name}")
    
    print(f"\nSummary: {prerequest_count} pre-request scripts, {test_count} test scripts")
    print()
    
    # ========================================
    # STEP 3: MODIFY
    # ========================================
    print("=" * 60)
    print("STEP 3: MODIFYING COLLECTION")
    print("=" * 60)
    
    # Modification 1: Update base URL for all requests
    print("Updating base URLs from staging to production...")
    url_updates = 0
    
    for request in all_requests:
        if "staging" in request.url.host:
            old_host = request.url.host
            request.url.host = request.url.host.replace("staging", "production")
            print(f"  ✓ {request.name}: {old_host} → {request.url.host}")
            url_updates += 1
    
    print(f"Updated {url_updates} URLs")
    print()
    
    # Modification 2: Add common header to all requests
    print("Adding X-Environment header to all requests...")
    
    for request in all_requests:
        # Check if header already exists
        has_env_header = any(h.key == "X-Environment" for h in request.headers)
        if not has_env_header:
            request.headers.append(Header(
                key="X-Environment",
                value="production"
            ))
            print(f"  ✓ Added to {request.name}")
    print()
    
    # Modification 3: Add authentication to requests without it
    print("Adding API key authentication to requests without auth...")
    
    for request in all_requests:
        if not request.has_auth():
            request.auth = Auth(
                type="apikey",
                parameters=[
                    AuthParameter(key="key", value="X-API-Key"),
                    AuthParameter(key="value", value="{{api_key}}")
                ]
            )
            print(f"  ✓ Added API key auth to {request.name}")
    print()
    
    # Modification 4: Update timeout for specific requests
    print("Updating configuration for long-running requests...")
    
    long_running_keywords = ["export", "report", "batch"]
    for request in all_requests:
        if any(keyword in request.name.lower() for keyword in long_running_keywords):
            # Add custom timeout header (application-specific)
            request.headers.append(Header(
                key="X-Timeout",
                value="60000"
            ))
            print(f"  ✓ Set extended timeout for {request.name}")
    print()
    
    # Save modified collection
    print("Saving modified collection...")
    with open("modified_collection.json", "w") as f:
        f.write(collection.to_json(indent=2))
    print("✓ Saved to modified_collection.json")
    print()
    
    # ========================================
    # STEP 4: EXECUTE
    # ========================================
    print("=" * 60)
    print("STEP 4: EXECUTING MODIFIED COLLECTION")
    print("=" * 60)
    
    # Setup execution context
    context = ExecutionContext()
    context.set_variable("api_key", "your-production-api-key")
    context.set_variable("base_url", "https://api.production.example.com")
    context.set_environment_variable("environment", "production")
    
    print("Execution context configured:")
    print(f"  api_key: {context.get_variable('api_key')}")
    print(f"  base_url: {context.get_variable('base_url')}")
    print(f"  environment: {context.get_environment_variable('environment')}")
    print()
    
    # Create executor with custom configuration
    executor = RequestExecutor(
        timeout=30.0,
        follow_redirects=True,
        verify_ssl=True
    )
    
    # Execute collection
    print("Executing requests...")
    print()
    
    results = await executor.execute_collection(collection, context=context)
    
    # ========================================
    # STEP 5: ANALYZE RESULTS
    # ========================================
    print("=" * 60)
    print("STEP 5: ANALYZING RESULTS")
    print("=" * 60)
    
    # Summary statistics
    success_count = sum(1 for r in results if r.success)
    failure_count = sum(1 for r in results if not r.success)
    total_duration = sum(r.duration_ms for r in results if r.success)
    
    print(f"Execution Summary:")
    print(f"  Total requests: {len(results)}")
    print(f"  Successful: {success_count}")
    print(f"  Failed: {failure_count}")
    print(f"  Success rate: {success_count / len(results) * 100:.1f}%")
    print(f"  Total duration: {total_duration:.0f}ms")
    print(f"  Average duration: {total_duration / len(results):.0f}ms")
    print()
    
    # Detailed results
    print("Detailed Results:")
    for result in results:
        if result.success:
            status_icon = "✓"
            status_code = result.response.status_code
            duration = f"{result.duration_ms:.0f}ms"
            
            # Check test results
            test_info = ""
            if result.test_results:
                if result.test_results.all_passed:
                    test_info = f" | Tests: {result.test_results.passed}/{result.test_results.total} passed"
                else:
                    test_info = f" | Tests: {result.test_results.failed}/{result.test_results.total} failed"
            
            print(f"  {status_icon} {result.request.name}")
            print(f"     Status: {status_code} | Duration: {duration}{test_info}")
        else:
            status_icon = "✗"
            print(f"  {status_icon} {result.request.name}")
            print(f"     Error: {result.error}")
    print()
    
    # Status code distribution
    print("Status Code Distribution:")
    status_codes = {}
    for result in results:
        if result.success:
            code = result.response.status_code
            status_codes[code] = status_codes.get(code, 0) + 1
    
    for code, count in sorted(status_codes.items()):
        print(f"  {code}: {count}")
    print()
    
    # Performance analysis
    print("Performance Analysis:")
    slow_threshold = 1000  # 1 second
    slow_requests = [r for r in results if r.success and r.duration_ms > slow_threshold]
    
    if slow_requests:
        print(f"  Slow requests (>{slow_threshold}ms):")
        for result in sorted(slow_requests, key=lambda r: r.duration_ms, reverse=True):
            print(f"    {result.request.name}: {result.duration_ms:.0f}ms")
    else:
        print(f"  No slow requests (all under {slow_threshold}ms)")
    print()
    
    # Test results summary
    print("Test Results Summary:")
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for result in results:
        if result.test_results:
            total_tests += result.test_results.total
            total_passed += result.test_results.passed
            total_failed += result.test_results.failed
    
    if total_tests > 0:
        print(f"  Total tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Pass rate: {total_passed / total_tests * 100:.1f}%")
    else:
        print("  No tests executed")
    print()
    
    # Final verdict
    print("=" * 60)
    print("FINAL VERDICT")
    print("=" * 60)
    
    if failure_count == 0 and total_failed == 0:
        print("✓ ALL CHECKS PASSED")
        print("  Collection is ready for production use")
    elif failure_count > 0:
        print("✗ EXECUTION FAILURES DETECTED")
        print(f"  {failure_count} request(s) failed to execute")
    elif total_failed > 0:
        print("✗ TEST FAILURES DETECTED")
        print(f"  {total_failed} test(s) failed")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())

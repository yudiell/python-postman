#!/usr/bin/env python3
"""
Example: Using the CFTC Test Suite Programmatically

This example shows how to use the CFTC test suite components
programmatically for custom testing scenarios.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from python_postman import PythonPostman, RequestExecutor, ExecutionContext


async def example_1_load_collection():
    """Example 1: Load and inspect the CFTC collection."""
    print("\n" + "="*80)
    print("Example 1: Load and Inspect CFTC Collection")
    print("="*80)

    # Load collection
    test_data_path = Path(__file__).parent.parent / "test_data"
    collection_path = test_data_path / "cftc.gov.postman_collection.json"
    
    collection = PythonPostman.from_file(collection_path)
    
    print(f"\n✅ Collection: {collection.info.name}")
    print(f"   Schema: {collection.info.schema}")
    
    # Show variables
    print(f"\n📋 Collection Variables:")
    for var in collection.variables:
        print(f"   {var.key} = {var.value}")
    
    # Show authentication
    if collection.auth:
        print(f"\n🔐 Authentication:")
        print(f"   Type: {collection.auth.type}")
        if collection.auth.type == "apikey":
            config = collection.auth.get_api_key_config()
            print(f"   Key: {config.get('key')}")
    
    # Show requests
    print(f"\n📝 Requests:")
    for request in collection.get_requests():
        print(f"   - {request.name} ({request.method})")
        if request.url:
            print(f"     URL: {request.url.raw}")


async def example_2_variable_resolution():
    """Example 2: Demonstrate variable resolution."""
    print("\n" + "="*80)
    print("Example 2: Variable Resolution")
    print("="*80)

    # Load collection
    test_data_path = Path(__file__).parent.parent / "test_data"
    collection_path = test_data_path / "cftc.gov.postman_collection.json"
    
    collection = PythonPostman.from_file(collection_path)
    
    # Create execution context with collection variables
    collection_vars = {var.key: var.value for var in collection.variables}
    
    # Add environment variables (higher precedence)
    env_vars = {
        "datasetId": "yw9f-hn96",  # Override collection default
        "cftc-X-App-Token": "test_token_12345"
    }
    
    context = ExecutionContext(
        collection_variables=collection_vars,
        environment_variables=env_vars
    )
    
    print(f"\n🔧 Variable Resolution:")
    print(f"   baseURL: {context.get_variable('baseURL')}")
    print(f"   datasetId: {context.get_variable('datasetId')} (overridden)")
    
    # Resolve URL template
    request = collection.get_request_by_name("getApiData")
    if request and request.url:
        original_url = request.url.raw
        resolved_url = context.resolve_variables(original_url)
        
        print(f"\n🔗 URL Resolution:")
        print(f"   Original: {original_url}")
        print(f"   Resolved: {resolved_url}")


async def example_3_execute_request():
    """Example 3: Execute a request (requires API token)."""
    print("\n" + "="*80)
    print("Example 3: Execute Request (requires API token)")
    print("="*80)
    
    import os
    api_token = os.getenv("CFTC_API_TOKEN")
    
    if not api_token:
        print("\n⚠️  Skipped: CFTC_API_TOKEN not set in environment")
        print("   To run this example:")
        print("   export CFTC_API_TOKEN=your_token_here")
        return
    
    # Load collection
    test_data_path = Path(__file__).parent.parent / "test_data"
    collection_path = test_data_path / "cftc.gov.postman_collection.json"
    
    collection = PythonPostman.from_file(collection_path)
    
    # Setup execution context
    collection_vars = {var.key: var.value for var in collection.variables}
    env_vars = {
        "datasetId": "kh3c-gbw2",
        "cftc-X-App-Token": api_token
    }
    
    context = ExecutionContext(
        collection_variables=collection_vars,
        environment_variables=env_vars
    )
    context._collection = collection
    
    # Create executor
    executor = RequestExecutor(
        client_config={
            "timeout": 30.0,
            "verify": True,
            "follow_redirects": True,
        }
    )
    
    try:
        # Get request
        request = collection.get_request_by_name("getApiData")
        
        print(f"\n🚀 Executing: {request.name}")
        print(f"   Method: {request.method}")
        print(f"   URL: {context.resolve_variables(request.url.raw)}")
        
        # Execute request
        result = await executor.execute_request(request, context)
        
        if result.success:
            print(f"\n✅ Success!")
            print(f"   Status: {result.response.status_code}")
            print(f"   Time: {result.execution_time_ms:.2f}ms")
            
            # Parse response
            if result.response.json:
                data = result.response.json
                if isinstance(data, list):
                    print(f"   Records: {len(data)}")
                    if len(data) > 0:
                        print(f"\n📊 First Record:")
                        for key, value in list(data[0].items())[:3]:
                            print(f"      {key}: {value}")
        else:
            print(f"\n❌ Failed: {result.error}")
    
    finally:
        await executor.aclose()


async def example_4_multiple_datasets():
    """Example 4: Execute multiple datasets (requires API token)."""
    print("\n" + "="*80)
    print("Example 4: Execute Multiple Datasets (requires API token)")
    print("="*80)
    
    import os
    api_token = os.getenv("CFTC_API_TOKEN")
    
    if not api_token:
        print("\n⚠️  Skipped: CFTC_API_TOKEN not set in environment")
        return
    
    # Load collection
    test_data_path = Path(__file__).parent.parent / "test_data"
    collection_path = test_data_path / "cftc.gov.postman_collection.json"
    
    collection = PythonPostman.from_file(collection_path)
    request = collection.get_request_by_name("getApiData")
    
    # Create executor
    executor = RequestExecutor(
        client_config={"timeout": 30.0, "verify": True, "follow_redirects": True}
    )
    
    try:
        datasets = ["kh3c-gbw2", "yw9f-hn96"]
        
        print(f"\n🔄 Executing {len(datasets)} datasets...")
        
        for dataset_id in datasets:
            # Setup context for this dataset
            collection_vars = {var.key: var.value for var in collection.variables}
            env_vars = {
                "datasetId": dataset_id,
                "cftc-X-App-Token": api_token
            }
            
            context = ExecutionContext(
                collection_variables=collection_vars,
                environment_variables=env_vars
            )
            context._collection = collection
            
            # Execute
            result = await executor.execute_request(request, context)
            
            if result.success:
                record_count = len(result.response.json) if result.response.json else 0
                print(f"   ✅ {dataset_id}: {result.response.status_code} ({record_count} records, {result.execution_time_ms:.2f}ms)")
            else:
                print(f"   ❌ {dataset_id}: {result.error}")
            
            # Small delay between requests
            await asyncio.sleep(0.5)
    
    finally:
        await executor.aclose()


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("CFTC Collection Usage Examples")
    print("="*80)
    
    try:
        # Example 1: Load and inspect (no API token required)
        await example_1_load_collection()
        
        # Example 2: Variable resolution (no API token required)
        await example_2_variable_resolution()
        
        # Example 3: Execute request (requires API token)
        await example_3_execute_request()
        
        # Example 4: Multiple datasets (requires API token)
        await example_4_multiple_datasets()
        
        print("\n" + "="*80)
        print("✅ Examples completed!")
        print("="*80)
        print("\nTo run examples 3 and 4, set CFTC_API_TOKEN:")
        print("  export CFTC_API_TOKEN=your_token_here")
        print("="*80 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

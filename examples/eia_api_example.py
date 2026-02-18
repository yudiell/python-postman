#!/usr/bin/env python3
"""
Real-World Example: EIA APIv2 Collection

This example demonstrates python-postman features using the U.S. Energy
Information Administration (EIA) APIv2 Postman collection — a real-world
collection with 278 requests across 226 folders covering energy data
endpoints (electricity, coal, natural gas, petroleum, etc.).

What this example shows:
1. Loading and inspecting a large real-world collection
2. Navigating deeply nested folder hierarchies (up to 6 levels)
3. Using search and filtering to find specific requests
4. Analyzing collection structure with statistics
5. Resolving inherited authentication across the collection
6. Tracing variables across scopes
7. Setting up execution context for API calls
"""

from python_postman import PythonPostman
from python_postman.models.folder import Folder
from python_postman.introspection import AuthResolver, VariableTracer


def main():
    # ---------------------------------------------------------------
    # 1. Load the collection
    # ---------------------------------------------------------------
    collection = PythonPostman.from_file(
        "tests/test_data/real_world/EIA_APIv2.postman_collection.json"
    )

    print(f"Collection: {collection.info.name}")
    print(f"Description: {collection.info.description[:120]}...")
    print()

    # ---------------------------------------------------------------
    # 2. High-level statistics
    # ---------------------------------------------------------------
    stats = collection.get_statistics()
    data = stats.collect()

    print("=== Collection Statistics ===")
    print(f"  Total requests:         {data['total_requests']}")
    print(f"  Total folders:          {data['total_folders']}")
    print(f"  Max nesting depth:      {data['max_nesting_depth']}")
    print(f"  Avg requests/folder:    {data['avg_requests_per_folder']:.2f}")
    print()

    print("  Requests by method:")
    for method, count in sorted(data["requests_by_method"].items()):
        print(f"    {method}: {count}")
    print()

    print("  Requests by auth type:")
    for auth_type, count in sorted(data["requests_by_auth"].items()):
        print(f"    {auth_type}: {count}")
    print()

    # ---------------------------------------------------------------
    # 3. Navigate the folder hierarchy
    # ---------------------------------------------------------------
    print("=== Top-Level Folder Structure ===")

    # The collection has a single top-level "v2" folder containing
    # domain-specific subfolders (electricity, coal, natural-gas, etc.)
    all_folders = list(collection.get_folders())
    top_level_folders = [
        item for item in collection.items if isinstance(item, Folder)
    ]

    print(f"  Total folders (recursive): {len(all_folders)}")
    print(f"  Top-level folders: {len(top_level_folders)}")
    print()

    # Show the second level — the actual energy domain folders
    for top_folder in top_level_folders:
        print(f"  [{top_folder.name}]")
        for sub in top_folder.get_subfolders():
            sub_reqs = len(list(sub.get_requests()))
            sub_folders = len(sub.get_subfolders())
            print(f"    {sub.name:45s} ({sub_reqs} reqs, {sub_folders} subfolders)")
    print()

    # ---------------------------------------------------------------
    # 4. Search for specific requests
    # ---------------------------------------------------------------
    print("=== Search Examples ===")

    # Find all POST requests (data submission endpoints)
    post_requests = collection.search().by_method("POST").execute()
    print(f"  POST requests: {len(post_requests)}")
    for result in post_requests[:3]:
        print(f"    - {result.request.name}")
    if len(post_requests) > 3:
        print(f"    ... and {len(post_requests) - 3} more")
    print()

    # Find requests related to electricity
    electricity_requests = (
        collection.search().in_folder("electricity").execute()
    )
    print(f"  Requests in 'electricity' folders: {len(electricity_requests)}")

    # Find requests with URL patterns
    coal_data_requests = (
        collection.search()
        .by_url_pattern("coal")
        .by_method("GET")
        .execute()
    )
    print(f"  GET requests with 'coal' in URL: {len(coal_data_requests)}")

    # Note: by_auth_type filters by request-level auth only.
    # In this collection, auth is set at the collection level and inherited,
    # so individual requests don't have auth set directly.
    # The statistics above show all 278 requests resolve to apikey auth
    # via inheritance.
    print()

    # ---------------------------------------------------------------
    # 5. Inspect authentication
    # ---------------------------------------------------------------
    print("=== Authentication Analysis ===")

    # Collection-level auth applies to all requests
    auth = collection.auth
    print(f"  Collection auth type: {auth.type}")
    for param in auth.parameters:
        print(f"    {param.key} = {param.value}")
    print()

    # Use AuthResolver to see how auth is inherited
    # AuthResolver.resolve_auth is a static method that walks the hierarchy
    sample_request = list(collection.get_requests())[0]
    resolved = AuthResolver.resolve_auth(
        sample_request, collection=collection
    )
    print(f"  Resolved auth for '{sample_request.name}':")
    print(f"    Type: {resolved.auth.type if resolved.auth else None}")
    print(f"    Source: {resolved.source.value}")
    print(f"    Path: {' > '.join(resolved.path)}")
    print()

    # ---------------------------------------------------------------
    # 6. Variable tracing
    # ---------------------------------------------------------------
    print("=== Variable Analysis ===")

    # Collection variables
    variables = collection.get_variables()
    print(f"  Collection variables: {variables}")

    # Trace where baseUrl is used
    tracer = VariableTracer(collection)
    usage = tracer.find_variable_usage("baseUrl")
    print(f"  'baseUrl' is used in {len(usage)} locations")
    for loc in usage[:5]:
        print(f"    - {loc}")
    if len(usage) > 5:
        print(f"    ... and {len(usage) - 5} more")
    print()

    # Find undefined variable references
    undefined = tracer.find_undefined_references()
    if undefined:
        print(f"  Undefined variables referenced: {undefined}")
    else:
        print("  No undefined variable references found")
    print()

    # ---------------------------------------------------------------
    # 7. Inspect individual requests
    # ---------------------------------------------------------------
    print("=== Request Details ===")

    # Look at a specific electricity data request
    electricity_folder = collection.get_folder_by_name("retail-sales")
    if electricity_folder:
        print(f"  Folder: {electricity_folder.name}")
        for req in electricity_folder.get_requests():
            print(f"    {req.method} {req.name}")
            print(f"      URL: {req.url.raw}")

            # Show query parameters if present
            if req.url.query:
                params = [
                    q.key for q in req.url.query if not q.disabled
                ]
                if params:
                    print(f"      Query params: {', '.join(params)}")

            # Show body for POST requests
            if req.body and req.body.raw:
                preview = req.body.raw[:100].replace("\n", " ")
                print(f"      Body: {preview}...")

            # Show headers
            if req.headers:
                for h in req.headers:
                    print(f"      Header: {h.key}: {h.value}")
            print()

    # ---------------------------------------------------------------
    # 8. Execution setup (requires httpx)
    # ---------------------------------------------------------------
    print("=== Execution Setup ===")
    print("  To execute requests against the live EIA API:")
    print()
    print("  from python_postman.execution import RequestExecutor, ExecutionContext")
    print()
    print("  executor = collection.create_executor(")
    print("      client_config={'timeout': 30.0},")
    print("  )")
    print()
    print("  context = ExecutionContext(")
    print("      environment_variables={")
    print('          "apiKey": "YOUR_EIA_API_KEY",')
    print('          "baseUrl": "https://api.eia.gov",')
    print('          "route1": "2024",')
    print("      }")
    print("  )")
    print()
    print("  request = collection.get_request_by_name('/v2/aeo')")
    print("  result = await executor.execute_request(request, context)")
    print()
    print("  Register for a free API key at: https://www.eia.gov/opendata/")


if __name__ == "__main__":
    main()

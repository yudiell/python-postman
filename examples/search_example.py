"""
Example demonstrating the search and filtering functionality.

This example shows how to use the RequestQuery builder to search
and filter requests in a Postman collection.
"""

from python_postman import PythonPostman

# Load a collection
collection = PythonPostman.from_file("tests/test_data/nested_collection.json")

print(f"Collection: {collection.info.name}")
print(f"Total requests: {len(list(collection.get_requests()))}\n")

# Example 1: Find all GET requests
print("=" * 60)
print("Example 1: Find all GET requests")
print("=" * 60)
results = collection.search().by_method("GET").execute()
print(f"Found {len(results)} GET requests:")
for result in results:
    print(f"  - {result.full_path}")
print()

# Example 2: Find requests by URL pattern
print("=" * 60)
print("Example 2: Find requests with '/users' in the URL")
print("=" * 60)
results = collection.search().by_url_pattern(r"/users").execute()
print(f"Found {len(results)} requests:")
for result in results:
    print(f"  - {result.request.name}: {result.request.url.to_string()}")
print()

# Example 3: Find requests with authentication
print("=" * 60)
print("Example 3: Find requests with bearer authentication")
print("=" * 60)
results = collection.search().by_auth_type("bearer").execute()
print(f"Found {len(results)} requests with bearer auth:")
for result in results:
    print(f"  - {result.full_path}")
print()

# Example 4: Find requests with test scripts
print("=" * 60)
print("Example 4: Find requests with test scripts")
print("=" * 60)
results = collection.search().has_scripts("test").execute()
print(f"Found {len(results)} requests with test scripts:")
for result in results:
    print(f"  - {result.full_path}")
print()

# Example 5: Complex query with multiple filters
print("=" * 60)
print("Example 5: Complex query - GET requests with test scripts")
print("=" * 60)
results = (
    collection.search()
    .by_method("GET")
    .has_scripts("test")
    .execute()
)
print(f"Found {len(results)} matching requests:")
for result in results:
    print(f"  - {result.full_path}")
    print(f"    URL: {result.request.url.to_string()}")
print()

# Example 6: Using iterator for large result sets
print("=" * 60)
print("Example 6: Using iterator (memory efficient)")
print("=" * 60)
print("Processing all requests:")
for result in collection.search().execute_iter():
    print(f"  - Processing: {result.request.name}")
print()

# Example 7: Find requests in a specific folder
print("=" * 60)
print("Example 7: Find requests in a specific folder")
print("=" * 60)
# Note: This will only work if your collection has folders
results = collection.search().in_folder("Users").execute()
if results:
    print(f"Found {len(results)} requests in 'Users' folder:")
    for result in results:
        print(f"  - {result.request.name}")
else:
    print("No 'Users' folder found in this collection")
print()

# Example 8: Find requests by host
print("=" * 60)
print("Example 8: Find requests by host")
print("=" * 60)
# Get all unique hosts first
all_requests = list(collection.get_requests())
hosts = set()
for req in all_requests:
    if req.url.host:
        hosts.add(".".join(req.url.host))

if hosts:
    first_host = list(hosts)[0]
    results = collection.search().by_host(first_host).execute()
    print(f"Found {len(results)} requests to {first_host}:")
    for result in results:
        print(f"  - {result.request.name}")
else:
    print("No hosts found in collection")

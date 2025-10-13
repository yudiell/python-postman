"""
Example demonstrating collection statistics functionality.

This example shows how to:
1. Parse a Postman collection
2. Generate statistics about the collection
3. Export statistics to JSON and CSV formats
"""

from python_postman import PythonPostman


def main():
    # Parse a collection
    collection = PythonPostman.from_file("tests/test_data/nested_collection.json")
    
    print(f"Collection: {collection.info.name}")
    print("=" * 60)
    
    # Get statistics
    stats = collection.get_statistics()
    
    # Collect all statistics
    data = stats.collect()
    
    # Display summary statistics
    print("\n📊 Summary Statistics:")
    print(f"  Total Requests: {data['total_requests']}")
    print(f"  Total Folders: {data['total_folders']}")
    print(f"  Max Nesting Depth: {data['max_nesting_depth']}")
    print(f"  Avg Requests per Folder: {data['avg_requests_per_folder']:.2f}")
    
    # Display requests by HTTP method
    print("\n🔧 Requests by HTTP Method:")
    for method, count in sorted(data['requests_by_method'].items()):
        print(f"  {method}: {count}")
    
    # Display requests by authentication type
    print("\n🔐 Requests by Authentication Type:")
    for auth_type, count in sorted(data['requests_by_auth'].items()):
        print(f"  {auth_type}: {count}")
    
    # Export to JSON
    print("\n📄 Exporting to JSON...")
    json_output = stats.to_json()
    with open("collection_stats.json", "w") as f:
        f.write(json_output)
    print("  ✓ Saved to collection_stats.json")
    
    # Export to CSV
    print("\n📊 Exporting to CSV...")
    csv_output = stats.to_csv()
    with open("collection_stats.csv", "w") as f:
        f.write(csv_output)
    print("  ✓ Saved to collection_stats.csv")
    
    # Individual statistics methods
    print("\n🔍 Individual Statistics Methods:")
    print(f"  count_requests(): {stats.count_requests()}")
    print(f"  count_folders(): {stats.count_folders()}")
    print(f"  get_max_depth(): {stats.get_max_depth()}")
    
    # Method breakdown
    by_method = stats.count_by_method()
    print(f"\n  HTTP Methods breakdown:")
    for method, count in by_method.items():
        print(f"    {method}: {count}")
    
    # Auth breakdown
    by_auth = stats.count_by_auth()
    print(f"\n  Authentication breakdown:")
    for auth_type, count in by_auth.items():
        print(f"    {auth_type}: {count}")
    
    # Cache demonstration
    print("\n💾 Cache Demonstration:")
    print("  First call (calculates)...")
    data1 = stats.collect(use_cache=True)
    print("  Second call (uses cache)...")
    data2 = stats.collect(use_cache=True)
    print(f"  Same object reference: {data1 is data2}")
    
    print("\n  Clearing cache...")
    stats.clear_cache()
    print("  Third call (recalculates)...")
    data3 = stats.collect(use_cache=True)
    print(f"  Different object reference: {data1 is data3}")
    print(f"  But same values: {data1 == data3}")


if __name__ == "__main__":
    main()

"""REST API Testing Example

Demonstrates testing a REST API with CRUD operations.
"""

import argparse
from postman_collection_runner import PostmanCollectionRunner

def main():
    parser = argparse.ArgumentParser(description="Run REST API tests")
    parser.add_argument("--environment", default="dev", choices=["dev", "prod"],
                       help="Environment to test against")
    args = parser.parse_args()
    
    # Initialize runner
    runner = PostmanCollectionRunner()
    
    # Load collection and environment
    collection = runner.load_collection("collections/rest-api.json")
    environment = runner.load_environment(f"environments/{args.environment}.json")
    
    print(f"Testing against {args.environment} environment")
    print("="*60)
    
    # Execute collection
    results = runner.execute(collection, environment=environment)
    
    # Print detailed results
    for result in results.request_results:
        status = "✓" if result.success else "✗"
        print(f"{status} {result.request_name}")
        
        if result.success:
            print(f"  Status: {result.response.status_code}")
            print(f"  Time: {result.response.elapsed.total_seconds():.2f}s")
        else:
            print(f"  Error: {result.error}")
        print()
    
    # Summary
    print("="*60)
    print(f"Results: {results.successful_requests}/{results.total_requests} passed")
    print(f"Success rate: {results.success_rate:.1f}%")
    
    return 0 if results.failed_requests == 0 else 1

if __name__ == "__main__":
    exit(main())

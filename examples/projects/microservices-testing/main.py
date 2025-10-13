"""Microservices Testing Example

Demonstrates testing multiple microservices with shared state.
"""

from postman_collection_runner import PostmanCollectionRunner

def main():
    runner = PostmanCollectionRunner()
    
    # Load environment
    environment = runner.load_environment("environments/microservices.json")
    
    # Shared variables across services
    shared_vars = {}
    
    print("Testing Microservices Architecture")
    print("="*60)
    
    # 1. Test Auth Service
    print("\n1. Testing Auth Service...")
    auth_collection = runner.load_collection("collections/auth-service.json")
    auth_results = runner.execute(auth_collection, environment=environment)
    
    if auth_results.failed_requests > 0:
        print("❌ Auth service failed, stopping tests")
        return 1
    
    print("✓ Auth service passed")
    # Extract token for subsequent services
    shared_vars["authToken"] = "sample-token-123"
    
    # 2. Test User Service
    print("\n2. Testing User Service...")
    user_collection = runner.load_collection("collections/user-service.json")
    user_results = runner.execute(user_collection, environment=environment, 
                                  variables=shared_vars)
    
    if user_results.failed_requests > 0:
        print("❌ User service failed, stopping tests")
        return 1
    
    print("✓ User service passed")
    shared_vars["userId"] = "user-123"
    
    # 3. Test Order Service
    print("\n3. Testing Order Service...")
    order_collection = runner.load_collection("collections/order-service.json")
    order_results = runner.execute(order_collection, environment=environment,
                                   variables=shared_vars)
    
    if order_results.failed_requests > 0:
        print("❌ Order service failed")
        return 1
    
    print("✓ Order service passed")
    
    # Summary
    total_requests = (auth_results.total_requests + 
                     user_results.total_requests + 
                     order_results.total_requests)
    total_failed = (auth_results.failed_requests + 
                   user_results.failed_requests + 
                   order_results.failed_requests)
    
    print("\n" + "="*60)
    print(f"Overall Results: {total_requests - total_failed}/{total_requests} passed")
    print("✓ All microservices integration tests passed!")
    
    return 0

if __name__ == "__main__":
    exit(main())

#!/usr/bin/env python3
"""
Complete Workflow Example

This example demonstrates a complete end-to-end workflow using
python-postman for API testing and automation.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, Any, List

from python_postman import PythonPostman
from python_postman.execution import (
    RequestExecutor,
    ExecutionContext,
    RequestExtensions,
    ExecutionResult,
    CollectionExecutionResult,
)


class APIWorkflow:
    """Complete API workflow demonstrating all major features."""

    def __init__(self):
        self.collection = None
        self.executor = None
        self.results = {}
        self.session_data = {}

    async def setup(self):
        """Initialize the workflow."""
        print("🚀 Setting up API workflow...")

        # Create a sample collection programmatically for demo
        self.collection = self._create_sample_collection()

        # Initialize executor with comprehensive configuration
        self.executor = RequestExecutor(
            client_config={
                "timeout": 30.0,
                "verify": True,
                "follow_redirects": True,
                "limits": {"max_connections": 10, "max_keepalive_connections": 5},
            },
            global_headers={
                "User-Agent": "python-postman-workflow/1.0",
                "Accept": "application/json",
                "X-Client-Version": "1.0.0",
            },
            request_delay=0.1,  # 100ms delay between requests
        )

        print("✅ Workflow setup complete")

    def _create_sample_collection(self):
        """Create a sample collection for demonstration."""
        collection_data = {
            "info": {
                "name": "Complete API Workflow",
                "description": "Demonstrates all python-postman execution features",
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "variable": [
                {"key": "base_url", "value": "https://jsonplaceholder.typicode.com"},
                {"key": "api_version", "value": "v1"},
                {"key": "timeout", "value": "30"},
            ],
            "auth": {
                "type": "bearer",
                "bearer": [
                    {"key": "token", "value": "{{auth_token}}", "type": "string"}
                ],
            },
            "item": [
                {
                    "name": "Health Check",
                    "request": {
                        "method": "GET",
                        "url": "{{base_url}}/posts/1",
                        "header": [{"key": "Accept", "value": "application/json"}],
                    },
                    "event": [
                        {
                            "listen": "test",
                            "script": {
                                "exec": [
                                    "pm.test('Status code is 200', function () {",
                                    "    pm.response.to.have.status(200);",
                                    "});",
                                    "",
                                    "pm.test('Response has required fields', function () {",
                                    "    const jsonData = pm.response.json();",
                                    "    pm.expect(jsonData).to.have.property('id');",
                                    "    pm.expect(jsonData).to.have.property('title');",
                                    "});",
                                ]
                            },
                        }
                    ],
                },
                {
                    "name": "Get All Posts",
                    "request": {
                        "method": "GET",
                        "url": "{{base_url}}/posts",
                        "header": [{"key": "Accept", "value": "application/json"}],
                    },
                },
                {
                    "name": "Create Post",
                    "request": {
                        "method": "POST",
                        "url": "{{base_url}}/posts",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps(
                                {
                                    "title": "{{post_title}}",
                                    "body": "{{post_body}}",
                                    "userId": "{{user_id}}",
                                }
                            ),
                        },
                    },
                },
                {
                    "name": "Update Post",
                    "request": {
                        "method": "PUT",
                        "url": "{{base_url}}/posts/{{post_id}}",
                        "header": [
                            {"key": "Content-Type", "value": "application/json"}
                        ],
                        "body": {
                            "mode": "raw",
                            "raw": json.dumps(
                                {
                                    "id": "{{post_id}}",
                                    "title": "{{updated_title}}",
                                    "body": "{{updated_body}}",
                                    "userId": "{{user_id}}",
                                }
                            ),
                        },
                    },
                },
                {
                    "name": "Delete Post",
                    "request": {
                        "method": "DELETE",
                        "url": "{{base_url}}/posts/{{post_id}}",
                    },
                },
            ],
        }

        return PythonPostman.from_dict(collection_data)

    async def run_health_check(self) -> bool:
        """Run health check to verify API availability."""
        print("\n🏥 Running health check...")

        context = ExecutionContext(
            environment_variables={"base_url": "https://jsonplaceholder.typicode.com"}
        )

        health_request = self.collection.get_request_by_name("Health Check")
        result = await self.executor.execute_request(health_request, context)

        if result.success and result.response.is_success():
            print("✅ Health check passed")

            # Show test results
            if result.test_results:
                print(
                    f"  🧪 Tests: {result.test_results.passed} passed, {result.test_results.failed} failed"
                )

            return True
        else:
            print(f"❌ Health check failed: {result.error}")
            return False

    async def demonstrate_crud_operations(self):
        """Demonstrate CRUD operations with variable management."""
        print("\n📝 Demonstrating CRUD operations...")

        # Base context with common variables
        context = ExecutionContext(
            environment_variables={
                "base_url": "https://jsonplaceholder.typicode.com",
                "auth_token": "demo-token-12345",
            },
            collection_variables={
                "user_id": "1",
                "post_title": "My Test Post",
                "post_body": "This is a test post created by python-postman",
            },
        )

        # Step 1: Create a post
        print("  📄 Creating new post...")
        create_request = self.collection.get_request_by_name("Create Post")

        create_result = await self.executor.execute_request(create_request, context)

        if create_result.success:
            created_post = create_result.response.json
            post_id = created_post.get(
                "id", "101"
            )  # JSONPlaceholder returns 101 for new posts
            print(f"  ✅ Post created with ID: {post_id}")

            # Store post ID for subsequent operations
            context.set_variable("post_id", str(post_id), "environment")
        else:
            print(f"  ❌ Failed to create post: {create_result.error}")
            return

        # Step 2: Update the post
        print("  ✏️  Updating post...")
        update_request = self.collection.get_request_by_name("Update Post")

        # Use request extensions to modify the update
        extensions = RequestExtensions(
            body_extensions={
                "updated_title": "Updated Test Post",
                "updated_body": "This post has been updated via python-postman",
                "metadata": {
                    "updated_at": str(int(time.time())),
                    "updated_by": "python-postman",
                },
            }
        )

        update_result = await self.executor.execute_request(
            update_request, context, extensions=extensions
        )

        if update_result.success:
            print("  ✅ Post updated successfully")
        else:
            print(f"  ❌ Failed to update post: {update_result.error}")

        # Step 3: Delete the post
        print("  🗑️  Deleting post...")
        delete_request = self.collection.get_request_by_name("Delete Post")

        delete_result = await self.executor.execute_request(delete_request, context)

        if delete_result.success:
            print("  ✅ Post deleted successfully")
        else:
            print(f"  ❌ Failed to delete post: {delete_result.error}")

        # Store CRUD results
        self.results["crud_operations"] = {
            "create": create_result.success,
            "update": update_result.success,
            "delete": delete_result.success,
        }

    async def run_performance_test(self):
        """Run performance tests with parallel execution."""
        print("\n⚡ Running performance tests...")

        context = ExecutionContext(
            environment_variables={"base_url": "https://jsonplaceholder.typicode.com"}
        )

        # Test 1: Sequential execution
        print("  📊 Sequential execution test...")
        start_time = time.time()

        sequential_result = await self.executor.execute_collection(
            self.collection, parallel=False
        )

        sequential_time = time.time() - start_time

        print(f"    ⏱️  Sequential: {sequential_time:.2f}s")
        print(
            f"    📈 Results: {sequential_result.successful_requests}/{sequential_result.total_requests} successful"
        )

        # Test 2: Parallel execution
        print("  🚀 Parallel execution test...")
        start_time = time.time()

        parallel_result = await self.executor.execute_collection(
            self.collection, parallel=True
        )

        parallel_time = time.time() - start_time

        print(f"    ⏱️  Parallel: {parallel_time:.2f}s")
        print(
            f"    📈 Results: {parallel_result.successful_requests}/{parallel_result.total_requests} successful"
        )

        # Calculate performance improvement
        if sequential_time > 0:
            speedup = sequential_time / parallel_time
            print(f"    🏆 Speedup: {speedup:.2f}x")

        # Store performance results
        self.results["performance"] = {
            "sequential_time": sequential_time,
            "parallel_time": parallel_time,
            "speedup": speedup if sequential_time > 0 else 0,
            "sequential_success_rate": sequential_result.successful_requests
            / sequential_result.total_requests,
            "parallel_success_rate": parallel_result.successful_requests
            / parallel_result.total_requests,
        }

    async def demonstrate_error_handling(self):
        """Demonstrate comprehensive error handling."""
        print("\n🛡️  Demonstrating error handling...")

        # Test 1: Missing variable error
        print("  🔧 Testing variable resolution error...")
        try:
            bad_context = ExecutionContext()  # No variables defined
            request = self.collection.get_request_by_name("Health Check")
            result = await self.executor.execute_request(request, bad_context)
        except Exception as e:
            print(f"    ✅ Caught expected error: {type(e).__name__}")

        # Test 2: Invalid URL error
        print("  🌐 Testing invalid URL error...")
        context = ExecutionContext(
            environment_variables={
                "base_url": "https://invalid-domain-that-does-not-exist.com"
            }
        )

        request = self.collection.get_request_by_name("Health Check")
        result = await self.executor.execute_request(request, context)

        if not result.success:
            print(f"    ✅ Handled network error: {type(result.error).__name__}")

        # Test 3: Collection execution with stop_on_error
        print("  🛑 Testing stop on error behavior...")

        # This will likely fail due to invalid domain, testing stop behavior
        error_result = await self.executor.execute_collection(
            self.collection, stop_on_error=True
        )

        print(f"    📊 Stopped after {len(error_result.results)} requests")

    async def generate_report(self):
        """Generate a comprehensive execution report."""
        print("\n📊 Generating execution report...")

        report = {
            "workflow_summary": {
                "collection_name": self.collection.info.name,
                "total_requests": len(list(self.collection.get_all_requests())),
                "execution_timestamp": time.time(),
            },
            "results": self.results,
        }

        # Save report to file
        report_path = Path("workflow_report.json")
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"  📄 Report saved to: {report_path}")

        # Print summary
        print("\n📋 Workflow Summary:")
        print(f"  Collection: {report['workflow_summary']['collection_name']}")
        print(f"  Total requests: {report['workflow_summary']['total_requests']}")

        if "crud_operations" in self.results:
            crud = self.results["crud_operations"]
            print(f"  CRUD operations: {sum(crud.values())}/{len(crud)} successful")

        if "performance" in self.results:
            perf = self.results["performance"]
            print(
                f"  Performance improvement: {perf.get('speedup', 0):.2f}x with parallel execution"
            )

    async def cleanup(self):
        """Clean up resources."""
        print("\n🧹 Cleaning up...")

        if self.executor:
            await self.executor.aclose()

        print("✅ Cleanup complete")


async def main():
    """Run the complete workflow demonstration."""
    print("🎯 Python Postman Complete Workflow Demo")
    print("=" * 50)

    workflow = APIWorkflow()

    try:
        # Setup
        await workflow.setup()

        # Run health check
        if await workflow.run_health_check():
            # Run main workflow steps
            await workflow.demonstrate_crud_operations()
            await workflow.run_performance_test()
            await workflow.demonstrate_error_handling()

            # Generate report
            await workflow.generate_report()
        else:
            print("❌ Health check failed, skipping main workflow")

    except Exception as e:
        print(f"❌ Workflow error: {e}")

    finally:
        # Always cleanup
        await workflow.cleanup()

    print("\n🎉 Complete workflow demonstration finished!")


if __name__ == "__main__":
    asyncio.run(main())

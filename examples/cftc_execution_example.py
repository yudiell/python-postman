"""
Example: CFTC API Execution

This example demonstrates how to use the CFTCExecutor to execute requests
from the cftc.gov Postman collection with real API endpoints.

Features demonstrated:
- Loading and validating collections
- Variable resolution with different scopes
- Executing single requests with parameters
- Executing multiple datasets
- Generating execution reports
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.execution_tests.cftc_execution import CFTCExecutor
from tests.execution_tests.execution_config import ConfigManager


async def example_load_and_inspect():
    """Example: Load collection and inspect its structure."""
    print("\n" + "="*80)
    print("EXAMPLE 1: Load and Inspect Collection")
    print("="*80)

    # Create executor with test configuration
    config = {
        "cftc_api_token": "your_token_here",  # Replace with actual token for real execution
        "cftc_base_url": "https://publicreporting.cftc.gov/resource",
        "request_timeout": 30.0,
        "request_delay": 0.1,
        "verify_ssl": True,
        "output_format": "console",
        "output_path": "./execution_results",
        "verbose": True,
    }

    async with CFTCExecutor(config=config) as executor:
        # Load the collection
        collection = executor.load_collection()

        print(f"\n✅ Successfully loaded collection with {len(list(collection.get_requests()))} request(s)")


async def example_variable_resolution():
    """Example: Demonstrate variable resolution."""
    print("\n" + "="*80)
    print("EXAMPLE 2: Variable Resolution")
    print("="*80)

    config = {
        "cftc_api_token": "your_token_here",
        "cftc_base_url": "https://publicreporting.cftc.gov/resource",
        "request_timeout": 30.0,
        "request_delay": 0.1,
        "verify_ssl": True,
        "output_format": "console",
        "output_path": "./execution_results",
        "verbose": True,
    }

    async with CFTCExecutor(config=config) as executor:
        executor.load_collection()

        # Demonstrate variable resolution
        await executor.demonstrate_variable_resolution()


async def example_execution_context():
    """Example: Working with execution contexts."""
    print("\n" + "="*80)
    print("EXAMPLE 3: Execution Context Management")
    print("="*80)

    config = {
        "cftc_api_token": "your_token_here",
        "cftc_base_url": "https://publicreporting.cftc.gov/resource",
        "request_timeout": 30.0,
        "request_delay": 0.1,
        "verify_ssl": True,
        "output_format": "console",
        "output_path": "./execution_results",
        "verbose": True,
    }

    async with CFTCExecutor(config=config) as executor:
        executor.load_collection()

        # Create context with default dataset
        context1 = executor.setup_execution_context()
        print(f"\nDefault context:")
        print(f"  baseURL: {context1.get_variable('baseURL')}")
        print(f"  datasetId: {context1.get_variable('datasetId')}")

        # Create context with custom dataset
        context2 = executor.setup_execution_context(dataset_id="yw9f-hn96")
        print(f"\nCustom context:")
        print(f"  baseURL: {context2.get_variable('baseURL')}")
        print(f"  datasetId: {context2.get_variable('datasetId')}")

        # Create context with additional variables
        context3 = executor.setup_execution_context(
            dataset_id="kh3c-gbw2",
            additional_variables={"custom_var": "custom_value"}
        )
        print(f"\nContext with additional variables:")
        print(f"  datasetId: {context3.get_variable('datasetId')}")
        print(f"  custom_var: {context3.get_variable('custom_var')}")


async def example_single_request_execution():
    """Example: Execute a single request (requires valid API token)."""
    print("\n" + "="*80)
    print("EXAMPLE 4: Single Request Execution")
    print("="*80)
    print("\n⚠️  This example requires a valid CFTC API token to execute.")
    print("To run this example:")
    print("1. Get an API token from https://data.cftc.gov/")
    print("2. Set CFTC_API_TOKEN in your .env file")
    print("3. Uncomment the execution code below\n")

    # Uncomment the following code to execute with a real API token:
    """
    try:
        # Load configuration from .env file
        config = ConfigManager.load_from_env()

        async with CFTCExecutor(config=config) as executor:
            executor.load_collection()

            # Execute single request
            result = await executor.execute_single_request(
                dataset_id="kh3c-gbw2",
                limit=5
            )

            if result.success:
                print(f"\n✅ Request executed successfully!")
            else:
                print(f"\n❌ Request failed: {result.error}")

    except ImportError as e:
        print(f"\n⚠️  {e}")
        print("Install python-dotenv: pip install python-dotenv")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    """


async def example_multiple_datasets():
    """Example: Execute multiple datasets (requires valid API token)."""
    print("\n" + "="*80)
    print("EXAMPLE 5: Multiple Dataset Execution")
    print("="*80)
    print("\n⚠️  This example requires a valid CFTC API token to execute.")
    print("To run this example:")
    print("1. Get an API token from https://data.cftc.gov/")
    print("2. Set CFTC_API_TOKEN in your .env file")
    print("3. Uncomment the execution code below\n")

    # Uncomment the following code to execute with a real API token:
    """
    try:
        # Load configuration from .env file
        config = ConfigManager.load_from_env()

        async with CFTCExecutor(config=config) as executor:
            executor.load_collection()

            # Execute multiple datasets
            datasets = ["kh3c-gbw2", "yw9f-hn96"]
            results = await executor.execute_multiple_datasets(
                datasets=datasets,
                limit=5
            )

            # Generate comparison report
            print("\n" + "="*80)
            print("Execution Report")
            print("="*80)
            report = executor.generate_execution_report(results)
            print(report)

    except ImportError as e:
        print(f"\n⚠️  {e}")
        print("Install python-dotenv: pip install python-dotenv")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    """


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("CFTC Execution Examples")
    print("="*80)
    print("\nThese examples demonstrate the CFTCExecutor functionality.")
    print("Some examples require a valid CFTC API token to execute real requests.\n")

    try:
        # Example 1: Load and inspect
        await example_load_and_inspect()

        # Example 2: Variable resolution
        await example_variable_resolution()

        # Example 3: Execution context
        await example_execution_context()

        # Example 4: Single request (requires API token)
        await example_single_request_execution()

        # Example 5: Multiple datasets (requires API token)
        await example_multiple_datasets()

        print("\n" + "="*80)
        print("✅ Examples completed!")
        print("="*80)
        print("\nTo execute real API requests:")
        print("1. Get an API token from https://data.cftc.gov/")
        print("2. Copy .env.example to .env")
        print("3. Set CFTC_API_TOKEN in .env")
        print("4. Uncomment the execution code in examples 4 and 5")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

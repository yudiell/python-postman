"""
Multi-collection execution example.

This example demonstrates how to use the MultiCollectionRunner to execute
multiple Postman collections and compare execution modes.
"""

import asyncio
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.execution_tests.multi_collection_runner import MultiCollectionRunner
from tests.execution_tests.execution_config import ConfigManager, CollectionConfig


async def example_run_single_collection():
    """Example: Run a single collection."""
    print("\n" + "="*80)
    print("Example 1: Run Single Collection")
    print("="*80)

    # Get test data path
    test_data_path = Path(__file__).parent.parent / "tests" / "test_data"
    collection_path = test_data_path / "execution_collection.json"

    # Create runner
    async with MultiCollectionRunner() as runner:
        # Run the collection
        result = await runner.run_collection(
            collection_path=collection_path,
            context_variables={},
            parallel=False,
            stop_on_error=False,
        )

        print(f"\n✅ Collection execution completed!")
        print(f"   Total requests: {result.total_requests}")
        print(f"   Success rate: {result.success_rate * 100:.1f}%")


async def example_run_multiple_collections():
    """Example: Run multiple collections."""
    print("\n" + "="*80)
    print("Example 2: Run Multiple Collections")
    print("="*80)

    # Get test data path
    test_data_path = Path(__file__).parent.parent / "tests" / "test_data"

    # Define collections to execute
    collection_configs = [
        CollectionConfig(
            name="Execution Collection",
            path=test_data_path / "execution_collection.json",
            variables={},
            auth_required=False,
            timeout=30.0,
        ),
        CollectionConfig(
            name="Auth Execution Collection",
            path=test_data_path / "auth_execution_collection.json",
            variables={},
            auth_required=True,
            timeout=30.0,
        ),
    ]

    # Filter to only existing collections
    existing_configs = [c for c in collection_configs if c.path.exists()]

    if not existing_configs:
        print("⚠️  No test collections found")
        return

    # Create runner
    async with MultiCollectionRunner() as runner:
        # Run all collections
        aggregated = await runner.run_all_collections(
            collection_configs=existing_configs,
            parallel=False,
            stop_on_error=False,
        )

        print(f"\n✅ All collections executed!")
        print(f"   Total collections: {aggregated.total_collections}")
        print(f"   Total requests: {aggregated.total_requests}")
        print(f"   Overall success rate: {aggregated.success_rate * 100:.1f}%")


async def example_compare_execution_modes():
    """Example: Compare sequential vs parallel execution."""
    print("\n" + "="*80)
    print("Example 3: Compare Sequential vs Parallel Execution")
    print("="*80)

    # Get test data path
    test_data_path = Path(__file__).parent.parent / "tests" / "test_data"
    collection_path = test_data_path / "execution_collection.json"

    if not collection_path.exists():
        print(f"⚠️  Collection not found: {collection_path}")
        return

    # Create runner
    async with MultiCollectionRunner() as runner:
        # Compare execution modes
        report = await runner.compare_execution_modes(
            collection_path=collection_path,
            context_variables={},
        )

        print(f"\n✅ Comparison completed!")
        print(f"   Speedup factor: {report.speedup_factor:.2f}x")
        print(f"   Time saved: {report.time_saved_ms:.2f}ms")


async def example_cftc_collection():
    """Example: Run CFTC collection (requires API token)."""
    print("\n" + "="*80)
    print("Example 4: Run CFTC Collection")
    print("="*80)

    try:
        # Load configuration (will check for API token)
        config = ConfigManager.load_from_env()
        api_token = config.get("cftc_api_token")

        if not api_token:
            print("⚠️  CFTC_API_TOKEN not configured in .env file")
            print("   This example requires an API token from:")
            print("   https://dev.socrata.com/foundry/publicreporting.cftc.gov/")
            print("   Copy .env.example to .env and add your token")
            return

        # Get CFTC collection config
        cftc_config = ConfigManager.get_cftc_config(api_token)

        if not cftc_config.path.exists():
            print(f"⚠️  CFTC collection not found: {cftc_config.path}")
            return

        # Create runner
        async with MultiCollectionRunner(executor_config=config) as runner:
            # Run CFTC collection
            result = await runner.run_collection(
                collection_path=cftc_config.path,
                context_variables=cftc_config.variables,
                parallel=False,
                stop_on_error=False,
            )

            print(f"\n✅ CFTC collection executed!")
            print(f"   Total requests: {result.total_requests}")
            print(f"   Success rate: {result.success_rate * 100:.1f}%")

    except ImportError as e:
        print(f"⚠️  Missing dependency: {e}")
        print("   Install python-dotenv: pip install python-dotenv")
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all examples."""
    print("\n" + "="*80)
    print("Multi-Collection Execution Examples")
    print("="*80)

    # Run examples
    await example_run_single_collection()
    await example_run_multiple_collections()
    await example_compare_execution_modes()
    await example_cftc_collection()

    print("\n" + "="*80)
    print("All examples completed!")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())


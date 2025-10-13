"""
Example: Variable Scope Introspection

This example demonstrates how to use the VariableTracer to analyze
variable usage, detect shadowing, and find undefined references in
Postman collections.
"""

from python_postman import PythonPostman
from python_postman.models import (
    Collection,
    CollectionInfo,
    Variable,
    Request,
    Folder,
    Url,
    Header,
    Body,
)
from python_postman.introspection import VariableTracer, VariableReference
from python_postman.execution import ExecutionContext


def create_sample_collection():
    """Create a sample collection with various variable scenarios."""
    
    # Create requests with variable references
    get_user = Request(
        name="Get User",
        method="GET",
        url=Url.from_string("{{base_url}}/users/{{user_id}}"),
        headers=[
            Header(key="Authorization", value="Bearer {{api_key}}"),
            Header(key="Content-Type", value="application/json"),
        ],
    )
    
    create_user = Request(
        name="Create User",
        method="POST",
        url=Url.from_string("{{base_url}}/users"),
        headers=[Header(key="Authorization", value="Bearer {{api_key}}")],
        body=Body(
            mode="raw",
            raw='{"name": "{{user_name}}", "email": "{{user_email}}"}',
        ),
    )
    
    # Create folder with shadowed variable
    auth_folder = Folder(
        name="Authentication",
        items=[get_user, create_user],
        variables=[
            Variable(key="api_key", value="folder_override_key"),  # Shadows collection
            Variable(key="endpoint", value="/auth"),
        ],
    )
    
    # Create collection with variables
    collection = Collection(
        info=CollectionInfo(
            name="Sample API Collection",
            schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        ),
        items=[auth_folder],
        variables=[
            Variable(
                key="base_url",
                value="https://api.example.com",
                description="Base URL for the API",
            ),
            Variable(
                key="api_key",
                value="collection_default_key",
                description="API authentication key",
            ),
            Variable(key="user_name", value="John Doe"),
            # Note: user_id and user_email are NOT defined (will be undefined)
        ],
    )
    
    return collection


def example_trace_variable():
    """Example: Trace all definitions of a variable."""
    print("=" * 70)
    print("Example 1: Trace Variable Definitions")
    print("=" * 70)
    
    collection = create_sample_collection()
    tracer = VariableTracer(collection)
    
    # Trace the api_key variable (defined in multiple scopes)
    print("\nTracing 'api_key' variable:")
    references = tracer.trace_variable("api_key")
    
    for i, ref in enumerate(references, 1):
        print(f"\n  Definition {i}:")
        print(f"    Scope: {ref.scope.value}")
        print(f"    Value: {ref.value}")
        print(f"    Location: {ref.location}")
    
    print(f"\n  Total definitions found: {len(references)}")


def example_find_shadowed_variables():
    """Example: Find variables defined in multiple scopes."""
    print("\n" + "=" * 70)
    print("Example 2: Find Shadowed Variables")
    print("=" * 70)
    
    collection = create_sample_collection()
    tracer = VariableTracer(collection)
    
    shadowed = tracer.find_shadowed_variables()
    
    if shadowed:
        print("\n⚠️  Warning: Variables defined in multiple scopes:")
        for var_name, refs in shadowed.items():
            print(f"\n  Variable: '{var_name}'")
            print(f"  Defined in {len(refs)} scopes:")
            for ref in refs:
                print(f"    - {ref.scope.value}: {ref.value}")
                print(f"      at {ref.location}")
    else:
        print("\n✓ No shadowed variables found")


def example_find_undefined_references():
    """Example: Find undefined variable references."""
    print("\n" + "=" * 70)
    print("Example 3: Find Undefined Variable References")
    print("=" * 70)
    
    collection = create_sample_collection()
    tracer = VariableTracer(collection)
    
    undefined = tracer.find_undefined_references()
    
    if undefined:
        print("\n❌ Undefined variables found:")
        for var in undefined:
            print(f"  - {var}")
        print(f"\n  Total undefined: {len(undefined)}")
    else:
        print("\n✓ All variables are defined")


def example_find_variable_usage():
    """Example: Find all usage locations of a variable."""
    print("\n" + "=" * 70)
    print("Example 4: Find Variable Usage Locations")
    print("=" * 70)
    
    collection = create_sample_collection()
    tracer = VariableTracer(collection)
    
    # Find usage of api_key
    print("\nFinding usage of 'api_key':")
    usage = tracer.find_variable_usage("api_key")
    
    if usage:
        print(f"\n  Variable 'api_key' is used in {len(usage)} locations:")
        for location in usage:
            print(f"    - {location}")
    else:
        print("\n  Variable 'api_key' is not used")
    
    # Find usage of base_url
    print("\n\nFinding usage of 'base_url':")
    usage = tracer.find_variable_usage("base_url")
    
    if usage:
        print(f"\n  Variable 'base_url' is used in {len(usage)} locations:")
        for location in usage:
            print(f"    - {location}")


def example_trace_with_context():
    """Example: Trace variables with execution context."""
    print("\n" + "=" * 70)
    print("Example 5: Trace Variables with Execution Context")
    print("=" * 70)
    
    collection = create_sample_collection()
    tracer = VariableTracer(collection)
    
    # Create execution context with runtime overrides
    context = ExecutionContext(
        environment_variables={"env": "production"},
        collection_variables={"api_key": "collection_key"},
        folder_variables={"api_key": "folder_key"},
        request_variables={"api_key": "request_override_key"},
    )
    
    print("\nTracing 'api_key' with execution context:")
    references = tracer.trace_variable("api_key", context)
    
    print(f"\n  Found {len(references)} definitions (ordered by precedence):")
    for i, ref in enumerate(references, 1):
        print(f"\n  {i}. {ref.scope.value.upper()} scope (precedence: {i})")
        print(f"     Value: {ref.value}")
        print(f"     Location: {ref.location}")
    
    print("\n  The effective value will be from REQUEST scope (highest precedence)")


def example_validation_workflow():
    """Example: Complete validation workflow before execution."""
    print("\n" + "=" * 70)
    print("Example 6: Collection Validation Workflow")
    print("=" * 70)
    
    collection = create_sample_collection()
    tracer = VariableTracer(collection)
    
    print("\nValidating collection before execution...")
    
    # Step 1: Check for undefined variables
    print("\n1. Checking for undefined variables...")
    undefined = tracer.find_undefined_references()
    
    if undefined:
        print(f"   ❌ Found {len(undefined)} undefined variables:")
        for var in undefined:
            print(f"      - {var}")
    else:
        print("   ✓ All variables are defined")
    
    # Step 2: Check for shadowed variables
    print("\n2. Checking for shadowed variables...")
    shadowed = tracer.find_shadowed_variables()
    
    if shadowed:
        print(f"   ⚠️  Found {len(shadowed)} shadowed variables:")
        for var_name in shadowed.keys():
            print(f"      - {var_name}")
    else:
        print("   ✓ No shadowed variables")
    
    # Step 3: Generate variable report
    print("\n3. Variable usage report:")
    all_vars = set()
    for var in collection.variables:
        all_vars.add(var.key)
    
    for var_name in sorted(all_vars):
        usage = tracer.find_variable_usage(var_name)
        print(f"   - {var_name}: used in {len(usage)} location(s)")
    
    # Step 4: Validation summary
    print("\n" + "-" * 70)
    if undefined:
        print("❌ Validation FAILED - Cannot execute collection")
        print(f"   Please define: {', '.join(undefined)}")
    else:
        print("✓ Validation PASSED - Collection is ready for execution")
        if shadowed:
            print("⚠️  Note: Some variables are shadowed (review recommended)")


def example_generate_documentation():
    """Example: Generate variable documentation."""
    print("\n" + "=" * 70)
    print("Example 7: Generate Variable Documentation")
    print("=" * 70)
    
    collection = create_sample_collection()
    tracer = VariableTracer(collection)
    
    print("\n# Collection Variables Documentation\n")
    print(f"Collection: {collection.info.name}\n")
    
    for var in collection.variables:
        print(f"## {var.key}")
        print(f"- **Value**: `{var.value}`")
        if var.description:
            print(f"- **Description**: {var.description}")
        
        usage = tracer.find_variable_usage(var.key)
        if usage:
            print(f"- **Usage**: {len(usage)} location(s)")
            for location in usage:
                print(f"  - {location}")
        else:
            print("- **Usage**: Not used")
        
        print()


def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("Variable Scope Introspection Examples")
    print("=" * 70)
    
    # Run all examples
    example_trace_variable()
    example_find_shadowed_variables()
    example_find_undefined_references()
    example_find_variable_usage()
    example_trace_with_context()
    example_validation_workflow()
    example_generate_documentation()
    
    print("\n" + "=" * 70)
    print("Examples completed!")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()

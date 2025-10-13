"""
Example: Working with Description Fields

This example demonstrates how to use description fields effectively
for both folders and requests in a Postman collection.
"""

from python_postman.models import Item, Collection, CollectionInfo

# Example 1: Creating a well-documented API collection
print("=" * 60)
print("Example 1: Creating a Well-Documented Collection")
print("=" * 60)

# Create collection with description
collection_info = CollectionInfo(
    name="E-Commerce API",
    schema="https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
    description="""
# E-Commerce Platform API

This collection contains all API endpoints for the e-commerce platform.

## Authentication
All endpoints require Bearer token authentication unless otherwise noted.

## Base URL
Production: `https://api.ecommerce.com/v1`
Staging: `https://staging-api.ecommerce.com/v1`

## Rate Limits
- 1000 requests per hour for authenticated users
- 100 requests per hour for unauthenticated endpoints
"""
)

# Create folders with descriptions
users_folder = Item.create_folder(
    name="User Management",
    description="""
User account management endpoints.

**Authentication**: Required for all endpoints
**Permissions**: Some endpoints require admin role
"""
)

products_folder = Item.create_folder(
    name="Product Catalog",
    description="""
Product browsing and search endpoints.

**Authentication**: Optional (required for personalized results)
**Caching**: Responses cached for 5 minutes
"""
)

orders_folder = Item.create_folder(
    name="Order Processing",
    description="""
Order creation and management endpoints.

**Authentication**: Required
**Idempotency**: POST requests support idempotency keys
**Webhooks**: Order status changes trigger webhook notifications
"""
)

# Create requests with detailed descriptions
get_user = Item.create_request(
    name="Get User Profile",
    method="GET",
    url="https://api.ecommerce.com/v1/users/{{user_id}}",
    description="""
Retrieves detailed information about a user account.

**Authentication**: Bearer token required
**Permissions**: Users can only access their own profile unless they have admin role

**Path Parameters**:
- `user_id`: UUID of the user

**Response Codes**:
- `200`: Success - returns user object
- `401`: Unauthorized - invalid or missing token
- `403`: Forbidden - insufficient permissions
- `404`: Not found - user does not exist

**Response Body**:
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```
"""
)

create_user = Item.create_request(
    name="Create User",
    method="POST",
    url="https://api.ecommerce.com/v1/users",
    description="""
Creates a new user account.

**Authentication**: Not required (public registration)
**Rate Limit**: 10 requests per hour per IP address

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "John Doe"
}
```

**Validation Rules**:
- Email must be valid and unique
- Password must be at least 8 characters
- Name is optional

**Response Codes**:
- `201`: Created - returns new user object and auth token
- `400`: Bad request - validation errors
- `409`: Conflict - email already exists
- `429`: Too many requests - rate limit exceeded
"""
)

search_products = Item.create_request(
    name="Search Products",
    method="GET",
    url="https://api.ecommerce.com/v1/products/search?q={{query}}&page={{page}}",
    description="""
Search for products by keyword, category, or filters.

**Authentication**: Optional (affects personalization)
**Caching**: Results cached for 5 minutes
**Pagination**: Returns 20 items per page

**Query Parameters**:
- `q`: Search query (required)
- `page`: Page number (default: 1)
- `category`: Filter by category ID (optional)
- `min_price`: Minimum price filter (optional)
- `max_price`: Maximum price filter (optional)
- `sort`: Sort order - `price_asc`, `price_desc`, `relevance` (default: relevance)

**Response Codes**:
- `200`: Success - returns paginated product list
- `400`: Bad request - invalid parameters

**Example Response**:
```json
{
  "results": [...],
  "total": 150,
  "page": 1,
  "pages": 8
}
```
"""
)

create_order = Item.create_request(
    name="Create Order",
    method="POST",
    url="https://api.ecommerce.com/v1/orders",
    description="""
Creates a new order for the authenticated user.

**Authentication**: Bearer token required
**Idempotency**: Include `Idempotency-Key` header to prevent duplicate orders
**Webhooks**: Triggers `order.created` webhook event

**Request Body**:
```json
{
  "items": [
    {"product_id": "uuid", "quantity": 2}
  ],
  "shipping_address_id": "uuid",
  "payment_method_id": "uuid"
}
```

**Business Rules**:
- All products must be in stock
- Shipping address must belong to the user
- Payment method must be valid and verified

**Response Codes**:
- `201`: Created - order successfully placed
- `400`: Bad request - validation errors
- `401`: Unauthorized - invalid token
- `402`: Payment required - payment method declined
- `409`: Conflict - duplicate idempotency key or stock issues

**Important Notes**:
- Orders are held for 15 minutes before payment processing
- Failed payments automatically cancel the order
- Successful orders trigger inventory updates
"""
)

# Add requests to folders
users_folder.items.extend([get_user, create_user])
products_folder.items.append(search_products)
orders_folder.items.append(create_order)

# Create collection
collection = Collection(
    info=collection_info,
    items=[users_folder, products_folder, orders_folder]
)

print(f"\nCollection: {collection.info.name}")
print(f"Description: {collection.info.description[:100]}...")
print(f"\nFolders: {len(collection.items)}")
print(f"Total Requests: {sum(1 for _ in collection.get_requests())}")


# Example 2: Displaying descriptions in a structured way
print("\n" + "=" * 60)
print("Example 2: Displaying Collection Structure with Descriptions")
print("=" * 60)

def display_collection_structure(collection, show_descriptions=True):
    """Display collection structure with descriptions."""
    
    print(f"\n📦 {collection.info.name}")
    if show_descriptions and collection.info.description:
        # Show first line of description
        first_line = collection.info.description.strip().split('\n')[0]
        print(f"   {first_line}")
    
    def display_items(items, indent=1):
        for item in items:
            prefix = "  " * indent
            
            if hasattr(item, 'method'):  # It's a request
                print(f"\n{prefix}🔹 {item.method} {item.name}")
                if show_descriptions and item.description:
                    # Show first meaningful line
                    lines = [l.strip() for l in item.description.strip().split('\n') if l.strip()]
                    if lines:
                        print(f"{prefix}   {lines[0][:80]}...")
            else:  # It's a folder
                print(f"\n{prefix}📁 {item.name}")
                if show_descriptions and item.description:
                    # Show first meaningful line
                    lines = [l.strip() for l in item.description.strip().split('\n') if l.strip()]
                    if lines:
                        print(f"{prefix}   {lines[0][:80]}...")
                
                # Recursively display folder contents
                if hasattr(item, 'items'):
                    display_items(item.items, indent + 1)
    
    display_items(collection.items)

display_collection_structure(collection)


# Example 3: Auditing descriptions
print("\n" + "=" * 60)
print("Example 3: Auditing Description Coverage")
print("=" * 60)

def audit_descriptions(collection):
    """Audit description coverage in a collection."""
    
    stats = {
        'total_items': 0,
        'items_with_descriptions': 0,
        'folders': 0,
        'folders_with_descriptions': 0,
        'requests': 0,
        'requests_with_descriptions': 0,
        'missing': []
    }
    
    def check_items(items, path=""):
        for item in items:
            current_path = f"{path}/{item.name}"
            stats['total_items'] += 1
            
            has_description = bool(item.description and item.description.strip())
            
            if has_description:
                stats['items_with_descriptions'] += 1
            else:
                stats['missing'].append({
                    'type': item.__class__.__name__,
                    'name': item.name,
                    'path': current_path
                })
            
            if hasattr(item, 'method'):  # Request
                stats['requests'] += 1
                if has_description:
                    stats['requests_with_descriptions'] += 1
            else:  # Folder
                stats['folders'] += 1
                if has_description:
                    stats['folders_with_descriptions'] += 1
                
                # Check nested items
                if hasattr(item, 'items'):
                    check_items(item.items, current_path)
    
    check_items(collection.items)
    return stats

stats = audit_descriptions(collection)

print(f"\n📊 Description Coverage Report")
print(f"   Total Items: {stats['total_items']}")
print(f"   Items with Descriptions: {stats['items_with_descriptions']} "
      f"({stats['items_with_descriptions']/stats['total_items']*100:.1f}%)")
print(f"\n   Folders: {stats['folders']}")
print(f"   Folders with Descriptions: {stats['folders_with_descriptions']} "
      f"({stats['folders_with_descriptions']/stats['folders'] * 100:.1f}%)")
print(f"\n   Requests: {stats['requests']}")
print(f"   Requests with Descriptions: {stats['requests_with_descriptions']} "
      f"({stats['requests_with_descriptions']/stats['requests'] * 100:.1f}%)")

if stats['missing']:
    print(f"\n⚠️  Items Missing Descriptions:")
    for item in stats['missing']:
        print(f"   - {item['type']}: {item['path']}")
else:
    print(f"\n✅ All items have descriptions!")


# Example 4: Generating documentation from descriptions
print("\n" + "=" * 60)
print("Example 4: Generating Markdown Documentation")
print("=" * 60)

def generate_markdown_docs(collection):
    """Generate markdown documentation from descriptions."""
    
    lines = [f"# {collection.info.name}\n"]
    
    if collection.info.description:
        lines.append(f"{collection.info.description}\n")
    
    lines.append("\n---\n")
    lines.append("\n## API Endpoints\n")
    
    def process_items(items, level=3):
        for item in items:
            if hasattr(item, 'method'):  # Request
                lines.append(f"\n{'#' * level} {item.method} {item.name}\n")
                lines.append(f"\n**Endpoint:** `{item.url.to_string()}`\n")
                
                if item.description:
                    lines.append(f"\n{item.description}\n")
                
                lines.append("\n---\n")
            else:  # Folder
                lines.append(f"\n{'#' * level} {item.name}\n")
                
                if item.description:
                    lines.append(f"\n{item.description}\n")
                
                # Process folder contents
                if hasattr(item, 'items'):
                    process_items(item.items, level + 1)
    
    process_items(collection.items)
    
    return "\n".join(lines)

markdown = generate_markdown_docs(collection)

# Show preview (first 1000 characters)
print("\n📄 Generated Markdown Documentation (preview):")
print("-" * 60)
print(markdown[:1000])
print("\n... (truncated)")
print("-" * 60)
print(f"\nTotal documentation length: {len(markdown)} characters")


# Example 5: Updating descriptions programmatically
print("\n" + "=" * 60)
print("Example 5: Updating Descriptions Programmatically")
print("=" * 60)

# Create a request without description
incomplete_request = Item.create_request(
    name="Delete User",
    method="DELETE",
    url="https://api.ecommerce.com/v1/users/{{user_id}}"
)

print(f"\nBefore: {incomplete_request.name}")
print(f"Description: {incomplete_request.description or '(none)'}")

# Add description
incomplete_request.description = """
Permanently deletes a user account.

**Authentication**: Bearer token required
**Permissions**: Admin role required

**Warning**: This action cannot be undone. All user data will be permanently deleted.

**Response Codes**:
- `204`: No content - user successfully deleted
- `401`: Unauthorized - invalid token
- `403`: Forbidden - insufficient permissions
- `404`: Not found - user does not exist
"""

print(f"\nAfter: {incomplete_request.name}")
print(f"Description: {incomplete_request.description[:100]}...")


print("\n" + "=" * 60)
print("✅ Examples completed successfully!")
print("=" * 60)
print("\nKey Takeaways:")
print("  • Use descriptions to document API behavior and requirements")
print("  • Markdown formatting makes descriptions more readable")
print("  • Descriptions are valuable for generating documentation")
print("  • Audit your collections to ensure complete documentation")
print("  • Update descriptions when modifying requests or folders")
print("\nFor more information, see: docs/guides/description-fields.md")

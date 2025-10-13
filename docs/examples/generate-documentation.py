"""
Parse → Generate Documentation Workflow Example

This example demonstrates how to use python-postman to generate
comprehensive API documentation from a Postman collection.

The generated documentation includes:
- Collection overview
- Request details (method, URL, headers, body)
- Example responses
- Authentication requirements
- Folder organization

Output formats:
- Markdown
- HTML
- JSON
"""

from python_postman import PythonPostman
from python_postman.introspection import AuthResolver
from typing import List
import json


def generate_markdown_docs(collection) -> str:
    """Generate markdown documentation from collection."""
    
    lines = []
    
    # Header
    lines.append(f"# {collection.info.name}\n")
    
    if collection.info.description:
        lines.append(f"{collection.info.description}\n")
    
    lines.append(f"**Schema Version:** {collection.schema_version}\n")
    lines.append("---\n")
    
    # Table of Contents
    lines.append("## Table of Contents\n")
    
    request_num = 1
    for item in collection.items:
        if hasattr(item, 'items'):  # Folder
            lines.append(f"{request_num}. [{item.name}](#{item.name.lower().replace(' ', '-')})")
            request_num += 1
            for sub_item in item.items:
                if hasattr(sub_item, 'method'):  # Request
                    lines.append(f"   - [{sub_item.name}](#{sub_item.name.lower().replace(' ', '-')})")
        elif hasattr(item, 'method'):  # Request
            lines.append(f"{request_num}. [{item.name}](#{item.name.lower().replace(' ', '-')})")
            request_num += 1
    
    lines.append("\n---\n")
    
    # Collection-level authentication
    if collection.auth:
        lines.append("## Authentication\n")
        lines.append(f"**Type:** {collection.auth.type}\n")
        lines.append("\nThis collection uses collection-level authentication. ")
        lines.append("Individual requests may override this setting.\n")
        lines.append("---\n")
    
    # Collection variables
    if collection.variables:
        lines.append("## Variables\n")
        lines.append("| Variable | Value | Description |")
        lines.append("|----------|-------|-------------|")
        for var in collection.variables:
            value = var.value if var.value else "*not set*"
            desc = var.description if var.description else ""
            lines.append(f"| `{var.key}` | `{value}` | {desc} |")
        lines.append("\n---\n")
    
    # Requests organized by folder
    def document_items(items, level=2):
        for item in items:
            if hasattr(item, 'items'):  # Folder
                document_folder(item, level)
            elif hasattr(item, 'method'):  # Request
                document_request(item, level)
    
    def document_folder(folder, level):
        lines.append(f"{'#' * level} {folder.name}\n")
        
        if folder.description:
            lines.append(f"{folder.description}\n")
        
        # Folder-level auth
        if folder.auth:
            lines.append(f"**Folder Authentication:** {folder.auth.type}\n")
        
        lines.append("")
        
        # Document folder items
        document_items(folder.items, level + 1)
    
    def document_request(request, level):
        lines.append(f"{'#' * level} {request.name}\n")
        
        if request.description:
            lines.append(f"{request.description}\n")
        
        # Request details
        lines.append(f"**Method:** `{request.method}`\n")
        lines.append(f"**URL:** `{request.url.to_string()}`\n")
        
        # Authentication
        resolved_auth = AuthResolver.resolve_auth(request, None, collection)
        if resolved_auth.auth:
            lines.append(f"**Authentication:** {resolved_auth.auth.type} (from {resolved_auth.source.value})\n")
        else:
            lines.append("**Authentication:** None\n")
        
        # Headers
        if request.headers:
            lines.append("\n**Headers:**\n")
            lines.append("| Key | Value |")
            lines.append("|-----|-------|")
            for header in request.headers:
                if not header.disabled:
                    lines.append(f"| `{header.key}` | `{header.value}` |")
            lines.append("")
        
        # Query parameters
        if request.url.query:
            lines.append("**Query Parameters:**\n")
            lines.append("| Key | Value | Description |")
            lines.append("|-----|-------|-------------|")
            for param in request.url.query:
                if not param.disabled:
                    desc = param.description if param.description else ""
                    lines.append(f"| `{param.key}` | `{param.value}` | {desc} |")
            lines.append("")
        
        # Request body
        if request.has_body():
            lines.append("**Request Body:**\n")
            lines.append(f"*Mode:* {request.body.mode}\n")
            
            if request.body.mode == "raw":
                content_type = request.get_content_type() or "text/plain"
                lines.append(f"*Content-Type:* {content_type}\n")
                lines.append("```")
                lines.append(request.body.raw)
                lines.append("```\n")
            elif request.body.mode == "formdata":
                lines.append("| Key | Value | Type |")
                lines.append("|-----|-------|------|")
                for param in request.body.formdata:
                    param_type = param.type if hasattr(param, 'type') else "text"
                    lines.append(f"| `{param.key}` | `{param.value}` | {param_type} |")
                lines.append("")
            elif request.body.mode == "urlencoded":
                lines.append("| Key | Value |")
                lines.append("|-----|-------|")
                for param in request.body.urlencoded:
                    lines.append(f"| `{param.key}` | `{param.value}` |")
                lines.append("")
        
        # Request characteristics
        characteristics = []
        if request.is_safe():
            characteristics.append("Safe")
        if request.is_idempotent():
            characteristics.append("Idempotent")
        if request.is_cacheable():
            characteristics.append("Cacheable")
        
        if characteristics:
            lines.append(f"**Characteristics:** {', '.join(characteristics)}\n")
        
        # Scripts
        if request.has_prerequest_script():
            lines.append("**Pre-request Script:** Yes\n")
        if request.has_test_script():
            lines.append("**Test Script:** Yes\n")
        
        # Example responses
        if request.responses:
            lines.append("\n**Example Responses:**\n")
            for response in request.responses:
                lines.append(f"### {response.name}\n")
                lines.append(f"**Status:** `{response.code} {response.status}`\n")
                
                # Response headers
                if response.headers:
                    lines.append("\n*Headers:*\n")
                    lines.append("| Key | Value |")
                    lines.append("|-----|-------|")
                    for header in response.headers[:5]:  # Limit to first 5
                        lines.append(f"| `{header.key}` | `{header.value}` |")
                    if len(response.headers) > 5:
                        lines.append(f"| ... | *{len(response.headers) - 5} more headers* |")
                    lines.append("")
                
                # Response body
                if response.body:
                    lines.append("*Body:*\n")
                    
                    # Try to parse as JSON for pretty printing
                    try:
                        json_body = json.loads(response.body)
                        lines.append("```json")
                        lines.append(json.dumps(json_body, indent=2))
                        lines.append("```\n")
                    except:
                        # Not JSON, display as-is
                        lines.append("```")
                        # Truncate long responses
                        if len(response.body) > 500:
                            lines.append(response.body[:500])
                            lines.append("... (truncated)")
                        else:
                            lines.append(response.body)
                        lines.append("```\n")
                
                if response.response_time:
                    lines.append(f"*Response Time:* {response.response_time}ms\n")
        
        lines.append("---\n")
    
    # Document all items
    document_items(collection.items)
    
    # Footer
    lines.append("\n---\n")
    lines.append(f"*Generated from Postman Collection: {collection.info.name}*\n")
    
    return "\n".join(lines)


def generate_html_docs(collection) -> str:
    """Generate HTML documentation from collection."""
    
    html = []
    
    # HTML header
    html.append("<!DOCTYPE html>")
    html.append("<html lang='en'>")
    html.append("<head>")
    html.append("    <meta charset='UTF-8'>")
    html.append("    <meta name='viewport' content='width=device-width, initial-scale=1.0'>")
    html.append(f"    <title>{collection.info.name} - API Documentation</title>")
    html.append("    <style>")
    html.append("        body { font-family: Arial, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; }")
    html.append("        h1 { color: #333; border-bottom: 2px solid #ff6c37; padding-bottom: 10px; }")
    html.append("        h2 { color: #555; margin-top: 30px; }")
    html.append("        h3 { color: #777; }")
    html.append("        .method { display: inline-block; padding: 5px 10px; border-radius: 3px; font-weight: bold; color: white; }")
    html.append("        .method.GET { background-color: #61affe; }")
    html.append("        .method.POST { background-color: #49cc90; }")
    html.append("        .method.PUT { background-color: #fca130; }")
    html.append("        .method.DELETE { background-color: #f93e3e; }")
    html.append("        .method.PATCH { background-color: #50e3c2; }")
    html.append("        .url { font-family: monospace; background-color: #f5f5f5; padding: 10px; border-radius: 3px; }")
    html.append("        table { border-collapse: collapse; width: 100%; margin: 10px 0; }")
    html.append("        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }")
    html.append("        th { background-color: #f2f2f2; }")
    html.append("        code { background-color: #f5f5f5; padding: 2px 5px; border-radius: 3px; }")
    html.append("        pre { background-color: #f5f5f5; padding: 15px; border-radius: 5px; overflow-x: auto; }")
    html.append("        .request { margin: 20px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }")
    html.append("        .badge { display: inline-block; padding: 3px 8px; border-radius: 3px; font-size: 12px; margin-right: 5px; }")
    html.append("        .badge.safe { background-color: #d4edda; color: #155724; }")
    html.append("        .badge.idempotent { background-color: #d1ecf1; color: #0c5460; }")
    html.append("        .badge.cacheable { background-color: #fff3cd; color: #856404; }")
    html.append("    </style>")
    html.append("</head>")
    html.append("<body>")
    
    # Title
    html.append(f"    <h1>{collection.info.name}</h1>")
    if collection.info.description:
        html.append(f"    <p>{collection.info.description}</p>")
    
    # Collection info
    html.append(f"    <p><strong>Schema Version:</strong> {collection.schema_version}</p>")
    
    # Requests
    for request in collection.get_requests():
        html.append("    <div class='request'>")
        html.append(f"        <h2>{request.name}</h2>")
        
        if request.description:
            html.append(f"        <p>{request.description}</p>")
        
        html.append(f"        <p><span class='method {request.method}'>{request.method}</span></p>")
        html.append(f"        <div class='url'>{request.url.to_string()}</div>")
        
        # Characteristics
        badges = []
        if request.is_safe():
            badges.append("<span class='badge safe'>Safe</span>")
        if request.is_idempotent():
            badges.append("<span class='badge idempotent'>Idempotent</span>")
        if request.is_cacheable():
            badges.append("<span class='badge cacheable'>Cacheable</span>")
        
        if badges:
            html.append(f"        <p>{''.join(badges)}</p>")
        
        # Headers
        if request.headers:
            html.append("        <h3>Headers</h3>")
            html.append("        <table>")
            html.append("            <tr><th>Key</th><th>Value</th></tr>")
            for header in request.headers:
                if not header.disabled:
                    html.append(f"            <tr><td><code>{header.key}</code></td><td><code>{header.value}</code></td></tr>")
            html.append("        </table>")
        
        # Example responses
        if request.responses:
            html.append("        <h3>Example Responses</h3>")
            for response in request.responses:
                html.append(f"        <h4>{response.name} - {response.code} {response.status}</h4>")
                if response.body:
                    html.append("        <pre><code>")
                    try:
                        json_body = json.loads(response.body)
                        html.append(json.dumps(json_body, indent=2))
                    except:
                        html.append(response.body[:500])
                    html.append("</code></pre>")
        
        html.append("    </div>")
    
    # HTML footer
    html.append("</body>")
    html.append("</html>")
    
    return "\n".join(html)


def generate_json_docs(collection) -> str:
    """Generate JSON documentation from collection."""
    
    docs = {
        "name": collection.info.name,
        "description": collection.info.description,
        "schema_version": str(collection.schema_version),
        "requests": []
    }
    
    for request in collection.get_requests():
        request_doc = {
            "name": request.name,
            "description": request.description,
            "method": request.method,
            "url": request.url.to_string(),
            "headers": [
                {"key": h.key, "value": h.value}
                for h in request.headers if not h.disabled
            ],
            "characteristics": {
                "safe": request.is_safe(),
                "idempotent": request.is_idempotent(),
                "cacheable": request.is_cacheable()
            }
        }
        
        # Add body if present
        if request.has_body():
            request_doc["body"] = {
                "mode": request.body.mode,
                "content": request.body.raw if request.body.mode == "raw" else None
            }
        
        # Add example responses
        if request.responses:
            request_doc["examples"] = [
                {
                    "name": r.name,
                    "status_code": r.code,
                    "status": r.status,
                    "body": r.body
                }
                for r in request.responses
            ]
        
        docs["requests"].append(request_doc)
    
    return json.dumps(docs, indent=2)


def main():
    """Main function to generate documentation."""
    
    print("=" * 60)
    print("POSTMAN COLLECTION DOCUMENTATION GENERATOR")
    print("=" * 60)
    print()
    
    # Parse collection
    print("Parsing collection...")
    parser = PythonPostman()
    collection = parser.parse("collection.json")
    print(f"✓ Parsed: {collection.info.name}")
    print(f"  Requests: {len(list(collection.get_requests()))}")
    print()
    
    # Generate markdown documentation
    print("Generating Markdown documentation...")
    markdown_docs = generate_markdown_docs(collection)
    with open("API_DOCUMENTATION.md", "w") as f:
        f.write(markdown_docs)
    print("✓ Saved to API_DOCUMENTATION.md")
    print()
    
    # Generate HTML documentation
    print("Generating HTML documentation...")
    html_docs = generate_html_docs(collection)
    with open("API_DOCUMENTATION.html", "w") as f:
        f.write(html_docs)
    print("✓ Saved to API_DOCUMENTATION.html")
    print()
    
    # Generate JSON documentation
    print("Generating JSON documentation...")
    json_docs = generate_json_docs(collection)
    with open("API_DOCUMENTATION.json", "w") as f:
        f.write(json_docs)
    print("✓ Saved to API_DOCUMENTATION.json")
    print()
    
    print("=" * 60)
    print("DOCUMENTATION GENERATION COMPLETE")
    print("=" * 60)
    print()
    print("Generated files:")
    print("  - API_DOCUMENTATION.md (Markdown)")
    print("  - API_DOCUMENTATION.html (HTML)")
    print("  - API_DOCUMENTATION.json (JSON)")
    print()


if __name__ == "__main__":
    main()

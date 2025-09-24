# Test Data Collections

This directory contains Postman collection JSON files used for integration testing.

## Valid Collections

### simple_collection.json

- Basic collection with 2 requests (GET and POST)
- Contains collection-level variables
- Tests basic parsing functionality

### nested_collection.json

- Complex nested folder structure with 3 levels of nesting
- Contains 5 requests across multiple folders
- Tests folder navigation, recursive iteration, and hierarchical auth/variables
- Includes different authentication types at different levels

### auth_collection.json

- Collection demonstrating various authentication types
- Contains 4 requests, each with different auth: Basic, Bearer, API Key, OAuth2
- Tests authentication parsing and configuration access

### events_collection.json

- Collection with pre-request scripts and test scripts
- Contains both collection-level and request-level events
- Tests script parsing and event handling

### empty_collection.json

- Valid collection with no items or variables
- Tests handling of empty collections

## Invalid Collections (for error testing)

### malformed_json.json

- Contains JSON syntax errors (missing commas, invalid comments)
- Tests JSON parsing error handling

### invalid_collection.json

- Valid JSON but invalid Postman collection structure (missing required fields)
- Tests collection validation error handling

## Usage

These files are used by the integration tests in `test_integration.py` to validate:

- End-to-end parsing workflows
- Complex nested structures
- Authentication type handling
- Event and script parsing
- Error handling scenarios
- Search and navigation functionality

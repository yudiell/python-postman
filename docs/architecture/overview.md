# Architecture Overview

## Introduction

The python-postman library provides a comprehensive solution for working with Postman collections in Python. It follows a clean, layered architecture that separates concerns and allows users to choose the features they need.

## Core Design Principles

1. **Separation of Concerns**: Clear distinction between parsing/modeling and execution
2. **Type Safety**: Leverage Python's type system for better developer experience
3. **Optional Dependencies**: Core functionality works without execution dependencies
4. **Performance**: Efficient handling of large collections
5. **Extensibility**: Easy to extend with new features

## Architecture Layers

The library is organized into two primary layers:

### 1. Model Layer (Core)

The model layer handles parsing and representing Postman collections as Python objects. This layer has no external dependencies beyond Python's standard library.

**Key Responsibilities:**

- Parse Postman collection JSON files
- Represent collections as Python objects
- Validate collection structure
- Serialize collections back to JSON
- Provide introspection and search capabilities

**Main Components:**

- `parser.py` - Entry point for parsing collections
- `models/` - Object representations of collection elements
- `introspection/` - Tools for analyzing collections
- `search/` - Advanced search and filtering
- `types/` - Type definitions and enums

### 2. Execution Layer (Optional)

The execution layer provides runtime HTTP request execution capabilities. This layer requires the `httpx` library as an optional dependency.

**Key Responsibilities:**

- Execute HTTP requests from collection definitions
- Handle authentication at runtime
- Resolve variables dynamically
- Run pre-request and test scripts
- Capture and process responses

**Main Components:**

- `execution/executor.py` - Request execution engine
- `execution/context.py` - Execution context management
- `execution/auth_handler.py` - Authentication handling
- `execution/variable_resolver.py` - Variable resolution
- `execution/script_runner.py` - Script execution

## Directory Structure

```
python_postman/
├── parser.py                    # Entry point (PythonPostman class)
├── models/                      # Model layer - collection representation
│   ├── collection.py            # Collection and ValidationResult
│   ├── request.py               # Request class
│   ├── folder.py                # Folder class
│   ├── item.py                  # Abstract Item base class
│   ├── auth.py                  # Auth, AuthType, AuthParameter
│   ├── body.py                  # Body, BodyMode, FormParameter
│   ├── header.py                # Header, HeaderCollection
│   ├── url.py                   # Url, QueryParam
│   ├── variable.py              # Variable
│   ├── event.py                 # Event (scripts)
│   ├── response.py              # Response and ExampleResponse
│   ├── schema.py                # Schema version management
│   └── collection_info.py       # CollectionInfo
├── execution/                   # Execution layer (optional)
│   ├── executor.py              # RequestExecutor
│   ├── context.py               # ExecutionContext
│   ├── results.py               # ExecutionResult, TestResults
│   ├── auth_handler.py          # AuthHandler
│   ├── variable_resolver.py     # VariableResolver
│   ├── script_runner.py         # ScriptRunner
│   └── response.py              # ExecutionResponse
├── introspection/               # Introspection utilities
│   ├── auth_resolver.py         # Authentication inheritance resolution
│   └── variable_tracer.py       # Variable scope tracing
├── search/                      # Advanced search and filtering
│   ├── query.py                 # Query builder
│   └── filters.py               # Filter implementations
├── types/                       # Type definitions and enums
│   ├── http_methods.py          # HTTP method enums/literals
│   └── auth_types.py            # Authentication type enums
├── utils/                       # Utility functions
│   ├── json_parser.py           # JSON parsing utilities
│   └── validators.py            # Validation utilities
└── exceptions/                  # Exception classes
    ├── base.py                  # Base exception classes
    ├── parse_error.py           # Parsing exceptions
    ├── validation_error.py      # Validation exceptions
    └── schema_error.py          # Schema version exceptions
```

## Data Flow

### Parsing Flow

```
JSON File → Parser → Collection Object → Model Objects
                                       ↓
                              Validation & Introspection
```

### Execution Flow

```
Collection Object → Request Selection → Variable Resolution
                                              ↓
                                    Authentication Setup
                                              ↓
                                    Pre-request Scripts
                                              ↓
                                      HTTP Execution
                                              ↓
                                       Test Scripts
                                              ↓
                                    Execution Results
```

## Key Design Patterns

### 1. Builder Pattern

Used in search queries for fluent API:

```python
collection.search().by_method("POST").by_host("api.example.com").execute()
```

### 2. Factory Pattern

Used for creating model objects:

```python
Item.create_request(name="Test", method="GET", url="https://api.example.com")
```

### 3. Strategy Pattern

Used for schema version handling:

```python
SchemaValidator.get_parser_for_version(version)
```

### 4. Visitor Pattern

Used for traversing collection hierarchies:

```python
collection.traverse(visitor_function)
```

## Extension Points

The library provides several extension points:

1. **Custom Validators**: Add custom validation logic
2. **Custom Script Runners**: Implement alternative script execution
3. **Custom Auth Handlers**: Add support for new authentication types
4. **Custom Filters**: Create specialized search filters

## Performance Considerations

- **Lazy Loading**: Collections are parsed on-demand
- **Caching**: Statistics and computed values are cached
- **Iterator Support**: Large collections can be processed incrementally
- **Minimal Dependencies**: Core functionality has no external dependencies

## Next Steps

- [Model Layer Documentation](model-layer.md)
- [Execution Layer Documentation](execution-layer.md)
- [Layer Interaction Patterns](layer-interaction.md)
- [Decision Tree](../guides/decision-tree.md)

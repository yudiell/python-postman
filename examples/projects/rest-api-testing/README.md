# REST API Testing Example Project

Complete example project demonstrating REST API testing with postman-collection-runner.

## Overview

This project shows how to:

- Test a REST API with CRUD operations
- Handle authentication
- Validate response data
- Use environment variables
- Generate test reports

## Project Structure

```
rest-api-testing/
├── collections/
│   └── rest-api.json         # Sample REST API collection
├── environments/
│   ├── dev.json              # Development environment
│   └── prod.json             # Production environment
├── tests/
│   └── test_rest_api.py      # Pytest tests
├── main.py                   # Standalone execution
└── requirements.txt
```

## Setup

```bash
pip install -r requirements.txt
```

## Usage

### Standalone Execution

```bash
python main.py
```

### With Pytest

```bash
pytest tests/
```

### With Specific Environment

```bash
python main.py --environment prod
```

## Features Demonstrated

- GET, POST, PUT, DELETE requests
- Bearer token authentication
- Request chaining (using response data in subsequent requests)
- Response validation
- Error handling
- Environment switching

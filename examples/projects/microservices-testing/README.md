# Microservices Testing Example Project

Example project demonstrating testing multiple microservices with postman-collection-runner.

## Overview

This project shows how to:

- Test multiple microservices in sequence
- Share data between service calls
- Handle service dependencies
- Test service integration points
- Manage multiple collections

## Project Structure

```
microservices-testing/
├── collections/
│   ├── auth-service.json
│   ├── user-service.json
│   └── order-service.json
├── environments/
│   └── microservices.json
└── main.py
```

## Scenario

Tests a typical e-commerce microservices architecture:

1. Auth Service - Get authentication token
2. User Service - Create/manage user profile
3. Order Service - Create and process orders

## Usage

```bash
python main.py
```

## Features Demonstrated

- Multi-collection execution
- Token passing between services
- Service dependency handling
- Integration testing
- Error propagation

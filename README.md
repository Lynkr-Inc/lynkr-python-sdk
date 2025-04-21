# Lynkr Python SDK

[![PyPI version](https://img.shields.io/pypi/v/lynkr.svg)](https://pypi.org/project/lynkr/)
[![Python versions](https://img.shields.io/pypi/pyversions/lynkr.svg)](https://pypi.org/project/lynkr/)
[![License](https://img.shields.io/pypi/l/lynkr.svg)](https://github.com/folio-inc/lynkr/blob/main/LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Official Python SDK for the Lynkr Service. This SDK provides a simple and intuitive interface to interact with Lynkr's schema generation and action execution endpoints.

## Features

- Simple and intuitive API
- Comprehensive error handling
- Type hints for better IDE integration
- JSON schema validation
- Extensive documentation

## Installation

```bash
pip install lynkr
```

## Quick Start

```python
import os
from lynkr import Client

# Set your API key as an environment variable
os.environ["LYNKR_API_KEY"] = "your_api_key"

# Create a client
client = Client()

# Get a schema for a natural language request
ref_id, schema = client.get_schema("Show me my current orders in my Wealthsimple account")

# Print the schema details
print(f"Reference ID: {ref_id}")
print(f"Required fields: {schema.get_required_fields()}")
print(f"Schema JSON: {schema.to_json()}")

# Fill in the schema
payload = {
    "service_email": "john@example.com",
    "service_password": "veryverysecure",
}

# Validate the data against the schema
validation_errors = schema.validate(payload)
if validation_errors:
    print(f"Validation errors: {validation_errors}")
else:
    # Execute the action with the filled schema
    result = client.execute_action(ref_id, payload)
    print(f"Action result: {result}")
```

## Usage

### Initializing the Client

You can initialize the client by providing your API key directly or by setting it as an environment variable:

```python
# Option 1: Pass the API key directly
client = Client(api_key="your_api_key")

# Option 2: Use environment variable
import os
os.environ["LYNKR_API_KEY"] = "your_api_key"
client = Client()
```

### Getting a Schema

Get a schema for a natural language request:

```python
ref_id, schema = client.get_schema("Place an order for 100 shares of GOOG on my Wealthsimple account.")
```

The `get_schema` method returns a tuple containing:

- A reference ID string (used for the follow-up execute_action call)
- A Schema object that provides helper methods to work with the schema

### Working with the Schema

The Schema object provides several useful methods:

```python
# Get the schema as a dictionary
schema_dict = schema.to_dict()

# Get the schema as a formatted JSON string
schema_json = schema.to_json(indent=2)

# Get a list of required fields
required_fields = schema.get_required_fields()

# Get the type of a specific field
field_type = schema.get_field_type("report_format")

# Validate data against the schema
errors = schema.validate(your_data)
if not errors:
    print("Data is valid!")
else:
    print(f"Validation errors: {errors}")
```

### Executing an Action

Once you have filled in the schema data, you can execute the action:

```python
# Fill in the schema with the required data
data = {
    "service_email": "john@example.com",
    "service_password": "veryverysecure",
    "security_id": "sec-s-76a7155242e8477880cbb43269235cb6",
    "limit_price": 5.00,
    "quantity": 100,
    "order_type": "buy_quantity",
    "order_sub_type": "limit",
    "time_in_force": "day"
}

# Execute the action
result = client.execute_action(ref_id, data)

# Process the result
print(f"Resulting Action: {result}")
```

## Error Handling

The SDK uses custom exceptions to provide clear error messages:

```python
from lynkr import Client
from lynkr.exceptions import ApiError, ValidationError

try:
    client = Client(api_key="invalid_key")
    ref_id, schema = client.get_schema("Some request")
except ValidationError as e:
    print(f"Validation error: {e}")
except ApiError as e:
    print(f"API error ({e.status_code}): {e.message}")
```

## Advanced Configuration

### Request Timeout

Set a custom timeout for API requests:

```python
client = Client(
    api_key="your_api_key",
    timeout=60  # 60 seconds
)
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

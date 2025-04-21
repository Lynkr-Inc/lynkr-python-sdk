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
from lynkr.client import LynkrClient

# Set your API key directly
client = LynkrClient(api_key="your_api_key")

# Or set your API key as an environment variable
# os.environ["LYNKR_API_KEY"] = "your_api_key"
# client = LynkrClient()

# Get a schema for a natural language request
ref_id, schema = client.get_schema("Show me my current orders in my Wealthsimple account")

# Print the schema details
print(f"Reference ID: {ref_id}")
print(f"Required fields: {schema.get_required_fields()}")
print(f"Schema JSON: {schema.to_json()}")

# Fill in the schema data
schema_data = {
    "service_email": "john@example.com",
    "service_password": "veryverysecure",
}

# Validate the data against the schema
validation_errors = schema.validate(schema_data)
if validation_errors:
    print(f"Validation errors: {validation_errors}")
else:
    # Execute the action with the filled schema data
    # The ref_id from the previous call is stored in the client
    result = client.execute_action(schema_data=schema_data)
    # Or, if you want to specify a different ref_id
    # result = client.execute_action(schema_data=schema_data, ref_id=ref_id)
    print(f"Action result: {result}")
```

## Usage

### Initializing the Client

You can initialize the client by providing your API key directly or by setting it as an environment variable:

```python
# Option 1: Pass the API key directly
client = LynkrClient(api_key="your_api_key")

# Option 2: Use environment variable
import os
os.environ["LYNKR_API_KEY"] = "your_api_key"
client = LynkrClient()

# Customize base URL (optional)
client = LynkrClient(
    api_key="your_api_key",
    base_url="https://custom-api.lynkr.ca",
    timeout=60  # Custom timeout in seconds
)
```

### Getting a Schema

Get a schema for a natural language request:

```python
ref_id, schema = client.get_schema("Place an order for 100 shares of GOOG on my Wealthsimple account.")
```

The `get_schema` method returns a tuple containing:

- A reference ID string (used for the follow-up execute_action call)
- A Schema object that provides helper methods to work with the schema

The reference ID is also stored within the client object for convenience.

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
schema_data = {
    "service_email": "john@example.com",
    "service_password": "veryverysecure",
    "security_id": "sec-s-76a7155242e8477880cbb43269235cb6",
    "limit_price": 5.00,
    "quantity": 100,
    "order_type": "buy_quantity",
    "order_sub_type": "limit",
    "time_in_force": "day"
}

# Execute the action using the stored ref_id from the previous get_schema call
result = client.execute_action(schema_data=schema_data)

# Or provide a specific ref_id
result = client.execute_action(schema_data=schema_data, ref_id="custom_ref_id")

# Process the result
print(f"Result: {result}")
```

## Error Handling

The SDK uses custom exceptions to provide clear error messages:

```python
from lynkr.client import LynkrClient
from lynkr.exceptions import ApiError, ValidationError

try:
    client = LynkrClient(api_key="invalid_key")
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
client = LynkrClient(
    api_key="your_api_key",
    timeout=60  # 60 seconds
)
```

### Custom Base URL

Use a different API endpoint:

```python
client = LynkrClient(
    api_key="your_api_key",
    base_url="https://staging-api.lynkr.ca"
)
```

## Complete Example

Here's a complete example showing a full workflow:

```python
from lynkr.client import LynkrClient
from lynkr.exceptions import ApiError, ValidationError

# Initialize client
client = LynkrClient(api_key="your_api_key")

try:
    # Get schema for sending an email
    ref_id, schema = client.get_schema("I want to send an email")

    # Print schema details
    print(f"Required fields: {schema.get_required_fields()}")

    # Prepare data
    schema_data = {
        "x-api-key": "your_email_provider_api_key",
        "sender_address": "noreply@example.com",
        "receiver_address": "recipient@example.com",
        "subject": "Hello from Lynkr SDK",
        "html": "<p>This is a test email sent using the Lynkr SDK</p>"
    }

    # Validate data
    errors = schema.validate(schema_data)
    if errors:
        print(f"Validation errors: {errors}")
    else:
        # Execute the action
        response = client.execute_action(schema_data=schema_data)
        print(f"Email sent successfully: {response}")

except ValidationError as e:
    print(f"Validation error: {e}")
except ApiError as e:
    print(f"API error: {e}")
    if e.status_code:
        print(f"Status code: {e.status_code}")
    if e.response:
        print(f"Response details: {e.response}")
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

"""
Basic usage example for Lynkr SDK.
"""

import os
import json
from lynkr.client import LynkrClient
from lynkr.exceptions import ApiError, ValidationError

# Set API key
API_KEY = os.environ.get("LYNKR_API_KEY") or "your_api_key_here"

def main():
    """Run the basic example."""
    
    # Initialize client
    client = LynkrClient(api_key=API_KEY)
    
    try:
        # Get schema for a request
        print("Getting schema for request...")
        ref_id, schema = client.get_schema("Generate a weather report for New York City")
        
        print(f"\nReference ID: {ref_id}")
        print(f"Required fields: {schema.get_required_fields()}")
        print(f"Schema: {schema.to_json()}")
        
        # Prepare data according to schema
        schema_data = {
            "location": "New York City",
            "date_range": "next 7 days",
            "units": "metric",
            "include_forecast": True
        }
        
        # Validate the data
        errors = schema.validate(schema_data)
        if errors:
            print(f"\nValidation errors: {errors}")
            return
            
        print("\nData is valid. Executing action...")
        
        # Execute the action (ref_id is stored in the client from the previous get_schema call)
        result = client.execute_action(schema_data=schema_data)
        
        # Alternatively, you can explicitly provide the ref_id
        # result = client.execute_action(schema_data=schema_data, ref_id=ref_id)
        
        # Pretty print the result
        print("\nAction result:")
        print(json.dumps(result, indent=2))
        
    except ValidationError as e:
        print(f"\nValidation error: {e}")
    except ApiError as e:
        print(f"\nAPI error: {e}")
        if hasattr(e, 'status_code') and e.status_code:
            print(f"Status code: {e.status_code}")
        if hasattr(e, 'response') and e.response:
            print(f"Response details: {e.response}")


if __name__ == "__main__":
    main()
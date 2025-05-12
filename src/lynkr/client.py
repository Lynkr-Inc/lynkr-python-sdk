"""
Client module provides the main interface to the API.
"""

import os
import typing as t
from urllib.parse import urljoin

from .utils.http import HttpClient
from .exceptions import ApiError, ValidationError
from .schema import Schema
from .keys.key_manager import KeyManager
from langchain.agents import tool


class LynkrClient:
    """
    Lynkr client for interacting with the API service.
    
    This client provides methods to get schema information and execute actions
    against the API service.
    
    Args:
        api_key: API key for authentication
        base_url: Base URL for the API (defaults to http://api.lynkr.ca)
        timeout: Request timeout in seconds
    """
    
    def __init__(
        self, 
        api_key: str = None, 
        base_url: str = "http://api.lynkr.ca",
        timeout: int = 30,
    ):
        self.api_key = api_key or os.environ.get("LYNKR_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Pass it as a parameter or set LYNKR_API_KEY environment variable."
            )
        
        self.base_url = base_url
        self.ref_id = None
        self.http_client = HttpClient(timeout=timeout)
        self.keys = KeyManager()
    
    def get_schema(self, request_string: str) -> t.Tuple[str, Schema]:
        """
        Get a schema for a given request string.
        
        Args:
            request_string: Natural language description of the request
            
        Returns:
            Tuple containing (ref_id, schema)
            
        Raises:
            ApiError: If the API returns an error
            ValidationError: If the input is invalid
        """
        if not request_string or not isinstance(request_string, str):
            raise ValidationError("request_string must be a non-empty string")
        
        endpoint = urljoin(self.base_url, "/api/v0/schema")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        body = {
            "query": request_string
        }
        
        response = self.http_client.post(
            url=endpoint,
            headers=headers,
            json=body
        )
        
        # Extract ref_id and schema from response
        ref_id = response.get("ref_id")
        self.ref_id = ref_id

        schema_data = response.get("schema")
        
        if not ref_id or not schema_data:
            raise ApiError("Invalid response format from API")
            
        # Create the schema object
        schema = Schema(schema_data)
        
        # Store the metadata for later use, if available
        self.last_metadata = response.get("metadata", {})
        
        return ref_id, schema
    
    def to_execute_format(self, schema: Schema) -> t.Dict[str, t.Any]:
        """
        Convert schema to a format suitable for execution.
        
        Args:
            schema: Schema object
        
        Returns:
            Dict representation of the schema for execution
        """
        return {
            "schema": schema.to_dict()
        }
    
    def execute_action(
        self, 
        schema_data: t.Dict[str, t.Any], 
        ref_id: t.Optional[str] = None,
        auto_fill_keys: bool = True
    ) -> t.Dict[str, t.Any]:
        """
        Execute an action using the provided schema data.
        
        Args:
            schema_data: Filled schema data according to the schema structure
            ref_id: Reference ID returned from get_schema, default set to most recent get_schema call
            auto_fill_keys: Whether to automatically fill missing fields with stored API keys
            
        Returns:
            Dict containing the API response
            
        Raises:
            ApiError: If the API returns an error
            ValidationError: If the input is invalid
        """
            
        if ref_id is None and self.ref_id is None:
            return {
                "error": "ref_id is required to execute an action"
            }
        else:
            ref_id = ref_id or self.ref_id

        if not schema_data or not isinstance(schema_data, dict):
            raise ValidationError("schema_data must be a non-empty dictionary")
        
        # Auto-fill keys if enabled - try to detect the service from metadata
        if auto_fill_keys and hasattr(self, 'keys'):
            # If we have metadata from the last get_schema call, use it to identify the service
            service = getattr(self, 'last_metadata', {}).get('service')
            
            # Default fill using known field mappings
            updated_schema_data = self.keys.match_keys_to_schema(
                schema_data, 
                schema_data.get('required_fields', [])
            )
            
            # If we know the service, use it for more specific mapping
            if service and hasattr(self.keys, '_keys') and service.lower() in self.keys._keys:
                service_key = self.keys._keys.get(service.lower())
                for field_name in schema_data.get('required_fields', []):
                    # Check if this field is likely an API key field
                    if any(key_term in field_name.lower() for key_term in ['api_key', 'apikey', 'key', 'token', 'auth']):
                        updated_schema_data[field_name] = service_key
            
            schema_data = updated_schema_data

            print(f"Auto-filled schema data: {schema_data}")
        
        schema_payload = {
            "fields": { k: { "value": v } for k, v in schema_data.items() }
        }
        
        endpoint = urljoin(self.base_url, "/api/v0/execute")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "ref_id": ref_id,
            "schema": schema_payload
        }
        
        response = self.http_client.post(
            url=endpoint,
            headers=headers,
            json=payload
        )
        
        return response
    
    def langchain_tools(self) -> list:
        """
        Get LangChain tools for interacting with Lynkr.
        
        Returns:
            List of LangChain tools
        """
        @tool
        def get_schema(request_string: str):
            """
            Get a schema for a natural language request.
            
            This tool helps you understand what fields/parameters are required for a specific operation.
            Use this tool when you need to:
            - Convert a natural language request into a structured format
            - Determine what information is needed to fulfill a user's request
            - Find out the required fields for an action
            
            Examples:
            - "Get the schema for sending an email"
            - "What information is needed to check my bank balance"
            - "Show me fields required for ordering food delivery"
            
            Args:
                request_string: A clear, specific description of what you want to do
            
            Returns:
                Information about the required fields and reference ID for the action
            """
            try:
                ref_id, schema = self.get_schema(request_string)
                
                # Get details about the schema
                required_fields = schema.get_required_fields()
                optional_fields = schema._schema.get('optional_fields', [])
                sensitive_fields = schema._schema.get('sensitive_fields', [])
                
                # Check if we have API keys for the sensitive fields
                has_keys_for = []
                missing_keys_for = []
                
                for field in sensitive_fields:
                    # Check if we have a key that matches this field
                    field_matched = False
                    for key_name in self.keys._keys:
                        mappings = self.keys.get_field_mappings(key_name)
                        if field in mappings or field == key_name:
                            has_keys_for.append(field)
                            field_matched = True
                            break
                    
                    if not field_matched:
                        missing_keys_for.append(field)
                
                # Store the ref_id for later use
                self.ref_id = ref_id
                
                # Return useful information for the agent
                return {
                    "ref_id": ref_id,
                    "required_fields": required_fields,
                    "optional_fields": optional_fields,
                    "sensitive_fields": sensitive_fields,
                    "has_keys_for": has_keys_for,
                    "missing_keys_for": missing_keys_for,
                    "schema_json": schema.to_json()
                }

            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def execute_action(schema_data: dict, ref_id: str = None):
            """
            Execute an action with the provided schema data.
            
            Use this tool after getting a schema and filling in the required fields.
            This tool will:
            - Automatically fill in API keys if they're available
            - Submit the action for execution
            - Return the results
            
            Args:
                schema_data: Dictionary containing the field values for the action
                ref_id: Optional reference ID from a previous get_schema call
                       (if not provided, the most recent ref_id will be used)
            
            Returns:
                The result of executing the action
            """
            try:
                # Execute the action with the filled schema data
                result = self.execute_action(
                    schema_data=schema_data, 
                    ref_id=ref_id,
                    auto_fill_keys=True
                )
                return result
            except Exception as e:
                return f"Error: {str(e)}"
            
        @tool
        def list_api_keys():
            """
            List all stored API keys (with masked values for security).
            
            Use this tool to see what API keys are currently available for automatic filling.
            
            Returns:
                Dictionary of stored keys with masked values
            """
            try:
                return self.keys.list()
            except Exception as e:
                return f"Error listing API keys: {str(e)}"
                
        return [get_schema, execute_action, list_api_keys]
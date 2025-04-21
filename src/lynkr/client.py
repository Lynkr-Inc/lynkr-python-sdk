"""
Client module provides the main interface to the API.
"""

import os
import typing as t
from urllib.parse import urljoin

from .utils.http import HttpClient
from .exceptions import ApiError, ValidationError
from .schema import Schema


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
        timeout: int = 30
    ):
        self.api_key = api_key or os.environ.get("LYNKR_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API key is required. Pass it as a parameter or set LYNKR_API_KEY environment variable."
            )
        
        self.base_url = base_url
        self.ref_id = None
        self.http_client = HttpClient(timeout=timeout)
    
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
        
        body={
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
            
        return ref_id, Schema(schema_data)
    
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
    
    def execute_action(self, schema_data: t.Dict[str, t.Any], ref_id: t.Optional[str] = None) -> t.Dict[str, t.Any]:
        """
        Execute an action using the provided schema data.
        
        Args:
            ref_id: Reference ID returned from get_schema default set to most recent get_schema call
            schema_data: Filled schema data according to the schema structure
            
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
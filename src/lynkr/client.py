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

import json

class LynkrClient:
    """
    Lynkr client for interacting with the API service.
    
    This client provides methods to get schema information and execute actions
    against the API service.
    
    Args:
        api_key: API key for authentication
        base_url: Base URL for the API (defaults to http://api.lynkr.ca)
        timeout: Request timeout in seconds (default is 30)
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
                "API key is required. Pass it as a parameter to this method or set LYNKR_API_KEY environment variable."
            )
        
        self.base_url = base_url
        self.ref_id = None
        self.http_client = HttpClient(timeout=timeout)
        self.keys = {}
    def add_key(self, name: str, field_name: str, value: str):
        """
        Add or update a single credential field under a service.
        If the service doesn't exist yet, create it.
        If the field already exists, this will overwrite it with the new value.
        """
        # 1) create the service dict if needed
        svc = self.keys.setdefault(name, {})

        # 2) assign (or overwrite) the field
        svc[field_name] = value
        
    def get_schema(self, request_string: str) -> t.Tuple[str, Schema, str]:
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
        
        service = response.get("metadata")["service"]

        if not ref_id or not schema_data:
            raise ApiError("Invalid response format from API")
        
        return ref_id,  Schema(schema_data), service
        
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
    
    def langchain_tools(self) -> list:
        """
        Get a schema for a given request string using LangChain.
        
        Args:
            request_string: Natural language description of the request
            
        Returns:
            Tuple containing (ref_id, schema)
            
        Raises:
            ApiError: If the API returns an error
            ValidationError: If the input is invalid
        """
        def build_min_required(data, include_sensitive=False):
            """
            Build a JSON payload containing all required fields.
            
            Args:
                data (dict): Input dict containing 'ref_id', 'schema', 'service', etc.
                include_sensitive (bool): If True, include sensitive fields; otherwise skip them.

            Returns:
                str: Pretty-printed JSON string of the minimal required payload.
            """
            schema_d = data.__dict__["_schema"]
            print("SCHEMAD", schema_d)
            fields    = schema_d.get("fields", {})
            required  = schema_d.get("required_fields", []) or schema_d.get("required", [])
            sensitive = set(schema_d.get("sensitive_fields", []))
            
            payload = {
            }
            
            for field in required:
                # Skip sensitive unless explicitly requested
                if field in sensitive and not include_sensitive:
                    continue
                
                info = fields[field]
                t = info["type"]
                
                if t == "string":
                    payload[field] = ""
                elif t == "list":
                    payload[field] = []
                elif t == "integer":
                    payload[field] = 0
                elif t == "boolean":
                    payload[field] = False
                else:
                    payload[field] = None

            return json.dumps(payload, indent=2)
        # ——— Example usage ———

        async def get_schema(request_string: str):
            """
            get_schema(request_string: str) -> dict

            Converts a single, precise naturallanguage instruction into a structured schema.

            Usage:
            • Call this if you need to figure out which fields are required to fulfill a users request.
            • Always supply exactly one clear sentence, e.g.:
                "Send an email with subject, body, sender and recipient."
            • Returns:
                {
                    "ref_id":   "<unique schema ID>",
                    "schema":   { field_name: { "type": ..., "optional": ..., "sensitive": ... }, … },
                    "service":  "<integration key, e.g. 'resend', 'twilio', …>",
                    "message":  "Missing credentials for service: <service>"
                                OR "Credentials provided for service: <service>"
                }
            • If you see “Missing credentials…”, ask the user for API keys before proceeding.
            """
            try:
                ref_id, schema, service = self.get_schema(request_string)
                if service not in self.keys:
                    return {"ref_id":ref_id, "schema":schema, "service":service, "message": "No service key is provided schema data for execute actions should include schema key", "schema_example": build_min_required(schema, True)}
                else: 
                    return {"ref_id":ref_id, "schema":schema, "service":service, "message": "The service secrets are provided.", "schema_example": build_min_required(schema)}
           
            except Exception as e:
                return f"Error: {str(e)}"

        async def execute_schema(schema_data: dict, ref_id: str = None, service: str = None):
            """
            execute_schema(schema_data: dict, ref_id: str, service: str) -> dict

            Executes a fullypopulated schema against the specified external integration.

            Usage:
            • Only call this after get_schema has returned and you have merged in all required keys.
            • Input:
                schema_data: { field1: value1, field2: value2, …, api_key: "SECRET", … }
                ref_id:      "<ID from get_schema>"
                service:     "<service name from get_schema>"
            • Returns the raw API response, e.g.
                { "status": "success", "messageId": "XYZ789", … }
            • After calling this, you must emit a final userfriendly confirmation and stop.
            """
            try:
                
                currentService = self.keys.get(service)

                schema_data = {**schema_data, **currentService}
                print(schema_data)
                # Execute the action with the filled schema data
                # The ref_id from the previous call is stored in the client
                # for subsequent calls, so you can just call execute_action
                # result = lynkr_client.execute_action(schema_data=schema_data)
                # Or, if you want to specify a different ref_id
                result = self.execute_action(schema_data=schema_data, ref_id=ref_id)
                print(f"Action result: {result}")
                return {"result": result}
            except Exception as e:
                return f"Error: {str(e)}"
            
        return [get_schema, execute_schema]

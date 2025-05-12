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
        @tool
        def get_schema(request_string: str):
            """
            Use this tool when you need to convert a natural language request into a structured schema.
            
            This tool helps you obtain the appropriate data structure or schema needed to fulfill a user's request.
            Call this tool whenever you:
            - Need to understand what fields/parameters are required for a specific operation
            - Want to convert a user's natural language request into a structured format
            - Need to determine the expected format for submitting data
            
            Your request_string should be a single, specific sentence clearly stating exactly what schema you need.
            For best results, be precise about the specific action or data type you're working with.
            
            Examples of good request strings:
            - "I need the schema for creating a new user account"
            - "Get me the schema for processing a payment transaction"
            - "Show me the data structure required for booking a flight"
            
            Args:
                request_string: A clear, specific natural language description of what schema you need
            
            Returns:
                A structured schema matching your request
            """
            try:
                ref_id, schema, service = self.get_schema(request_string)
                if service not in self.keys:
                    return {"ref_id":ref_id, "schema":schema, "service":service, "message": "No service key is provided schema data for execute actions should include schema key"}
                else: 
                    return {"ref_id":ref_id, "schema":schema, "service":service, "message": "The service secrets are provided."}
           
            except Exception as e:
                return f"Error: {str(e)}"

        @tool
        def execute_schema(schema_data: dict, ref_id: str = None, service: str = None):
            """
            Use this tool to execute actions based on a schema obtained from get_schema().
            
            This tool takes a schema (typically obtained from a previous get_schema call) and executes it
            after filling in any missing information through conversations with the user or by using other tools.
            
            Call this tool when:
            - You have obtained a schema and need to execute the corresponding action
            - You have gathered all necessary information to complete a user's request
            - You need to submit structured data to perform an operation
            
            The process typically follows these steps:
            1. First call get_schema() to obtain the required schema structure
            2. Gather any missing information by either:
            - Asking the user directly for specific inputs
            - Using other available tools to retrieve the required data
            3. Call this execute_schema() tool with the complete information
            
            Args:
                schema: The schema structure (dictionary) obtained from get_schema() filled with the information based on the schema guidelines and the user
                ref_id: The reference ID from the previous get_schema call (optional)
                service: The service name to use for filling in the schema data
            Returns:
                The result of executing the action defined by the filled schema
            
            Note: If the schema cannot be completely filled with available information, this tool will
            automatically engage with the user to request the missing details before execution.
            """
            try:
                
                currentService = self.keys.get(service)

                schema_data = {**schema_data, **currentService}
                print(schema_data)
                validation_errors = schema_data.validate(schema_data)
                if validation_errors:
                    print(f"Validation errors: {validation_errors}")
                else:
                    # Execute the action with the filled schema data
                    # The ref_id from the previous call is stored in the client
                    # for subsequent calls, so you can just call execute_action
                    # result = lynkr_client.execute_action(schema_data=schema_data)
                    # Or, if you want to specify a different ref_id
                    result = self.execute_action(schema_data=schema_data, ref_id=ref_id)
                    print(f"Action result: {result}")
            except Exception as e:
                return f"Error: {str(e)}"
            
        return [get_schema, execute_schema]

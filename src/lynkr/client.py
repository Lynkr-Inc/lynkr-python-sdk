"""
Client module provides the main interface to the API.
"""

import json
import os
import typing as t
from urllib.parse import urljoin
import base64

from .utils.http import HttpClient
from .exceptions import ApiError, ValidationError
from .schema import Schema
from .keys.key_manager import KeyManager
from langchain.agents import tool
from langchain_core.tools.structured import StructuredTool
from .crypto import hybrid_encrypt, load_public_key, decrypt_with_aes


class LynkrClient:
    """
    Lynkr client for interacting with the API service.
    
    This client provides methods to get schema information and execute actions
    against the API service.
    
    Args:
        api_key: API key for authentication
        base_url: Base URL for the API (defaults to https://api.lynkr.ca)
        timeout: Request timeout in seconds (default is 30)
    """
    
    def __init__(
        self, 
        api_key: str = None, 
        base_url: str = "https://api.lynkr.ca",
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
        
        endpoint = urljoin(self.base_url, "/api/v0/schema/")
        
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
    
    def execute_action(self, schema_data: dict, ref_id: str = None, service: str = None):
        """
        Use this tool to execute actions based on a schema obtained from get_schema().
        
        This tool takes a schema (typically obtained from a previous get_schema call) and executes it
        after filling in any missing information through conversations with the user or by using other tools.
        
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
            result = self.execute(schema_data=schema_data, ref_id=ref_id)
            return {"Result": result}
        except Exception as e:
            return f"Error: {str(e)}"
            
    def execute(self, schema_data: t.Dict[str, t.Any], ref_id: t.Optional[str] = None) -> t.Dict[str, t.Any]:
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
        
        endpoint = urljoin(self.base_url, "/api/v0/execute/")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "ref_id": ref_id,
            "schema": schema_payload
        }
        
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        PUBLIC_KEY_PATH = os.path.join(BASE_DIR, "public_key.pem")
        public_key = load_public_key(PUBLIC_KEY_PATH)  # Adjust as needed
        
        encrypted_data, aes_key = hybrid_encrypt(payload, public_key)
        
        response = self.http_client.post(
            url=endpoint,
            headers=headers,
            json=encrypted_data
        )

        resp_json = response["data"]

        if all(k in resp_json for k in ("payload", "iv", "tag")):
            ciphertext = base64.b64decode(resp_json["payload"])
            iv = base64.b64decode(resp_json["iv"])
            tag = base64.b64decode(resp_json["tag"])
            plaintext = decrypt_with_aes(ciphertext, aes_key, iv, tag)
            try:
                # Usually the server returns JSON as plaintext
                return json.loads(plaintext.decode())
            except Exception as e:
                # Could not decode JSON, return raw plaintext
                return plaintext
        else:
            # Not encrypted, just return the response as usual
            return resp_json
    
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
        
        def get_minimum_schema(data: str, include_sensitive: bool = False):
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
            
            Args:print(response)
                request_string: A clear, specific natural language description of what schema you need
            
            Returns:
                str: Pretty-printed JSON string of the minimal required payload.
            """
            schema_d = data.__dict__["_schema"]
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

        def get_schema_langchain(request_string: str):
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
                    "schema":   {'fields': {'required': [{'name': ...}, ...], 'optional': [{'name': ...}], 'sensitive_fields': ['x-api-key']},
                    "service":  "<integration key, e.g. 'resend', 'twilio', …>",
                    "message":  "Missing credentials for service: <service>"
                                OR "Credentials provided for service: <service>"
                }
            • If you see “Missing credentials…”, ask the user for API keys before proceeding.
            """
            try:
                print(request_string)
                ref_id, schema, service = self.get_schema(request_string)
                print(schema)
                if service not in self.keys:
                    return {"ref_id":ref_id, "schema":schema, "service":service, "message": "No service key is provided schema data for execute actions should include schema key"}
                else: 
                    return {"ref_id":ref_id, "schema":schema, "service":service, "message": "The service secrets are provided."}
           
            except Exception as e:
                return f"Error: {str(e)}"

        def execute_schema_langchain(schema_data: dict, ref_id: str = None, service: str = None):
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
                result = self.execute(schema_data=schema_data, ref_id=ref_id)
                return {"Result": result}
            except Exception as e:
                return f"Error: {str(e)}"
        tools = [
                    StructuredTool.from_function(
                        get_schema_langchain,
                        name="get_schema_langchain",
                        description="Translate a single, precise natural-language instruction into a structured schema."
                    ),
                    StructuredTool.from_function(
                        execute_schema_langchain,
                        name="execute_schema_langchain",
                        description="Execute a fully-populated schema against the specified external integration."
                    ),
                ] 
        return tools

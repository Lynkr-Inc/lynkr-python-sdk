"""
Tests for the LynkrClient class.
"""

import pytest
import json
import responses
from urllib.parse import urljoin

from lynkr.client import LynkrClient
from lynkr.exceptions import ApiError, ValidationError


class TestLynkrClient:
    """Tests for the LynkrClient class."""

    def test_init_with_api_key(self, api_key):
        """Test initializing with API key parameter."""
        client = LynkrClient(api_key=api_key)
        assert client.api_key == api_key

    def test_init_without_api_key(self, monkeypatch):
        """Test initializing with API key from environment."""
        monkeypatch.setenv("LYNKR_API_KEY", "env_api_key")
        client = LynkrClient()
        assert client.api_key == "env_api_key"

    def test_init_missing_api_key(self, monkeypatch):
        """Test initializing without API key raises error."""
        monkeypatch.delenv("LYNKR_API_KEY", raising=False)
        with pytest.raises(ValueError) as excinfo:
            LynkrClient()
        assert "API key is required" in str(excinfo.value)

    def test_get_schema(self, client, mock_responses, schema_response, base_url):
        """Test get_schema method."""
        request_string = "Create a new user"
        url = urljoin(base_url, "/api/v0/schema")
        
        mock_responses.add(
            responses.POST,
            url,
            json=schema_response,
            status=200
        )
        
        ref_id, schema, service = client.get_schema(request_string)
        
        assert ref_id == schema_response["ref_id"]
        assert schema.to_dict() == schema_response["schema"]
        assert service == schema_response["metadata"]["service"]
        
        # Check request payload
        request = mock_responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["query"] == request_string

    def test_get_schema_validation_error(self, client):
        """Test get_schema with invalid input."""
        with pytest.raises(ValidationError) as excinfo:
            client.get_schema("")
        assert "request_string must be a non-empty string" in str(excinfo.value)

    def test_get_schema_api_error(self, client, mock_responses, base_url):
        """Test get_schema with API error response."""
        request_string = "Create a new user"
        url = urljoin(base_url, "/api/v0/schema")
        
        error_response = {
            "error": "invalid_request",
            "message": "Invalid request format"
        }
        
        mock_responses.add(
            responses.POST,
            url,
            json=error_response,
            status=400
        )
        
        with pytest.raises(ApiError) as excinfo:
            client.get_schema(request_string)
        # Fixed: Changed the expected error message to match what ApiError actually returns
        assert "Invalid request format" in str(excinfo.value)

    def test_to_execute_format(self, client, schema_response):
        """Test to_execute_format method."""
        from lynkr.schema import Schema
        
        schema = Schema(schema_response["schema"])
        # Fixed: Changed method name from toExecuteFormat to to_execute_format
        result = client.to_execute_format(schema)
        
        assert "schema" in result
        assert result["schema"] == schema_response["schema"]

    def test_execute_action(self, client, mock_responses, execute_response, base_url):
        """Test execute_action method."""
        # Set up the ref_id in the client
        client.ref_id = "ref_123456789"
        
        schema_data = {"name": "Test User"}
        
        url = urljoin(base_url, "/api/v0/execute")
        
        mock_responses.add(
            responses.POST,
            url,
            json=execute_response,
            status=200
        )
        
        result = client.execute_action(schema_data=schema_data)
        
        assert result == execute_response
        
        # Check request payload
        request = mock_responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["ref_id"] == "ref_123456789"
        assert "schema" in payload
        assert "fields" in payload["schema"]
        assert payload["schema"]["fields"]["name"]["value"] == "Test User"

    def test_execute_action_with_explicit_ref_id(self, client, mock_responses, execute_response, base_url):
        """Test execute_action with explicit ref_id."""
        schema_data = {"name": "Test User"}
        explicit_ref_id = "explicit_ref_id"
        
        url = urljoin(base_url, "/api/v0/execute")
        
        mock_responses.add(
            responses.POST,
            url,
            json=execute_response,
            status=200
        )
        
        result = client.execute_action(schema_data=schema_data, ref_id=explicit_ref_id)
        
        assert result == execute_response
        
        # Check request payload
        request = mock_responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["ref_id"] == explicit_ref_id

    def test_execute_action_without_ref_id(self, client):
        """Test execute_action with no ref_id."""
        schema_data = {"name": "Test User"}
        
        # Ensure client has no ref_id
        client.ref_id = None
        
        result = client.execute_action(schema_data=schema_data)
        
        assert "error" in result
        assert "ref_id is required" in result["error"]

    def test_execute_action_validation_error(self, client):
        """Test execute_action with invalid input."""
        client.ref_id = "ref_123456789"
        
        with pytest.raises(ValidationError) as excinfo:
            client.execute_action(schema_data="")
        assert "schema_data must be a non-empty dictionary" in str(excinfo.value)

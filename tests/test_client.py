"""
Tests for the Client class.
"""

import pytest
import json
import responses
from urllib.parse import urlencode

from lynkr import Client
from lynkr.exceptions import ApiError, ValidationError


class TestClient:
    """Tests for the Client class."""

    def test_init_with_api_key(self, api_key):
        """Test initializing with API key parameter."""
        client = Client(api_key=api_key)
        assert client.api_key == api_key

    def test_init_without_api_key(self, monkeypatch):
        """Test initializing with API key from environment."""
        monkeypatch.setenv("MYAPI_API_KEY", "env_api_key")
        client = Client()
        assert client.api_key == "env_api_key"

    def test_init_missing_api_key(self, monkeypatch):
        """Test initializing without API key raises error."""
        monkeypatch.delenv("MYAPI_API_KEY", raising=False)
        with pytest.raises(ValueError) as excinfo:
            Client()
        assert "API key is required" in str(excinfo.value)

    def test_get_schema(self, client, mock_responses, schema_response, base_url):
        """Test get_schema method."""
        request_string = "Create a new user"
        params = {"request": request_string}
        url = f"{base_url}/api/v0/schema/?{urlencode(params)}"
        
        mock_responses.add(
            responses.GET,
            url,
            json=schema_response,
            status=200
        )
        
        ref_id, schema = client.get_schema(request_string)
        
        assert ref_id == schema_response["ref_id"]
        assert schema.to_dict() == schema_response["schema"]

    def test_get_schema_validation_error(self, client):
        """Test get_schema with invalid input."""
        with pytest.raises(ValidationError) as excinfo:
            client.get_schema("")
        assert "request_string must be a non-empty string" in str(excinfo.value)

    def test_get_schema_api_error(self, client, mock_responses, base_url):
        """Test get_schema with API error response."""
        request_string = "Create a new user"
        params = {"request": request_string}
        url = f"{base_url}/api/v0/schema/?{urlencode(params)}"
        
        error_response = {
            "error": "invalid_request",
            "message": "Invalid request format"
        }
        
        mock_responses.add(
            responses.GET,
            url,
            json=error_response,
            status=400
        )
        
        with pytest.raises(ApiError) as excinfo:
            client.get_schema(request_string)
        assert "Invalid request format" in str(excinfo.value)

    def test_execute_action(self, client, mock_responses, execute_response, base_url):
        """Test execute_action method."""
        ref_id = "ref_123456789"
        data = {"name": "Test User", "email": "test@example.com"}
        
        url = f"{base_url}/api/v0/execute/"
        
        mock_responses.add(
            responses.POST,
            url,
            json=execute_response,
            status=200
        )
        
        result = client.execute_action(ref_id, data)
        
        assert result == execute_response
        
        # Check request payload
        request = mock_responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["ref_id"] == ref_id
        assert payload["data"] == data

    def test_execute_action_validation_error(self, client):
        """Test execute_action with invalid input."""
        with pytest.raises(ValidationError) as excinfo:
            client.execute_action("", {})
        assert "ref_id must be a non-empty string" in str(excinfo.value)
        
        with pytest.raises(ValidationError) as excinfo:
            client.execute_action("ref_id", "")
        assert "schema_data must be a non-empty dictionary" in str(excinfo.value)
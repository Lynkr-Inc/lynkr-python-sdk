"""
Tests for the LynkrClient class.
"""

import pytest
import json
import responses
import base64
from unittest.mock import patch, MagicMock
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
        url = urljoin(base_url, "/api/v0/schema/")
        
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
        url = urljoin(base_url, "/api/v0/schema/")
        
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
        assert "Invalid request format" in str(excinfo.value)

    def test_to_execute_format(self, client, schema_response):
        """Test to_execute_format method."""
        from lynkr.schema import Schema
        
        schema = Schema(schema_response["schema"])
        result = client.to_execute_format(schema)
        
        assert "schema" in result
        assert result["schema"] == schema_response["schema"]

    @patch('lynkr.client.hybrid_encrypt')
    @patch('lynkr.client.load_public_key')
    def test_execute_action(self, mock_load_key, mock_encrypt, client, mock_responses, execute_response, base_url):
        """Test execute_action method using a non-encrypted response path."""
        # Set up the ref_id in the client
        client.ref_id = "ref_123456789"
        
        # Mock the encryption functions
        mock_public_key = MagicMock()
        mock_load_key.return_value = mock_public_key
        mock_encrypt.return_value = (
            {
                "encrypted_key": "test_key", 
                "iv": "test_iv", 
                "tag": "test_tag", 
                "payload": "test_payload"
            }, 
            b'test_aes_key'
        )
        
        # Set up a NON-encrypted response (missing iv/tag/payload)
        # This will skip the decryption logic in the client
        non_encrypted_response = {
            "data": execute_response["data"]
        }
        
        schema_data = {"name": "Test User"}
        
        url = urljoin(base_url, "/api/v0/execute/")
        
        mock_responses.add(
            responses.POST,
            url,
            json=non_encrypted_response,
            status=200
        )
        
        result = client.execute_action(schema_data=schema_data)
        
        # The result should be the data from execute_response
        assert result == execute_response["data"]
        
        # Verify the request was made correctly
        assert len(mock_responses.calls) == 1
        request = mock_responses.calls[0].request
        payload = json.loads(request.body)
        assert payload["encrypted_key"] == "test_key"
        assert payload["iv"] == "test_iv"
        assert payload["tag"] == "test_tag"
        assert payload["payload"] == "test_payload"

    @patch('lynkr.client.hybrid_encrypt')
    @patch('lynkr.client.load_public_key') 
    def test_execute_action_with_explicit_ref_id(self, mock_load_key, mock_encrypt, client, mock_responses, execute_response, base_url):
        """Test execute_action with explicit ref_id."""
        # Mock the encryption functions
        mock_public_key = MagicMock()
        mock_load_key.return_value = mock_public_key
        mock_encrypt.return_value = (
            {
                "encrypted_key": "test_key", 
                "iv": "test_iv", 
                "tag": "test_tag", 
                "payload": "test_payload"
            }, 
            b'test_aes_key'
        )
        
        # Set up a NON-encrypted response (missing iv/tag/payload)
        # This will skip the decryption logic in the client
        non_encrypted_response = {
            "data": execute_response["data"]
        }
        
        schema_data = {"name": "Test User"}
        explicit_ref_id = "explicit_ref_id"
        
        url = urljoin(base_url, "/api/v0/execute/")
        
        mock_responses.add(
            responses.POST,
            url,
            json=non_encrypted_response,
            status=200
        )
        
        result = client.execute_action(schema_data=schema_data, ref_id=explicit_ref_id)
        
        # The result should be the data from execute_response
        assert result == execute_response["data"]
        
        # Verify the correct ref_id was used
        mock_encrypt.assert_called_once()
        args, _ = mock_encrypt.call_args
        payload = args[0]
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
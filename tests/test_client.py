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
        client = LynkrClient(api_key=api_key)
        assert client.api_key == api_key

    def test_init_without_api_key(self, monkeypatch):
        monkeypatch.setenv("LYNKR_API_KEY", "env_api_key")
        client = LynkrClient()
        assert client.api_key == "env_api_key"

    def test_init_missing_api_key(self, monkeypatch):
        monkeypatch.delenv("LYNKR_API_KEY", raising=False)
        with pytest.raises(ValueError) as excinfo:
            LynkrClient()
        assert "API key is required" in str(excinfo.value)

    def test_get_schema(self, client, mock_responses, schema_response, base_url):
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
        with pytest.raises(ValidationError) as excinfo:
            client.get_schema("")
        assert "request_string must be a non-empty string" in str(excinfo.value)

    def test_get_schema_api_error(self, client, mock_responses, base_url):
        request_string = "Create a new user"
        url = urljoin(base_url, "/api/v0/schema/")
        error_response = {"error": "invalid_request", "message": "Invalid request format"}

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
        from lynkr.schema import Schema

        schema = Schema(schema_response["schema"])
        result = client.to_execute_format(schema)

        assert "schema" in result
        assert result["schema"] == schema_response["schema"]

    # @patch('lynkr.client.hybrid_encrypt')
    # @patch('lynkr.client.load_public_key')
    # def test_execute_action(self, mock_load_key, mock_encrypt, client, mock_responses, execute_response, base_url):
    #     # Arrange
    #     client.ref_id = "ref_123456789"
    #     mock_load_key.return_value = MagicMock()
    #     mock_encrypt.return_value = (
    #         {
    #             "encrypted_key": "test_key",
    #             "iv": "test_iv",
    #             "tag": "test_tag",
    #             "payload": "test_payload"
    #         },
    #         b'test_aes_key'
    #     )
    #     non_encrypted = {"data": execute_response["data"]}
    #     url = urljoin(base_url, "/api/v0/execute/")
    #     mock_responses.add(responses.POST, url, json=non_encrypted, status=200)
    #     schema_data = {"name": "Test User"}

    #     # Act
    #     result = client.execute_action(schema_data=schema_data, service="test_service")

    #     # Assert
    #     assert "Result" in result
    #     assert result["Result"] == execute_response["data"]
    #     assert len(mock_responses.calls) == 1

    #     # Verify encryption payload
    #     sent = mock_responses.calls[0].request
    #     payload = json.loads(sent.body)
    #     assert payload["encrypted_key"] == "test_key"
    #     assert payload["iv"] == "test_iv"
    #     assert payload["tag"] == "test_tag"
    #     assert payload["payload"] == "test_payload"

    # @patch('lynkr.client.hybrid_encrypt')
    # @patch('lynkr.client.load_public_key')
    # def test_execute_action_with_explicit_ref_id(self, mock_load_key, mock_encrypt, client, mock_responses, execute_response, base_url):
    #     # Arrange
    #     mock_load_key.return_value = MagicMock()
    #     mock_encrypt.return_value = (
    #         {
    #             "encrypted_key": "test_key",
    #             "iv": "test_iv",
    #             "tag": "test_tag",
    #             "payload": "test_payload"
    #         },
    #         b'test_aes_key'
    #     )
    #     non_encrypted = {"data": execute_response["data"]}
    #     url = urljoin(base_url, "/api/v0/execute/")
    #     mock_responses.add(responses.POST, url, json=non_encrypted, status=200)

    #     schema_data = {"name": "Test User"}
    #     explicit_ref_id = "explicit_ref_id"

    #     # Act
    #     result = client.execute_action(schema_data=schema_data, ref_id=explicit_ref_id, service="test_service")

    #     # Assert
    #     assert "Result" in result
    #     assert result["Result"] == execute_response["data"]
    #     mock_encrypt.assert_called_once()
    #     encrypted_payload, _ = mock_encrypt.call_args[0]
    #     assert encrypted_payload["ref_id"] == explicit_ref_id

    # def test_execute_action_without_ref_id(self, client):
    #     # Arrange
    #     client.ref_id = None
    #     schema_data = {"foo": "bar"}

    #     # Act
    #     result = client.execute_action(schema_data=schema_data, service="any_service")

    #     # Assert
    #     # Now execute_action wraps even the missing-ref error in {"Result": {...}}
    #     assert "Result" in result
    #     assert isinstance(result["Result"], dict)
    #     assert "error" in result["Result"]
    #     assert "ref_id is required to execute an action" in result["Result"]["error"]

    # def test_execute_action_validation_error(self, client):
    #     client.ref_id = "ref_123456789"
    #     # schema_data must be a dict → this will trigger ValidationError inside execute(), caught by execute_action()
    #     result = client.execute_action(schema_data="", service="any_service")
    #     assert result == "Error: schema_data must be a non-empty dictionary"

    # def test_execute_action_merges_service_credentials(self, mock_responses, client, execute_response, base_url):
    #     """Verify that any keys added via add_key are merged into the schema_data."""
    #     # Arrange
    #     client.ref_id = "ref_abc123"
    #     client.add_key("svc", "api_key", "secret_svc_key")
    #     client.add_key("svc", "org_id", "org_987")
    #     # stub encrypt & public key
    #     with patch('lynkr.client.load_public_key') as load_key, \
    #          patch('lynkr.client.hybrid_encrypt') as do_encrypt:
    #         load_key.return_value = MagicMock()
    #         # capture the payload
    #         encrypted_dict = {"enc": "yes"}
    #         do_encrypt.return_value = (encrypted_dict, b"")
    #         url = urljoin(base_url, "/api/v0/execute/")
    #         mock_responses.add(responses.POST, url, json={"data": {}}, status=200)

    #         # Act
    #         client.execute_action(schema_data={"name": "Alice"}, service="svc")

    #         # Assert: hybrid_encrypt was called with the merged schema
    #         payload_arg = do_encrypt.call_args[0][0]
    #         fields = payload_arg["schema"]["fields"]
    #         assert fields["name"]["value"] == "Alice"
    #         assert fields["api_key"]["value"] == "secret_svc_key"
    #         assert fields["org_id"]["value"] == "org_987"

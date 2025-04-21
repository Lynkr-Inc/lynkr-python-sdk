"""
Test fixtures for Lynkr SDK tests.
"""

import json
import pytest
import responses
from lynkr.client import LynkrClient


@pytest.fixture
def api_key():
    """Return a test API key."""
    return "test_api_key_12345"


@pytest.fixture
def base_url():
    """Return a test base URL."""
    return "https://api.lynkr.com"


@pytest.fixture
def client(api_key, base_url):
    """Return a configured client instance."""
    return LynkrClient(api_key=api_key, base_url=base_url)


@pytest.fixture
def mock_responses():
    """Set up mocked API responses."""
    with responses.RequestsMock() as rsps:
        yield rsps


@pytest.fixture
def schema_response():
    """Return a sample schema response."""
    return {
        "ref_id": "ref_123456789",
        "schema": {
            "fields": {
                "name": {
                    "type": "string",
                    "description": "User's full name",
                    "optional": False,
                    "sensitive": False,
                },
            },
            "required_fields": ["name"],
            "optional_fields": [],
            "sensitive_fields": [],
        },
        "metadata": {
            "service": "service_name",
            "resource": "resource_name",
            "method": "POST",
            "confidence": "high",
            "not_found_reason": "null",
        },
    }


@pytest.fixture
def execute_response():
    """Return a sample execute response."""
    return {
        "status": "success",
        "data": {
            "details": {
                "success": True,
                "data": {
                    "id": "fb2644f9-fe14-420e-b4b2-bb20bf240250"
                },
                "error": "null"
            }
        },
        "error": "null"
    }
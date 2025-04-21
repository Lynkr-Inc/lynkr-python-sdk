"""
Test fixtures for Lynkr SDK tests.
"""

import json
import pytest
import responses
from lynkr import Client


@pytest.fixture
def api_key():
    """Return a test API key."""
    return "test_api_key_12345"


@pytest.fixture
def base_url():
    """Return a test base URL."""
    return "http://localhost:8000"


@pytest.fixture
def client(api_key, base_url):
    """Return a configured client instance."""
    return Client(api_key=api_key, base_url=base_url)


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
            "type": "object",
            "required": ["name", "email"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "User's full name"
                },
                "email": {
                    "type": "string",
                    "format": "email",
                    "description": "User's email address"
                },
                "role": {
                    "type": "string",
                    "enum": ["admin", "user", "guest"],
                    "description": "User's role"
                },
                "active": {
                    "type": "boolean",
                    "description": "Whether the user is active"
                }
            }
        }
    }


@pytest.fixture
def execute_response():
    """Return a sample execute response."""
    return {
        "success": True,
        "message": "Action executed successfully",
        "data": {
            "user_id": "usr_987654321",
            "created_at": "2023-04-15T12:30:45Z"
        }
    }
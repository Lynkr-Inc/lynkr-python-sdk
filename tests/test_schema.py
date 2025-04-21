"""
Tests for the Schema class.
"""

import pytest
import json

from lynkr.schema import Schema


class TestSchema:
    """Tests for the Schema class."""

    @pytest.fixture
    def sample_schema(self):
        """Return a sample schema for testing."""
        return {
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
                "age": {
                    "type": "integer",
                    "description": "User's age"
                },
                "active": {
                    "type": "boolean",
                    "description": "Whether the user is active"
                },
                "tags": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    },
                    "description": "User tags"
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata"
                }
            }
        }

    def test_to_dict(self, sample_schema):
        """Test to_dict method."""
        schema = Schema(sample_schema)
        assert schema.to_dict() == sample_schema

    def test_to_json(self, sample_schema):
        """Test to_json method."""
        schema = Schema(sample_schema)
        json_str = schema.to_json(indent=2)
        assert isinstance(json_str, str)
        assert json.loads(json_str) == sample_schema

    def test_get_required_fields(self, sample_schema):
        """Test get_required_fields method."""
        schema = Schema(sample_schema)
        assert schema.get_required_fields() == ["name", "email"]

    def test_get_field_type(self, sample_schema):
        """Test get_field_type method."""
        schema = Schema(sample_schema)
        assert schema.get_field_type("name") == "string"
        assert schema.get_field_type("age") == "integer"
        assert schema.get_field_type("active") == "boolean"
        assert schema.get_field_type("tags") == "array"
        assert schema.get_field_type("metadata") == "object"
        assert schema.get_field_type("nonexistent") is None

    def test_validate_valid_data(self, sample_schema):
        """Test validate method with valid data."""
        schema = Schema(sample_schema)
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "active": True,
            "tags": ["user", "premium"],
            "metadata": {"signup_date": "2023-01-15"}
        }
        errors = schema.validate(data)
        assert errors == []

    def test_validate_missing_required(self, sample_schema):
        """Test validate method with missing required fields."""
        schema = Schema(sample_schema)
        data = {
            "name": "John Doe"
            # Missing email
        }
        errors = schema.validate(data)
        assert len(errors) == 1
        assert "Missing required field: email" in errors

    def test_validate_wrong_types(self, sample_schema):
        """Test validate method with wrong field types."""
        schema = Schema(sample_schema)
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "age": "thirty",  # Should be integer
            "active": "yes",  # Should be boolean
            "tags": "user,premium",  # Should be array
            "metadata": "data"  # Should be object
        }
        errors = schema.validate(data)
        assert len(errors) == 4
        assert any("age" in error for error in errors)
        assert any("active" in error for error in errors)
        assert any("tags" in error for error in errors)
        assert any("metadata" in error for error in errors)
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
            "fields": {
                "name": {
                    "type": "string",
                    "description": "User's full name",
                    "optional": False,
                    "sensitive": False,
                },
                "email": {
                    "type": "string",
                    "description": "User's email address",
                    "optional": False,
                    "sensitive": False,
                },
                "age": {
                    "type": "integer",
                    "description": "User's age",
                    "optional": True,
                    "sensitive": False,
                },
                "active": {
                    "type": "boolean",
                    "description": "Whether the user is active",
                    "optional": True,
                    "sensitive": False,
                },
                "tags": {
                    "type": "array",
                    "description": "User tags",
                    "optional": True,
                    "sensitive": False,
                },
                "metadata": {
                    "type": "object",
                    "description": "Additional metadata",
                    "optional": True,
                    "sensitive": False,
                },
                "password": {
                    "type": "string",
                    "description": "User password",
                    "optional": False,
                    "sensitive": True,
                }
            },
            "required_fields": ["name", "email", "password"],
            "optional_fields": ["age", "active", "tags", "metadata"],
            "sensitive_fields": ["password"]
        }

    def test_init(self, sample_schema):
        """Test initialization."""
        schema = Schema(sample_schema)
        assert schema._schema == sample_schema

    def test_repr(self, sample_schema):
        """Test string representation."""
        schema = Schema(sample_schema)
        assert repr(schema) == f"Schema({sample_schema})"

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
        assert set(schema.get_required_fields()) == set(["name", "email", "password"])

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
            "password": "securepass123",
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
            "name": "John Doe",
            # Missing email and password
        }
        errors = schema.validate(data)
        assert len(errors) == 2
        assert any("email" in error for error in errors)
        assert any("password" in error for error in errors)

    def test_validate_wrong_types(self, sample_schema):
        """Test validate method with wrong field types."""
        schema = Schema(sample_schema)
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepass123",
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

    def test_validate_empty_data(self, sample_schema):
        """Test validate method with empty data."""
        schema = Schema(sample_schema)
        data = {}
        errors = schema.validate(data)
        assert len(errors) == 3  # Missing name, email, password
        assert any("name" in error for error in errors)
        assert any("email" in error for error in errors)
        assert any("password" in error for error in errors)

    def test_validate_extra_fields(self, sample_schema):
        """Test validate with extra fields not in schema."""
        schema = Schema(sample_schema)
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "password": "securepass123",
            "extra_field": "value"  # Not in schema
        }
        errors = schema.validate(data)
        assert errors == []  # Extra fields are allowed

    def test_is_sensitive_field(self, sample_schema):
        """Test checking if a field is sensitive."""
        schema = Schema(sample_schema)
        assert schema.is_sensitive_field("password") is True
        assert schema.is_sensitive_field("name") is False
        assert schema.is_sensitive_field("nonexistent") is False

    def test_is_optional_field(self, sample_schema):
        """Test checking if a field is optional."""
        schema = Schema(sample_schema)
        assert schema.is_optional_field("age") is True
        assert schema.is_optional_field("name") is False
        assert schema.is_optional_field("nonexistent") is False
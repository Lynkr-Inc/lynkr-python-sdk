"""
Schema handling for Lynkr SDK.
"""

import typing as t
import json


class Schema:
    """
    Represents a schema returned by the API.
    
    Provides helper methods to work with schema data.
    """
    
    def __init__(self, schema_data: t.Dict[str, t.Any]):
        self._schema = schema_data
    
    def __repr__(self) -> str:
        """String representation of the schema."""
        return f"Schema({self._schema})"
    
    def to_dict(self) -> t.Dict[str, t.Any]:
        """
        Convert schema to dictionary.
        
        Returns:
            Dict representation of the schema
        """
        return self._schema
    
    def to_json(self, indent: int = 2) -> str:
        """
        Convert schema to JSON string.
        
        Args:
            indent: Number of spaces for indentation
            
        Returns:
            JSON string representation of the schema
        """
        return json.dumps(self._schema, indent=indent)
    
    def get_required_fields(self) -> t.List[str]:
        """
        Get list of required fields from the schema.
        
        Returns:
            List of required field names
        """
        return self._schema.get("required_fields", [])
    
    def get_field_type(self, field_name: str) -> t.Optional[str]:
        """
        Get type of a specified field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Type of the field or None if field not found
        """
        fields = self._schema.get("fields", {})
        field = fields.get(field_name, {})
        return field.get("type")
    
    def is_sensitive_field(self, field_name: str) -> bool:
        """
        Check if a field is marked as sensitive.
        
        Args:
            field_name: Name of the field
            
        Returns:
            True if field is sensitive, False otherwise
        """
        sensitive_fields = self._schema.get("sensitive_fields", [])
        return field_name in sensitive_fields
    
    def is_optional_field(self, field_name: str) -> bool:
        """
        Check if a field is optional.
        
        Args:
            field_name: Name of the field
            
        Returns:
            True if field is optional, False otherwise
        """
        optional_fields = self._schema.get("optional_fields", [])
        return field_name in optional_fields
    
    def validate(self, data: t.Dict[str, t.Any]) -> t.List[str]:
        """
        Validate data against the schema.
        
        Args:
            data: Data to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check required fields
        for field in self.get_required_fields():
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        # Validate field types
        fields = self._schema.get("fields", {})
        for field_name, field_value in data.items():
            if field_name in fields:
                field_schema = fields[field_name]
                field_type = field_schema.get("type")
                
                # Basic type validation
                if field_type == "string" and not isinstance(field_value, str):
                    errors.append(f"Field '{field_name}' must be a string")
                elif field_type == "number" and not isinstance(field_value, (int, float)):
                    errors.append(f"Field '{field_name}' must be a number")
                elif field_type == "integer" and not isinstance(field_value, int):
                    errors.append(f"Field '{field_name}' must be an integer")
                elif field_type == "boolean" and not isinstance(field_value, bool):
                    errors.append(f"Field '{field_name}' must be a boolean")
                elif field_type == "array" and not isinstance(field_value, list):
                    errors.append(f"Field '{field_name}' must be an array")
                elif field_type == "object" and not isinstance(field_value, dict):
                    errors.append(f"Field '{field_name}' must be an object")
        
        return errors
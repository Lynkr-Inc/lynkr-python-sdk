"""
API key management for Lynkr SDK.
"""

import typing as t


class KeyManager:
    """
    Manages API keys for different services.
    
    This class provides methods to store, retrieve, and manage API keys
    that can be automatically used when executing actions.
    """
    
    def __init__(self):
        self._keys = {}
        self._key_to_field_mapping = {
            # Default mappings for common services
            "resend": ["x-api-key", "api_key", "apikey", "resend_api_key"],
            "openai": ["openai_api_key", "api_key", "openai_key"],
            "wealthsimple": ["access_token", "auth_token", "wealthsimple_api_key"],
            "stripe": ["stripe_api_key", "stripe_secret_key", "api_key"],
            "twilio": ["twilio_auth_token", "auth_token", "twilio_api_key"],
            "sendgrid": ["sendgrid_api_key", "api_key"],
            # Add more mappings as needed
        }
    
    def add(self, name: str, value: str, field_names: t.Optional[t.List[str]] = None) -> None:
        """
        Add a new API key.
        
        Args:
            name: Name/identifier for the key (e.g., "resend", "openai")
            value: The API key value
            field_names: Optional list of field names this key should match in schemas
                         If not provided, will use default mappings if available
        """
        # Store keys in lowercase for case-insensitive matching
        name = name.lower()
        self._keys[name] = value
        
        # If field_names are provided, update the mapping
        if field_names:
            self._key_to_field_mapping[name] = field_names
    
    def get(self, name: str) -> t.Optional[str]:
        """
        Get an API key by name.
        
        Args:
            name: Name/identifier of the key
            
        Returns:
            The API key value or None if not found
        """
        return self._keys.get(name.lower())
    
    def remove(self, name: str) -> bool:
        """
        Remove an API key.
        
        Args:
            name: Name/identifier of the key
            
        Returns:
            True if the key was removed, False if not found
        """
        name = name.lower()
        if name in self._keys:
            del self._keys[name]
            return True
        return False
    
    def list(self) -> t.Dict[str, str]:
        """
        List all stored API keys.
        
        Returns:
            Dictionary of key names and values (with values partially masked)
        """
        # Return a copy with masked values for security
        return {k: self._mask_key(v) for k, v in self._keys.items()}
    
    def _mask_key(self, key_value: str) -> str:
        """Mask API key for secure display."""
        if not key_value:
            return "****"
        if len(key_value) <= 8:
            return "****"
        return f"{key_value[:4]}...{key_value[-4:]}"
    
    def get_field_mappings(self, name: str) -> t.List[str]:
        """
        Get the field names that a key can map to in schemas.
        
        Args:
            name: Name/identifier of the key
            
        Returns:
            List of field names or empty list if no mappings found
        """
        return self._key_to_field_mapping.get(name.lower(), [])
    
    def match_keys_to_schema(self, schema_data: t.Dict[str, t.Any], 
                           required_fields: t.List[str]) -> t.Dict[str, t.Any]:
        """
        Match stored API keys to schema fields.
        
        This method attempts to fill in any missing required fields in the schema data
        with appropriate API keys from the store.
        
        Args:
            schema_data: Current schema data (may be partially filled)
            required_fields: List of required field names from the schema
            
        Returns:
            Updated schema data with API keys filled in where appropriate
        """
        # Create a copy to avoid modifying the original
        updated_data = schema_data.copy()
        
        # Track which fields still need to be filled
        missing_fields = [field for field in required_fields if field not in updated_data]
        
        # Try to match each key to missing fields
        for key_name, key_value in self._keys.items():
            field_mappings = self.get_field_mappings(key_name)
            
            for field_name in field_mappings:
                # If this field is required and missing, fill it with the key
                if field_name in missing_fields:
                    updated_data[field_name] = key_value
                    missing_fields.remove(field_name)
                    break  # One key should only fill one field
            
            # Also check if any missing fields match the key name directly
            # This helps with fields that might be named exactly after the service
            if key_name in missing_fields:
                updated_data[key_name] = key_value
                missing_fields.remove(key_name)
            
            # Check for fields that contain the key name (e.g., "resend_api_key")
            for field in missing_fields[:]:  # Use a copy for safe iteration while removing
                if key_name in field.lower() and ("key" in field.lower() or "token" in field.lower() or "auth" in field.lower()):
                    updated_data[field] = key_value
                    missing_fields.remove(field)
        
        return updated_data

    def __contains__(self, name: str) -> bool:
        """
        Check if a key exists by name.
        
        Args:
            name: Name/identifier of the key
            
        Returns:
            True if the key exists, False otherwise
        """
        return name.lower() in self._keys
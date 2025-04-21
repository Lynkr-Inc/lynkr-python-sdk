"""
Validation utilities for Lynkr SDK.
"""

import typing as t
import re

from ..exceptions import ValidationError


def validate_api_key(api_key: str) -> None:
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        
    Raises:
        ValidationError: If API key is invalid
    """
    if not api_key:
        raise ValidationError("API key cannot be empty")
        
    if not isinstance(api_key, str):
        raise ValidationError("API key must be a string")


def validate_ref_id(ref_id: str) -> None:
    """
    Validate reference ID format.
    
    Args:
        ref_id: Reference ID to validate
        
    Raises:
        ValidationError: If reference ID is invalid
    """
    if not ref_id:
        raise ValidationError("Reference ID cannot be empty")
        
    if not isinstance(ref_id, str):
        raise ValidationError("Reference ID must be a string")
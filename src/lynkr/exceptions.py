"""
Custom exceptions for Lynkr SDK.
"""

class ApiError(Exception):
    """
    Raised when the API returns an error response.
    """
    
    def __init__(self, message, status_code=None, response=None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response
        self.message = message
    
    def __str__(self):
        if self.status_code:
            return f"API Error ({self.status_code}): {self.message}"
        return f"API Error: {self.message}"


class ValidationError(Exception):
    """
    Raised when input validation fails.
    """
    
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.message = message
        self.errors = errors or []
    
    def __str__(self):
        if self.errors:
            return f"Validation Error: {self.message} - {', '.join(self.errors)}"
        return f"Validation Error: {self.message}"


class ConfigurationError(Exception):
    """
    Raised when the SDK is improperly configured.
    """
    pass
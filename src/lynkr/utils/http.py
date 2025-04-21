"""
HTTP client for making API requests.
"""

import typing as t
import requests
from requests.exceptions import RequestException, Timeout

from ..exceptions import ApiError


class HttpClient:
    """
    HTTP client for making API requests.
    
    Handles request/response cycle, error handling, and timeout.
    """
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
    
    def get(
        self, 
        url: str, 
        headers: t.Dict[str, str] = None, 
        params: t.Dict[str, t.Any] = None
    ) -> t.Dict[str, t.Any]:
        """
        Make a GET request.
        
        Args:
            url: Request URL
            headers: Request headers
            params: Query parameters
            
        Returns:
            Response as dictionary
            
        Raises:
            ApiError: If the request fails
        """
        return self._request("GET", url, headers=headers, params=params)
    
    def post(
        self, 
        url: str, 
        headers: t.Dict[str, str] = None, 
        json: t.Dict[str, t.Any] = None,
        data: t.Any = None
    ) -> t.Dict[str, t.Any]:
        """
        Make a POST request.
        
        Args:
            url: Request URL
            headers: Request headers
            json: JSON body
            data: Form data
            
        Returns:
            Response as dictionary
            
        Raises:
            ApiError: If the request fails
        """
        return self._request("POST", url, headers=headers, json=json, data=data)
    
    def _request(
        self, 
        method: str, 
        url: str,
        headers: t.Dict[str, str] = None,
        params: t.Dict[str, t.Any] = None,
        json: t.Dict[str, t.Any] = None,
        data: t.Any = None
    ) -> t.Dict[str, t.Any]:
        """
        Make a HTTP request.
        
        Args:
            method: HTTP method
            url: Request URL
            headers: Request headers
            params: Query parameters
            json: JSON body
            data: Form data
            
        Returns:
            Response as dictionary
            
        Raises:
            ApiError: If the request fails
        """
        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
                data=data,
                timeout=self.timeout
            )
            
            # Raise error for non-2xx status codes
            response.raise_for_status()
            
            # Parse JSON response
            try:
                return response.json()
            except ValueError:
                raise ApiError(f"Invalid JSON response: {response.text}")
                
        except Timeout:
            raise ApiError(f"Request timed out after {self.timeout} seconds")
            
        except RequestException as e:
            if hasattr(e, "response") and e.response is not None:
                status_code = e.response.status_code
                try:
                    error_detail = e.response.json()
                except ValueError:
                    error_detail = e.response.text
                    
                error_message = error_detail.get("message", str(e)) if isinstance(error_detail, dict) else str(e)
                raise ApiError(error_message, status_code=status_code, response=error_detail)
            else:
                raise ApiError(f"Request failed: {str(e)}")

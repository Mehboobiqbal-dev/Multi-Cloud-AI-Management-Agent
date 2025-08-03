import requests
from typing import Dict, Optional

def call_api(url: str, method: str = 'GET', data: Optional[Dict] = None, headers: Optional[Dict] = None) -> str:
    """Makes a dynamic API call with the specified method, data, and headers."""
    try:
        response = requests.request(method.upper(), url, json=data, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        return f"API call error: {str(e)}"
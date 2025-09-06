"""
OpenAI error mapper helpers - MVP stub.
"""
from typing import Dict, Any

def map_to_openai_error(error: Exception) -> Dict[str, Any]:
    """
    Map internal errors to OpenAI-style error format.
    
    Args:
        error: Internal exception
        
    Returns:
        OpenAI-style error dictionary
    """
    return {
        "message": "Internal Server Error",
        "type": "internal_server_error", 
        "param": None,
        "code": None
    }

from typing import Dict, Any


def sanitize_payload(body: Dict[str, Any]) -> Dict[str, Any]:
    """Remove unsupported parameters for gpt-5 and ensure model is gpt-5."""
    # Force model to be gpt-5
    body["model"] = "gpt-5"
    
    # Remove unsupported parameters for gpt-5
    for field in ["temperature", "top_p", "presence_penalty", "frequency_penalty"]:
        body.pop(field, None)
    
    # Replace max_tokens with max_completion_tokens for gpt-5
    if "max_tokens" in body:
        body["max_completion_tokens"] = body.pop("max_tokens")
    
    return body
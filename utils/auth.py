from typing import Optional, Dict, Any
from fastapi import Request, HTTPException
from core.config import config


def normalize_bearer(value: Optional[str]) -> Optional[str]:
    """Normalize API key to Bearer token format."""
    if not value:
        return None
    value = value.strip()
    return value if value.lower().startswith("bearer ") else f"Bearer {value}"


def resolve_auth(request: Request, provided: Optional[str], body: Optional[Dict[str, Any]] = None) -> str:
    """Resolve authentication token from various sources."""
    # 1. Explicitly provided in header
    if provided:
        return normalize_bearer(provided)
    
    # 2. Check request headers
    for key in ["authorization", "x-openai-api-key", "openai-api-key", "x-api-key"]:
        if key in request.headers:
            return normalize_bearer(request.headers[key])
    
    # 3. Check request body
    if body:
        for k in ["api_key", "openai_api_key", "key", "token"]:
            if k in body:
                return normalize_bearer(str(body[k]))
    
    # 4. Fallback to environment variable
    if config.openai_api_key:
        return normalize_bearer(config.openai_api_key)
    
    raise HTTPException(status_code=401, detail="Missing API key")

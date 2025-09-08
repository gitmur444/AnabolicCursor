"""
Common HTTP utilities for proxy requests.
"""
import httpx
from fastapi import HTTPException
from typing import Dict, Any, Optional

from utils.logging_utils import log_event
from utils.retry_utils import should_retry_status, log_and_wait_retry, RETRY_MAX


async def handle_error_response(response: httpx.Response) -> None:
    """Handle HTTP error responses with logging."""
    req_id = response.headers.get("x-request-id")
    
    if response.status_code >= 400:
        log_event("error", {
            "status": response.status_code, 
            "body": response.text, 
            "openai_request_id": req_id
        })
        raise HTTPException(status_code=response.status_code, detail=response.text)


async def handle_retryable_error(response: httpx.Response, attempt: int) -> bool:
    """Handle retryable errors. Returns True if should retry, False if exhausted."""
    if not should_retry_status(response.status_code):
        return False
        
    req_id = response.headers.get("x-request-id")
    body_text = response.text or ""
    
    if await log_and_wait_retry(response.status_code, attempt, response.headers, body_text, req_id):
        return True  # should retry
    
    # попытки исчерпаны — логим ошибку и падаем
    log_event("error", {
        "status": response.status_code, 
        "body": body_text, 
        "openai_request_id": req_id
    })
    raise HTTPException(status_code=response.status_code, detail=body_text)


def extract_openai_headers(response: httpx.Response) -> Dict[str, Optional[str]]:
    """Extract OpenAI specific headers for logging."""
    return {
        "req_id": response.headers.get("x-request-id"),
        "processing_ms": response.headers.get("openai-processing-ms")
    }



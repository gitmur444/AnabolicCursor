"""
Response logging utilities for proxy requests.
"""
import json
import time
from typing import Dict, Any, Optional, List

from core.config import config
from utils.logging_utils import log_event
from parsers.response_parser import extract_tool_calls_from_response, extract_choices_details


def log_response_event(
    payload: Dict[str, Any], 
    response_data: Optional[Dict[str, Any]] = None,
    content_text: str = "",
    usage: Optional[Dict] = None,
    finish_reason: Optional[str] = None,
    has_tool_calls: bool = False,
    tool_calls: Optional[List] = None,
    streaming: bool = False,
    content_length: int = 0,
    truncated: bool = False,
    req_id: Optional[str] = None,
    processing_ms: Optional[str] = None,
    cancelled_by_client: bool = False
) -> None:
    """Log response event with consistent format."""
    
    response_log = {
        "model": payload.get("model"),
        "streaming": streaming,
        "cancelled_by_client": cancelled_by_client,
        "content_length": content_length,
        "truncated": truncated,
    }
    
    # Add OpenAI headers if available
    if req_id:
        response_log["openai_request_id"] = req_id
    if processing_ms:
        response_log["openai_processing_ms"] = processing_ms
    
    # Add response content
    if response_data:
        response_log.update({
            "response_id": response_data.get("id"),
            "object_type": response_data.get("object"),
            "content_text": json.dumps(response_data, ensure_ascii=False),
        })
        
        # Extract additional info from response
        has_tool_calls, tool_calls, finish_reason = extract_tool_calls_from_response(response_data)
        choices_details = extract_choices_details(response_data)
        
        response_log.update({
            "usage": response_data.get("usage"),
            "finish_reason": finish_reason,
            "has_tool_calls": has_tool_calls,
            "tool_calls": tool_calls if tool_calls else None,
            "choices_count": len(response_data.get("choices", [])),
            "choices_details": choices_details,
        })
    else:
        # For streaming responses
        response_log.update({
            "content_text": content_text,
            "usage": usage,
            "finish_reason": finish_reason,
            "has_tool_calls": has_tool_calls,
            "tool_calls": tool_calls if tool_calls else None,
        })
    
    log_event("response", response_log)


def prepare_streaming_text_for_log(full_text: str, max_log_text: Optional[int] = None) -> tuple[str, bool]:
    """Prepare streaming text for logging with truncation if needed."""
    if max_log_text is None:
        max_log_text = config.max_log_text
        
    truncated = False
    logged_text = full_text
    
    if max_log_text and isinstance(max_log_text, int) and len(full_text) > max_log_text:
        logged_text = full_text[:max_log_text]
        truncated = True
        
    return logged_text, truncated

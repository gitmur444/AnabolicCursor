"""
Response parsing utilities for OpenAI API responses.
"""
import json
from typing import Dict, Any, List, Tuple, Optional


def extract_tool_calls_from_response(data: Dict[str, Any]) -> Tuple[bool, List[Dict], Optional[str]]:
    """Extract tool calls information from OpenAI API response."""
    has_tool_calls = False
    finish_reason = None
    tool_calls_info = []
    
    if "choices" in data and len(data["choices"]) > 0:
        choice = data["choices"][0]
        finish_reason = choice.get("finish_reason")
        message = choice.get("message", {})
        
        # Extract tool calls information
        if message.get("tool_calls"):
            has_tool_calls = True
            for tool_call in message["tool_calls"]:
                tool_calls_info.append({
                    "id": tool_call.get("id"),
                    "type": tool_call.get("type"),
                    "function_name": tool_call.get("function", {}).get("name"),
                    "function_args": tool_call.get("function", {}).get("arguments")
                })
        elif message.get("function_call"):
            has_tool_calls = True
            tool_calls_info.append({
                "type": "function_call",
                "function_name": message["function_call"].get("name"),
                "function_args": message["function_call"].get("arguments")
            })
    
    return has_tool_calls, tool_calls_info, finish_reason


def extract_choices_details(data: Dict[str, Any]) -> List[Dict]:
    """Extract detailed information about all choices in the response."""
    choices_details = []
    
    if "choices" in data and len(data["choices"]) > 0:
        for i, choice in enumerate(data["choices"]):
            choice_info = {
                "index": choice.get("index", i),
                "finish_reason": choice.get("finish_reason"),
                "has_content": bool(choice.get("message", {}).get("content")),
                "has_tool_calls": bool(choice.get("message", {}).get("tool_calls")),
                "content_length": len(choice.get("message", {}).get("content") or "")
            }
            choices_details.append(choice_info)
    
    return choices_details


def extract_text_from_streaming_chunk(obj: Dict[str, Any], current_event: Optional[str] = None) -> Optional[str]:
    """Extract text content from a streaming response chunk."""
    piece = None
    
    # 1) OpenAI Chat Completions (SSE): choices[0].delta.content
    if "choices" in obj and obj["choices"]:
        delta = (obj["choices"][0] or {}).get("delta", {})
        if isinstance(delta, dict) and isinstance(delta.get("content"), str):
            piece = delta["content"]
    
    # 2) Responses API / Unified streaming (разные типы событий)
    if piece is None:
        t = obj.get("type") or current_event
        if t in {"response.output_text.delta", "output_text.delta", "message.delta", "response.delta"}:
            d = obj.get("delta")
            if isinstance(d, str):
                piece = d
            elif isinstance(d, dict):
                piece = d.get("text") or d.get("output_text") or ""
    
    return piece


def extract_tool_calls_from_streaming_chunk(obj: Dict[str, Any]) -> List[Dict]:
    """Extract tool calls from streaming response chunk."""
    tool_calls_info = []
    
    try:
        choices = obj.get("choices", [])
        if not choices:
            return tool_calls_info
        ch0 = choices[0] or {}
        delta = ch0.get("delta", {})
        if delta.get("tool_calls"):
            for tool_call in delta["tool_calls"]:
                tool_calls_info.append({
                    "id": tool_call.get("id"),
                    "index": tool_call.get("index"),
                    "type": tool_call.get("type"),
                    "function_name": tool_call.get("function", {}).get("name"),
                    "function_args": tool_call.get("function", {}).get("arguments")
                })
    except Exception:
        pass
    
    return tool_calls_info


def extract_finish_reason_from_chunk(obj: Dict[str, Any]) -> Optional[str]:
    """Extract finish_reason from streaming chunk."""
    try:
        choices = obj.get("choices", [])
        if not choices:
            return None
        ch0 = choices[0] or {}
        return ch0.get("finish_reason")
    except Exception:
        return None

"""
Logging utilities for the Cursor Proxy application.
"""
import os
import time
import json
import logging
from typing import Dict


def setup_logging():
    """Setup logging configuration for the application."""
    os.makedirs("logs", exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        handlers=[
            logging.FileHandler("logs/proxy.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )
    
    # Reduce httpx/httpcore noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return logging.getLogger("cursor-proxy")


logger = setup_logging()


def _format_multiline_field(line: str, field: str) -> str:
    """Format a single line containing multiline field content."""
    before_field, after_field = line.split(field + ' "', 1)
    field_value, after_value = after_field.rsplit('"', 1)
    
    # Calculate indentation: spaces before field + 2 more for alignment
    base_spaces = len(before_field.replace('\t', '    '))
    indent_str = ' ' * (base_spaces + 2)
    
    # Split by \\n and join with proper indentation
    content_parts = field_value.split('\\n')
    formatted_content = content_parts[0]
    for part in content_parts[1:]:
        formatted_content += '\n' + indent_str + part
    
    return before_field + field + ' "' + formatted_content + '"' + after_value


def log_event(event_type: str, data: dict):
    """Log structured events as JSON with pretty formatting and readable newlines."""
    event = {
        "event": event_type,
        "timestamp": int(time.time()),
        "data": data,
    }
    
    json_str = json.dumps(event, ensure_ascii=False, indent=2)
    lines = json_str.split('\n')
    
    multiline_fields = ['"content":', '"description":', '"content_text":']
    result_lines = []
    
    for line in lines:
        field_found = None
        for field in multiline_fields:
            if '\\n' in line and field in line:
                field_found = field
                break
        
        if field_found:
            result_lines.append(_format_multiline_field(line, field_found))
        else:
            result_lines.append(line.replace('\\n', '\n'))
    
    logger.info('\n'.join(result_lines))


def redact_token(tok: str) -> str:
    """Redact API tokens for logging, keeping only first 6 and last 4 characters."""
    if not tok:
        return tok
    t = tok.replace("Bearer ", "").replace("bearer ", "").strip()
    if len(t) <= 10:
        return "Bearer ****"
    return f"Bearer {t[:6]}…{t[-4:]}"


def redact_headers(h: Dict[str, str]) -> Dict[str, str]:
    """Redact sensitive headers for safe logging."""
    if not h:
        return h
    safe = dict(h)
    for k in list(safe.keys()):
        kl = k.lower()
        if kl in ("authorization", "x-openai-api-key", "openai-api-key", "x-api-key"):
            safe[k] = redact_token(str(safe[k]))
    return safe
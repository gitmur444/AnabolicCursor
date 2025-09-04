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


def log_event(event_type: str, data: dict):
    """Log structured events as JSON with pretty formatting and readable newlines."""
    event = {
        "event": event_type,
        "timestamp": int(time.time()),
        "data": data,
    }
    
    # Convert to JSON with pretty formatting
    json_str = json.dumps(event, ensure_ascii=False, indent=2)
    
    # Replace \\n with actual newlines while preserving indentation
    lines = json_str.split('\n')
    result_lines = []
    
    for line in lines:
        if '\\n' in line and '"content":' in line:
            # This is a content line with escaped newlines
            # Find the indentation by looking at spaces before the content value
            before_content, after_content = line.split('"content": "', 1)
            content_value, after_value = after_content.rsplit('"', 1)
            
            # Calculate indentation: just the spaces before "content" + 2 more spaces for alignment
            base_spaces = len(before_content.replace('\t', '    '))  # Convert tabs to spaces
            indent_str = ' ' * (base_spaces + 2)  # +2 for nice alignment under the opening quote
            
            # Split content by \\n and join with proper indentation
            content_parts = content_value.split('\\n')
            formatted_content = content_parts[0]  # First line as-is
            for part in content_parts[1:]:
                formatted_content += '\n' + indent_str + part
            
            # Reconstruct the line
            new_line = before_content + '"content": "' + formatted_content + '"' + after_value
            result_lines.append(new_line)
        else:
            # Regular line or content without \\n - just replace \\n normally
            result_lines.append(line.replace('\\n', '\n'))
    
    formatted_log = '\n'.join(result_lines)
    logger.info(formatted_log)


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
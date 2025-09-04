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
    
    # Replace \\n with actual newlines for better readability in content fields
    formatted_log = json_str.replace('\\n', '\n')
    
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
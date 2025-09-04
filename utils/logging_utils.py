import os
import time
import json
import logging
from typing import Dict


def setup_logging():
    """Setup logging configuration for the proxy application."""
    os.makedirs("logs", exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,  # INFO вместо DEBUG
        format="%(message)s",  # пишем только JSON, без префиксов
        handlers=[
            logging.FileHandler("logs/proxy.log", encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    
    # подавляем шум от httpx и httpcore
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    return logging.getLogger("cursor-proxy")


logger = setup_logging()


def log_event(event_type: str, data: dict):
    """Log structured events as JSON with pretty formatting."""
    event = {
        "event": event_type,
        "timestamp": int(time.time()),
        "data": data,
    }
    # Форматируем JSON красиво с отступами
    logger.info(json.dumps(event, ensure_ascii=False, indent=2))


def redact_token(tok: str) -> str:
    """Redact API tokens for logging, keeping only first 6 and last 4 characters."""
    if not tok:
        return tok
    t = tok.replace("Bearer ", "").replace("bearer ", "").strip()
    if len(t) <= 10:
        return "Bearer ****"
    return f"Bearer {t[:6]}…{t[-4:]}"


def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
    """Redact sensitive headers for safe logging."""
    if not headers:
        return headers
    safe = dict(headers)
    for k in list(safe.keys()):
        kl = k.lower()
        if kl in ("authorization", "x-openai-api-key", "openai-api-key", "x-api-key"):
            safe[k] = redact_token(str(safe[k]))
    return safe

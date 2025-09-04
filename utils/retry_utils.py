"""
Retry utilities for handling rate limits and temporary errors from OpenAI API.
"""
import os
import re
import random
import asyncio
from typing import Dict

from utils.logging_utils import log_event

# Configuration from environment
RETRY_MAX = int(os.getenv("RETRY_MAX", "3"))
RETRY_BASE_SECONDS = float(os.getenv("RETRY_BASE_SECONDS", "1.5"))
RETRY_MAX_SECONDS = float(os.getenv("RETRY_MAX_SECONDS", "20"))


def should_retry_status(status: int) -> bool:
    """Check if HTTP status code indicates a retryable error."""
    # 429 (rate limit) и временные ошибки апстрима
    return status in (429, 500, 502, 503, 504)


def parse_retry_after(headers: Dict[str, str], body_text: str) -> float:
    """Parse retry delay from response headers and body."""
    # 1) стандартный Retry-After
    ra = headers.get("retry-after") or headers.get("Retry-After")
    if ra:
        try:
            return float(ra)
        except Exception:
            pass
    
    # 2) заголовки OpenAI про reset временных квот
    for k in (
        "x-ratelimit-reset-tokens",
        "x-ratelimit-reset-requests", 
        "X-RateLimit-Reset-Tokens",
        "X-RateLimit-Reset-Requests",
    ):
        v = headers.get(k)
        if v:
            try:
                return float(v)
            except Exception:
                pass
    
    # 3) парс текста ошибки: "Please try again in 6.13s"
    m = re.search(r"try again in ([0-9.]+)s", body_text or "", re.IGNORECASE)
    if m:
        try:
            return float(m.group(1))
        except Exception:
            pass
    
    return 0.0


def compute_backoff(attempt: int, suggested: float) -> float:
    """Compute backoff delay with exponential backoff and jitter."""
    base = suggested if suggested and suggested > 0 else (RETRY_BASE_SECONDS * (2 ** attempt))
    jitter = base * 0.2 * random.random()
    wait = min(base + jitter, RETRY_MAX_SECONDS)
    return max(wait, 0.25)


async def log_and_wait_retry(status: int, attempt: int, headers: Dict[str, str], body_text: str, req_id: str = None) -> bool:
    """Log retry attempt and wait if needed. Returns True if should retry, False if exhausted."""
    wait_s = compute_backoff(attempt, parse_retry_after(headers, body_text))
    will_retry = attempt < RETRY_MAX
    
    log_event("retry_scheduled", {
        "status": status,
        "attempt": attempt + 1,
        "will_retry": will_retry,
        "wait_seconds": round(wait_s, 2),
        "openai_request_id": req_id,
        "retry_reason": "rate_limit" if status == 429 else "server_error",
    })
    
    if will_retry:
        await asyncio.sleep(wait_s)
        return True
    
    return False

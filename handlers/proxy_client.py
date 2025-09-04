"""
Refactored proxy client with modular structure.
"""
import time
import json
import asyncio
from typing import Dict, Any, List

import httpx
from fastapi import HTTPException

from core.config import config
from utils.logging_utils import log_event, redact_headers
from utils.retry_utils import should_retry_status, log_and_wait_retry, RETRY_MAX
from parsers.response_parser import (
    extract_text_from_streaming_chunk,
    extract_tool_calls_from_streaming_chunk,
    extract_finish_reason_from_chunk
)
from parsers.response_logger import log_response_event, prepare_streaming_text_for_log
from utils.http_utils import extract_openai_headers


async def proxy_json(url: str, headers: Dict[str, str], payload: Dict[str, Any]):
    """Proxy non-streaming requests to OpenAI API with detailed logging."""
    log_event("forwarded_request", {"url": url, "headers": redact_headers(headers), "payload": payload})

    async with httpx.AsyncClient(timeout=None) as client:
        for attempt in range(RETRY_MAX + 1):
            r = await client.post(url, headers=headers, json=payload)
            openai_headers = extract_openai_headers(r)

            # Handle retryable errors (429, 5xx)
            if should_retry_status(r.status_code):
                body_text = r.text or ""
                if await log_and_wait_retry(r.status_code, attempt, r.headers, body_text, openai_headers["req_id"]):
                    continue  # retry
                # Attempts exhausted
                log_event("error", {"status": r.status_code, "body": body_text, "openai_request_id": openai_headers["req_id"]})
                raise HTTPException(status_code=r.status_code, detail=body_text)

            if r.status_code >= 400:
                log_event("error", {"status": r.status_code, "body": r.text, "openai_request_id": openai_headers["req_id"]})
                raise HTTPException(status_code=r.status_code, detail=r.text)

            # Success - parse and log response
            data = r.json()
            
            log_response_event(
                payload=payload,
                response_data=data,
                streaming=False,
                req_id=openai_headers["req_id"],
                processing_ms=openai_headers["processing_ms"]
            )
            
            return data


async def proxy_stream(url: str, headers: Dict[str, str], payload: Dict[str, Any]):
    """Proxy streaming requests to OpenAI API with detailed logging."""
    
    # Accumulators for final logging
    full_text_parts: List[str] = []
    usage = None
    finish_reason = None
    current_event = None
    tool_calls_info = []
    cancelled_by_client = False
    req_id = None
    processing_ms = None

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            attempt = 0
            while attempt <= RETRY_MAX:
                try:
                    async with client.stream("POST", url, headers=headers, json=payload) as r:
                        # Handle retryable errors (429, 5xx) 
                        if should_retry_status(r.status_code):
                            text = await r.aread()
                            body_text = text.decode(errors="ignore")
                            if await log_and_wait_retry(r.status_code, attempt, r.headers, body_text, r.headers.get("x-request-id")):
                                attempt += 1
                                continue  # retry
                            log_event("error", {"status": r.status_code, "body": body_text})
                            raise HTTPException(status_code=r.status_code, detail=body_text)

                        if r.status_code >= 400:
                            text = await r.aread()
                            body_text = text.decode(errors="ignore")
                            log_event("error", {"status": r.status_code, "body": body_text})
                            raise HTTPException(status_code=r.status_code, detail=body_text)

                        # Success - extract headers and process stream
                        openai_headers = extract_openai_headers(r)
                        req_id = openai_headers["req_id"]
                        processing_ms = openai_headers["processing_ms"]

                        async for raw_line in r.aiter_lines():
                            if not raw_line:
                                continue
                            line = raw_line.strip()

                            # SSE protocol handling
                            if line.startswith(":"):
                                continue
                            if line.startswith("event:"):
                                current_event = line.split("event:", 1)[1].strip()
                                continue
                            if not line.startswith("data:"):
                                yield raw_line + "\n"
                                continue

                            data_str = line[5:].strip()  # after 'data:'
                            if data_str == "[DONE]":
                                break

                            # Parse JSON chunk
                            try:
                                obj = json.loads(data_str)
                            except Exception:
                                yield raw_line + "\n"
                                continue

                            # Extract usage if present
                            if usage is None and "usage" in obj:
                                usage = obj["usage"]

                            # Extract finish_reason
                            chunk_finish_reason = extract_finish_reason_from_chunk(obj)
                            if chunk_finish_reason:
                                finish_reason = chunk_finish_reason
                            
                            # Extract tool calls from streaming chunks
                            chunk_tool_calls = extract_tool_calls_from_streaming_chunk(obj)
                            tool_calls_info.extend(chunk_tool_calls)

                            # Extract text content
                            piece = extract_text_from_streaming_chunk(obj, current_event)
                            if piece:
                                full_text_parts.append(piece)

                            # Forward the chunk to client
                            yield raw_line + "\n"
                        
                        # Normal completion - exit retry loop
                        return
                        
                except (httpx.StreamClosed, httpx.ReadError, httpx.RemoteProtocolError) as e:
                    # Network errors during stream reading - retry if possible
                    if attempt < RETRY_MAX:
                        log_event("stream_error_retry", {
                            "error": str(e), 
                            "attempt": attempt + 1,
                            "will_retry": True
                        })
                        attempt += 1
                        continue
                    else:
                        # Exhausted retry attempts
                        log_event("stream_error_final", {
                            "error": str(e),
                            "attempt": attempt + 1
                        })
                        raise

    except asyncio.CancelledError:
        cancelled_by_client = True
    except (httpx.ReadError, httpx.RemoteProtocolError, httpx.ConnectError) as e:
        cancelled_by_client = True
        log_event("error", {"stage": "stream", "message": str(e)})
        raise
    finally:
        # Final logging
        full_text = "".join(full_text_parts)
        logged_text, truncated = prepare_streaming_text_for_log(full_text)
        
        # If model stopped due to length limit, mark as truncated
        if finish_reason == "length":
            truncated = True

        log_response_event(
            payload=payload,
            content_text=logged_text,
            usage=usage,
            finish_reason=finish_reason,
            has_tool_calls=bool(tool_calls_info),
            tool_calls=tool_calls_info if tool_calls_info else None,
            streaming=True,
            content_length=len(full_text),
            truncated=truncated,
            req_id=req_id,
            processing_ms=processing_ms,
            cancelled_by_client=cancelled_by_client
        )

from typing import Optional

from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse, StreamingResponse

from core.config import config
from utils.auth import resolve_auth
from utils.models import resolve_model, sanitize_payload
from handlers.proxy_client import proxy_stream, proxy_json
from utils.logging_utils import log_event


router = APIRouter()


@router.post("/v1/chat/completions")
async def chat_completions(req: Request, authorization: Optional[str] = Header(None)):
    """Handle chat completions requests to OpenAI API."""
    body = await req.json()
    auth = resolve_auth(req, authorization, body)
    body["model"] = resolve_model(body.get("model"))
    body = sanitize_payload(body)

    # Check if request contains tool results (executed tool outputs)
    has_tool_results = False
    if "messages" in body:
        for msg in body["messages"]:
            if msg.get("role") == "tool" or "tool_call_id" in msg:
                has_tool_results = True
                break

    log_event("incoming_request", {
        "model": body.get("model"),
        "message_count": len(body.get("messages", [])),
        "has_tool_results": has_tool_results,
        "stream": body.get("stream", False),
        "tools_available": "tools" in body or "functions" in body,
        "full_payload": body,  # Log complete request payload
    })

    headers = {"Authorization": auth, "Content-Type": "application/json"}
    url = f"{config.openai_base_url}/v1/chat/completions"

    if body.get("stream"):
        return StreamingResponse(proxy_stream(url, headers, body), media_type="text/event-stream")
    data = await proxy_json(url, headers, body)
    return JSONResponse(content=data)


@router.post("/v1/responses")
async def responses(req: Request, authorization: Optional[str] = Header(None)):
    """Handle responses API requests to OpenAI API."""
    body = await req.json()
    auth = resolve_auth(req, authorization, body)
    body["model"] = resolve_model(body.get("model"))
    body = sanitize_payload(body)

    # Check if request contains tool results (executed tool outputs)
    has_tool_results = False
    if "messages" in body:
        for msg in body["messages"]:
            if msg.get("role") == "tool" or "tool_call_id" in msg:
                has_tool_results = True
                break

    log_event("incoming_request", {
        "model": body.get("model"),
        "message_count": len(body.get("messages", [])),
        "has_tool_results": has_tool_results,
        "stream": body.get("stream", False),
        "tools_available": "tools" in body or "functions" in body,
        "full_payload": body,  # Log complete request payload
    })

    headers = {"Authorization": auth, "Content-Type": "application/json"}
    url = f"{config.openai_base_url}/v1/responses"

    if body.get("stream"):
        return StreamingResponse(proxy_stream(url, headers, body), media_type="text/event-stream")
    data = await proxy_json(url, headers, body)
    return JSONResponse(content=data)


@router.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "proxy": "Cursor Proxy"}

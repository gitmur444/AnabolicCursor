from typing import Optional

from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse, StreamingResponse

from core.config import config
from utils.auth import resolve_auth
from utils.models import sanitize_payload
from handlers.proxy_client import proxy_stream, proxy_json
from utils.logging_utils import log_event


router = APIRouter()


async def _handle_proxy_request(req: Request, authorization: Optional[str], endpoint: str):
    """Common logic for handling proxy requests."""
    body = await req.json()
    auth = resolve_auth(req, authorization, body)
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
    url = f"{config.openai_base_url}{endpoint}"

    if body.get("stream"):
        return StreamingResponse(proxy_stream(url, headers, body), media_type="text/event-stream")
    data = await proxy_json(url, headers, body)
    return JSONResponse(content=data)


@router.post("/v1/chat/completions")
async def chat_completions(req: Request, authorization: Optional[str] = Header(None)):
    """Handle chat completions requests to OpenAI API."""
    return await _handle_proxy_request(req, authorization, "/v1/chat/completions")


@router.post("/v1/responses")
async def responses(req: Request, authorization: Optional[str] = Header(None)):
    """Handle responses API requests to OpenAI API."""
    return await _handle_proxy_request(req, authorization, "/v1/responses")


@router.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "proxy": "Cursor Proxy"}


# ---- Cursor auxiliary endpoints (stubs to avoid 404 and to log payloads) ----

@router.post("/v1/auth/exchange_user_api_key")
async def exchange_user_api_key(req: Request):
    """Stub: handle Cursor auth key exchange calls.

    Logs payload and returns a minimal success structure to satisfy the client.
    """
    try:
        body = await req.json()
    except Exception:
        body = None
    log_event("cursor_aux_api", {"endpoint": "exchange_user_api_key", "payload": body})
    return JSONResponse(content={"ok": True})


@router.post("/v1/aiserver.v1.AnalyticsService/TrackEvents")
async def analytics_track_events(req: Request):
    """Stub: track analytics events from Cursor.

    Accepts any JSON, logs it, returns success.
    """
    try:
        body = await req.json()
    except Exception:
        body = None
    log_event("cursor_aux_api", {"endpoint": "AnalyticsService.TrackEvents", "payload": body})
    return JSONResponse(content={"ok": True})


@router.post("/v1/aiserver.v1.DashboardService/GetUserPrivacyMode")
async def dashboard_get_user_privacy_mode(req: Request):
    """Stub: return a default privacy mode.

    If Cursor expects a boolean or enum, provide a conservative default.
    """
    try:
        body = await req.json()
    except Exception:
        body = None
    log_event("cursor_aux_api", {"endpoint": "DashboardService.GetUserPrivacyMode", "payload": body})
    return JSONResponse(content={"privacyMode": False})


@router.post("/v1/aiserver.v1.AiService/NameAgent")
async def ai_service_name_agent(req: Request):
    """Stub: name agent endpoint.

    Returns a fallback name and echoes any provided hint.
    """
    try:
        body = await req.json()
    except Exception:
        body = None
    log_event("cursor_aux_api", {"endpoint": "AiService.NameAgent", "payload": body})
    hint = None
    if isinstance(body, dict):
        hint = body.get("name") or body.get("hint") or body.get("prompt")
    return JSONResponse(content={"name": hint or "Agent"})

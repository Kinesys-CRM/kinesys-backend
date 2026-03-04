"""WebSocket endpoints for real-time call streaming."""

import json
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status

from app.services.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter()
ws_router = APIRouter()


@ws_router.websocket("/ws/agent")
async def agent_websocket(websocket: WebSocket) -> None:
    """Agent sends messages with {id, type, data} that are broadcast to subscribed frontends."""
    await manager.connect_agent(websocket)
    try:
        while True:
            raw_data = await websocket.receive_text()

            try:
                message = json.loads(raw_data)
            except json.JSONDecodeError:
                await websocket.send_json({"error": "Invalid JSON format", "type": "error"})
                continue

            call_id = message.get("id")
            if not call_id:
                await websocket.send_json({"error": "Message must include 'id' field", "type": "error"})
                continue

            sent_count = await manager.broadcast_to_call(call_id, raw_data)
            await websocket.send_json({"type": "ack", "call_id": call_id, "delivered_to": sent_count})

    except WebSocketDisconnect:
        logger.info("Agent disconnected")
    except Exception as e:
        logger.error("Agent WebSocket error: %s", e)
    finally:
        await manager.disconnect_agent()


@ws_router.websocket("/ws/calls/{call_id}")
async def frontend_websocket(websocket: WebSocket, call_id: str) -> None:
    """Frontend subscribes to a specific call_id to receive agent broadcasts."""
    if not call_id or not call_id.strip():
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect_frontend(websocket, call_id)
    try:
        await websocket.send_json({"type": "connected", "call_id": call_id})

        while True:
            raw_data = await websocket.receive_text()
            try:
                message = json.loads(raw_data)
            except json.JSONDecodeError:
                continue

            msg_type = message.get("type", "")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong", "call_id": call_id})
            elif msg_type == "status":
                count = await manager.get_frontend_count(call_id)
                await websocket.send_json({"type": "status", "call_id": call_id, "connected_clients": count})

    except WebSocketDisconnect:
        logger.info("Frontend disconnected from call %s", call_id)
    except Exception as e:
        logger.error("Frontend WebSocket error for call %s: %s", call_id, e)
    finally:
        await manager.disconnect_frontend(websocket, call_id)


@router.get("/active")
async def get_active_calls() -> dict[str, Any]:
    active_calls = await manager.get_active_calls()
    return {"active_calls": active_calls, "count": len(active_calls)}


@router.get("/{call_id}/status")
async def get_call_status(call_id: str) -> dict[str, Any]:
    count = await manager.get_frontend_count(call_id)
    return {"call_id": call_id, "connected_frontends": count, "active": count > 0}

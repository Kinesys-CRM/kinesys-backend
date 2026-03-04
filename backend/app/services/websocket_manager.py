"""WebSocket connection manager for real-time call streaming."""

import asyncio
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections between AI agents and frontend clients."""

    def __init__(self) -> None:
        self._frontends: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()
        self._agent_ws: WebSocket | None = None

    async def connect_frontend(self, websocket: WebSocket, call_id: str) -> None:
        await websocket.accept()
        async with self._lock:
            if call_id not in self._frontends:
                self._frontends[call_id] = set()
            self._frontends[call_id].add(websocket)

    async def disconnect_frontend(self, websocket: WebSocket, call_id: str) -> None:
        async with self._lock:
            if call_id in self._frontends:
                self._frontends[call_id].discard(websocket)
                if not self._frontends[call_id]:
                    del self._frontends[call_id]

    async def connect_agent(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._agent_ws = websocket
        logger.info("Agent connected")

    async def disconnect_agent(self) -> None:
        self._agent_ws = None
        logger.info("Agent disconnected")

    async def broadcast_to_call(self, call_id: str, message: str) -> int:
        """Broadcast a message to all frontends subscribed to a call. Returns send count."""
        async with self._lock:
            frontends = self._frontends.get(call_id, set()).copy()

        sent_count = 0
        failed: list[WebSocket] = []

        for ws in frontends:
            try:
                await ws.send_text(message)
                sent_count += 1
            except Exception:
                failed.append(ws)

        if failed:
            async with self._lock:
                if call_id in self._frontends:
                    for ws in failed:
                        self._frontends[call_id].discard(ws)

        return sent_count

    async def get_frontend_count(self, call_id: str) -> int:
        async with self._lock:
            return len(self._frontends.get(call_id, set()))

    async def get_active_calls(self) -> list[str]:
        async with self._lock:
            return list(self._frontends.keys())


manager = ConnectionManager()

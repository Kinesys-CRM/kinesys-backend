"""LiveKit AI agent dispatch endpoints."""

import json
import logging
import uuid
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from livekit import api

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentConfig(BaseModel):
    phone_number: str | None = Field(None, description="Phone number for the call")
    system_prompt: str | None = None
    welcome_message: str | None = None
    ai_speaks_first: bool = True
    voice_id: str | None = None
    llm_model: str = "gpt-4o-mini"
    stt_model: str = "nova-3"
    style_guardrails: str | None = None


class DispatchRequest(BaseModel):
    agent_config: AgentConfig
    room_name: str | None = None


class DispatchResponse(BaseModel):
    success: bool
    room_name: str
    message: str


class RoomTokenRequest(BaseModel):
    room_name: str
    participant_name: str


class RoomTokenResponse(BaseModel):
    token: str
    room_name: str
    livekit_url: str


def _create_livekit_api() -> api.LiveKitAPI:
    return api.LiveKitAPI(
        url=settings.LIVEKIT_URL,
        api_key=settings.LIVEKIT_API_KEY,
        api_secret=settings.LIVEKIT_API_SECRET,
    )


@router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_agent(request: DispatchRequest) -> DispatchResponse:
    """Dispatch an AI agent to a LiveKit room."""
    try:
        room_name = request.room_name or f"call-{uuid.uuid4().hex[:12]}"

        lk = _create_livekit_api()
        await lk.room.create_room(api.CreateRoomRequest(name=room_name))
        await lk.aclose()

        # Dispatch agent with config as metadata
        lk = _create_livekit_api()
        metadata = json.dumps(request.agent_config.model_dump())
        await lk.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name=settings.LIVEKIT_AGENT_NAME,
                room=room_name,
                metadata=metadata,
            )
        )
        await lk.aclose()

        logger.info(f"Dispatched agent to room: {room_name}")
        return DispatchResponse(
            success=True,
            room_name=room_name,
            message=f"Agent dispatched to room {room_name}",
        )
    except Exception as e:
        logger.error(f"Failed to dispatch agent: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to dispatch agent: {e}")


@router.post("/token", response_model=RoomTokenResponse)
async def get_room_token(request: RoomTokenRequest) -> RoomTokenResponse:
    """Generate a LiveKit token for a participant to join a room."""
    try:
        token = api.AccessToken(
            api_key=settings.LIVEKIT_API_KEY,
            api_secret=settings.LIVEKIT_API_SECRET,
        )
        token.with_identity(request.participant_name)
        token.with_name(request.participant_name)
        token.with_grants(api.VideoGrants(room_join=True, room=request.room_name))

        return RoomTokenResponse(
            token=token.to_jwt(),
            room_name=request.room_name,
            livekit_url=settings.LIVEKIT_URL,
        )
    except Exception as e:
        logger.error(f"Failed to generate token: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to generate token: {e}")


@router.get("/rooms")
async def list_rooms() -> dict[str, Any]:
    """List active LiveKit rooms."""
    try:
        lk = _create_livekit_api()
        rooms = await lk.room.list_rooms(api.ListRoomsRequest())
        await lk.aclose()

        return {
            "rooms": [
                {"name": r.name, "num_participants": r.num_participants}
                for r in rooms.rooms
            ],
            "count": len(rooms.rooms),
        }
    except Exception as e:
        logger.error(f"Failed to list rooms: {e}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list rooms: {e}")

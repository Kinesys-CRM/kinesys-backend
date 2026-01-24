from fastapi import APIRouter, Depends, HTTPException
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from googleapiclient.discovery import build
import json

from app.api.deps import get_current_user, get_db
from app.models.user_model import User
from app.crud.user_crud import user_crud
from sqlmodel.ext.asyncio.session import AsyncSession

router = APIRouter()


async def get_calendar_service(user: User, db: AsyncSession):
    """Build Google Calendar service from stored credentials"""
    if not user.google_credentials_json:
        raise HTTPException(401, "Google Calendar not connected")

    creds_dict = json.loads(user.google_credentials_json)
    
    # Handle expiry parsing
    expiry = None
    if creds_dict.get("expiry"):
        from datetime import datetime
        try:
            expiry = datetime.fromisoformat(creds_dict["expiry"])
        except ValueError:
            pass

    creds = Credentials(
        token=creds_dict["token"],
        refresh_token=creds_dict.get("refresh_token"),
        token_uri=creds_dict["token_uri"],
        client_id=creds_dict["client_id"],
        client_secret=creds_dict["client_secret"],
        scopes=creds_dict["scopes"],
        expiry=expiry,
    )

    # Refresh if expired
    if creds.expired and creds.refresh_token:
        creds.refresh(GoogleRequest())
        # Update stored credentials
        new_creds_json = json.dumps({
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "scopes": list(creds.scopes) if creds.scopes else creds_dict["scopes"],
            "expiry": creds.expiry.isoformat() if creds.expiry else None,
        })
        await user_crud.update_google_credentials(db, user=user, credentials_json=new_creds_json)

    return build("calendar", "v3", credentials=creds)


@router.get("/events")
async def list_events(
    max_results: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List upcoming calendar events"""
    service = await get_calendar_service(current_user, db)
    
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=now,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    
    return events_result.get("items", [])


@router.get("/status")
async def calendar_status(current_user: User = Depends(get_current_user)):
    """Check if user has Google Calendar connected"""
    return {
        "connected": current_user.google_credentials_json is not None,
    }
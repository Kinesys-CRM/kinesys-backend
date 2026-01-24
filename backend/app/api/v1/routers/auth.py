from urllib.parse import urlencode

from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import RedirectResponse, JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
import secrets

from app.core.config import settings
from app.api.deps import get_db, get_current_user
from app.controllers.auth import get_authorization_url, handle_oauth_callback
from app.schemas.user_schema import UserRead
from app.models.user_model import User

router = APIRouter()

# Frontend callback URL - where to redirect after OAuth
FRONTEND_CALLBACK_URL = "http://localhost:5173/auth/callback"


@router.get("/login")
async def login_google():
    """Redirect user to Google OAuth consent screen."""
    state = secrets.token_urlsafe(32)
    authorization_url = get_authorization_url(state)

    response = RedirectResponse(authorization_url)
    # For development, use less restrictive cookie settings
    # In production, use secure=True and samesite="lax"
    is_production = settings.MODE.value == "production"
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=is_production,
        samesite="lax" if is_production else "none",
        max_age=600,
    )
    return response


@router.get("/callback")
async def google_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback, create/update user, redirect to frontend with JWT."""
    # Validate CSRF state (skip in development - localhost cookies don't work with cross-site redirects)
    is_production = settings.MODE.value == "production"
    if is_production:
        cookie_state = request.cookies.get("oauth_state")
        if not cookie_state or state != cookie_state:
            # Redirect to frontend with error
            error_params = urlencode({"error": "csrf", "error_description": "Invalid state - possible CSRF"})
            return RedirectResponse(f"{FRONTEND_CALLBACK_URL}?{error_params}")

    try:
        result = await handle_oauth_callback(code=code, db=db)
    except Exception as e:
        # Redirect to frontend with error
        error_params = urlencode({"error": "oauth_failed", "error_description": str(e)})
        response = RedirectResponse(f"{FRONTEND_CALLBACK_URL}?{error_params}")
        response.delete_cookie("oauth_state")
        return response

    # Redirect to frontend with token
    params = urlencode({"token": result["access_token"]})
    response = RedirectResponse(f"{FRONTEND_CALLBACK_URL}?{params}")
    response.delete_cookie("oauth_state")
    return response


@router.get("/callback/json")
async def google_callback_json(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback, return JWT as JSON (for API clients)."""
    is_production = settings.MODE.value == "production"
    if is_production:
        cookie_state = request.cookies.get("oauth_state")
        if not cookie_state or state != cookie_state:
            raise HTTPException(400, "Invalid state - possible CSRF")

    try:
        result = await handle_oauth_callback(code=code, db=db)
    except Exception as e:
        raise HTTPException(400, f"OAuth failed: {e}")

    response = JSONResponse(result)
    response.delete_cookie("oauth_state")
    return response


@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user."""
    return UserRead(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        picture_url=current_user.picture_url,
        has_google_calendar=current_user.google_credentials_json is not None,
    )
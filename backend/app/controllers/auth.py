"""
Google OAuth Authentication Controller

Handles the business logic for Google OAuth authentication flow.
"""
from google_auth_oauthlib.flow import Flow
from sqlmodel.ext.asyncio.session import AsyncSession
import json

from app.core.config import settings
from app.core.jwt import create_access_token
from app.crud.user_crud import user_crud
from app.schemas.user_schema import UserCreate

SCOPES = [
    "https://www.googleapis.com/auth/calendar.events",
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


def get_google_flow() -> Flow:
    """Create Google OAuth flow with configured credentials."""
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )


def get_authorization_url(state: str) -> str:
    """Generate Google OAuth authorization URL."""
    flow = get_google_flow()
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        state=state,
    )
    return authorization_url


async def handle_oauth_callback(code: str, db: AsyncSession) -> dict:
    """
    Handle the OAuth callback from Google.
    
    1. Exchange code for tokens
    2. Get user info from Google
    3. Create or find user in database
    4. Store Google credentials
    5. Generate JWT token
    
    Returns dict with access_token and user info.
    """
    flow = get_google_flow()
    
    # Exchange authorization code for tokens
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Get user info from Google
    session = flow.authorized_session()
    userinfo = session.get("https://www.googleapis.com/oauth2/v3/userinfo").json()
    
    google_id = userinfo["sub"]
    email = userinfo["email"]
    name = userinfo.get("name", "")
    picture = userinfo.get("picture", "")
    
    # Find or create user
    user = await user_crud.get_by_google_id_or_email(db, google_id=google_id, email=email)
    
    if not user:
        user = await user_crud.create(
            db,
            obj_in=UserCreate(
                email=email,
                google_id=google_id,
                username=email.split("@")[0],
                full_name=name,
                picture_url=picture,
            ),
        )
    
    # Store Google credentials for Calendar API
    creds_json = json.dumps({
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": list(credentials.scopes) if credentials.scopes else SCOPES,
        "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
    })
    await user_crud.update_google_credentials(db, user=user, credentials_json=creds_json)
    
    # Create JWT for API auth
    access_token = create_access_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "picture_url": user.picture_url,
        },
    }

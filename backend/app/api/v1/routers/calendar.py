from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from app.core.config import settings

router = APIRouter()

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


#Directing the user to the google login page
@router.get("/auth/google")
async def login_google():
    flow = Flow.from_client_config(
    {
    "web": {
    "client_id": settings.GOOGLE_CLIENT_ID,
    "client_secret": settings.GOOGLE_CLIENT_SECRET,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    }
    },
    scopes=SCOPES,
    redirect_uri=settings.GOOGLE_REDIRECT_URI
    )


    auth_url, _ = flow.authorization_url(access_type='offline', prompt='consent')

    return RedirectResponse(auth_url)



#Directing the user back to the site.
@router.get("/auth/google/callback")
async def google_callback(request: Request):
    code = request.query_params.get("code")

    if not code:
        raise HTTPException(status_code=400,detail="Authorization code not found.")

    flow = Flow.from_client_config(
        {
        "web":{
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=["https://www.googleapis.com/auth/calendar.events",
                "openid", 
                "https://www.googleapis.com/auth/userinfo.email"
                ],
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

    try:
        flow.fetch_token(code=code)
    except Exception as e:
        raise HTTPException(status_code=404,detail=f"Failed to fetch token: {str(e)}")

    credentials= flow.credentials
    refresh_token= credentials.refresh_token

    # NOTE: Google only sends the refresh_token the FIRST time a user authorizes.
    
    if not refresh_token:
        print("Warning: no refresh token returned")

    return {
        "status": "success",
        "message": "Google Calendar connected",
        "has_refresh_token": refresh_token is not None
    }
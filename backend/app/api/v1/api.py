from fastapi import APIRouter
from .routers import auth

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
# router.include_router(mail.router, prefix="/mails", tags=["mails"])
# router.include_router(calendar.router, prefix="/calendar",tags=["calendar"])
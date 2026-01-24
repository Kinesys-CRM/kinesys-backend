from fastapi import APIRouter
from .routers import auth, mail

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(mail.router, prefix="/mails", tags=["mails"])
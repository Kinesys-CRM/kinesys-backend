from fastapi import APIRouter
from .routers import auth, leads, calls, bookings, ai_calling, calendar

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(leads.router, prefix="/leads", tags=["leads"])
router.include_router(calls.router, prefix="/calls", tags=["calls"])
router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
router.include_router(ai_calling.router, prefix="/ai-calling", tags=["ai-calling"])
router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])

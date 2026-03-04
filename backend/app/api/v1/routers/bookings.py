"""Booking endpoints for voice agent appointment scheduling."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.crud import booking_crud
from app.schemas.booking_schema import (
    AvailabilityResponse,
    BookingCreate,
    BookingResponse,
    ErrorResponse,
    TimeSlot,
)

router = APIRouter()


def _validate_timezone(tz: str) -> ZoneInfo:
    try:
        return ZoneInfo(tz)
    except ZoneInfoNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": f"Invalid timezone: {tz}. Use a valid IANA timezone like 'America/New_York'.",
                "error_code": "INVALID_TIMEZONE",
            },
        )


def _format_friendly_datetime(dt: datetime, tz: ZoneInfo) -> str:
    """Format datetime for voice agent readback (e.g., 'January 25, 2026 at 9:00 AM EST')."""
    local_dt = dt.astimezone(tz)
    hour = local_dt.strftime("%I").lstrip("0")
    return local_dt.strftime(f"%B %d, %Y at {hour}:%M %p %Z")


@router.get(
    "/availability",
    response_model=AvailabilityResponse,
    responses={400: {"model": ErrorResponse}},
)
async def get_availability(
    timeZone: str = Query(
        description="IANA timezone (e.g., 'America/New_York')",
        examples=["America/New_York", "Europe/London", "Asia/Tokyo"],
    ),
    db: AsyncSession = Depends(get_db),
) -> AvailabilityResponse:
    """Get available booking slots for the next 7 days."""
    tz = _validate_timezone(timeZone)
    utc = ZoneInfo("UTC")

    now = datetime.now(utc)
    end_date = now + timedelta(days=8)

    booked_slots = await booking_crud.get_booked_slots(db, now, end_date)

    available = booking_crud.generate_available_slots(
        booked_slots_utc=booked_slots,
        timezone_str=timeZone,
        days=7,
        start_hour=9,
        end_hour=20,
        slot_duration_minutes=60,
    )

    slots = [
        TimeSlot(date=date_str, times=times)
        for date_str, times in sorted(available.items())
    ]

    return AvailabilityResponse(available_slots=slots, timezone=timeZone)


@router.post(
    "/create",
    response_model=BookingResponse,
    responses={400: {"model": ErrorResponse}, 409: {"model": ErrorResponse}},
)
async def create_booking(
    booking_in: BookingCreate,
    db: AsyncSession = Depends(get_db),
) -> BookingResponse:
    """Create a booking appointment. Idempotent for same email + time slot."""
    tz = _validate_timezone(booking_in.timeZone)
    utc = ZoneInfo("UTC")

    try:
        local_dt = datetime.strptime(
            f"{booking_in.appointmentDate} {booking_in.appointmentTime}",
            "%Y-%m-%d %H:%M",
        )
        local_dt = local_dt.replace(tzinfo=tz)
        utc_dt = local_dt.astimezone(utc)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"success": False, "error": f"Invalid date/time: {e}", "error_code": "INVALID_DATETIME"},
        )

    if utc_dt <= datetime.now(utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "Cannot book appointments in the past.",
                "error_code": "PAST_DATETIME",
            },
        )

    # Idempotency check
    existing = await booking_crud.find_existing_booking(db, email=booking_in.email, appointment_datetime=utc_dt)
    if existing:
        return BookingResponse(
            success=True,
            booking_id=str(existing.id),
            confirmed_datetime=local_dt.isoformat(),
            message=f"Booking already confirmed for {_format_friendly_datetime(utc_dt, tz)}",
        )

    if not await booking_crud.check_slot_available(db, utc_dt):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "success": False,
                "error": "This time slot is no longer available.",
                "error_code": "SLOT_UNAVAILABLE",
            },
        )

    booking = await booking_crud.create_booking(
        db,
        appointment_datetime=utc_dt,
        timezone=booking_in.timeZone,
        first_name=booking_in.firstName,
        last_name=booking_in.lastName,
        email=booking_in.email,
        phone=booking_in.phone,
        contact_id=booking_in.contactId,
    )

    return BookingResponse(
        success=True,
        booking_id=str(booking.id),
        confirmed_datetime=local_dt.isoformat(),
        message=f"Booking confirmed for {_format_friendly_datetime(utc_dt, tz)}",
    )

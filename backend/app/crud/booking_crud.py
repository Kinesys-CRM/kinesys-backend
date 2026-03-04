"""CRUD operations for bookings."""

from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.booking_model import Booking, BookingStatus


async def get_booked_slots(
    db: AsyncSession, start_date: datetime, end_date: datetime,
) -> list[datetime]:
    """Get booked appointment datetimes within a date range (UTC)."""
    query = (
        select(Booking.appointment_datetime)
        .where(
            Booking.appointment_datetime >= start_date,
            Booking.appointment_datetime < end_date,
            Booking.is_active == True,
            Booking.status.in_([BookingStatus.CONFIRMED.value, BookingStatus.COMPLETED.value]),
        )
    )
    result = await db.exec(query)
    return list(result.all())


async def check_slot_available(db: AsyncSession, appointment_datetime: datetime) -> bool:
    query = (
        select(Booking)
        .where(
            Booking.appointment_datetime == appointment_datetime,
            Booking.is_active == True,
            Booking.status.in_([BookingStatus.CONFIRMED.value, BookingStatus.COMPLETED.value]),
        )
    )
    result = await db.exec(query)
    return result.first() is None


async def find_existing_booking(
    db: AsyncSession, email: str, appointment_datetime: datetime,
) -> Booking | None:
    """Find existing booking for idempotency (same email + same time)."""
    query = (
        select(Booking)
        .where(
            Booking.email == email,
            Booking.appointment_datetime == appointment_datetime,
            Booking.is_active == True,
            Booking.status == BookingStatus.CONFIRMED.value,
        )
    )
    result = await db.exec(query)
    return result.first()


async def create_booking(
    db: AsyncSession,
    *,
    appointment_datetime: datetime,
    timezone: str,
    first_name: str,
    last_name: str,
    email: str,
    phone: str,
    contact_id: UUID | None = None,
) -> Booking:
    booking = Booking(
        appointment_datetime=appointment_datetime,
        timezone=timezone,
        first_name=first_name,
        last_name=last_name,
        email=email,
        phone=phone,
        contact_id=contact_id,
        status=BookingStatus.CONFIRMED.value,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


async def get_booking(db: AsyncSession, booking_id: UUID) -> Booking | None:
    result = await db.exec(
        select(Booking).where(Booking.id == booking_id, Booking.is_active == True)
    )
    return result.first()


async def cancel_booking(db: AsyncSession, booking_id: UUID) -> Booking | None:
    booking = await get_booking(db, booking_id)
    if booking:
        booking.status = BookingStatus.CANCELLED.value
        await db.commit()
        await db.refresh(booking)
    return booking


def generate_available_slots(
    booked_slots_utc: list[datetime],
    timezone_str: str,
    days: int = 7,
    start_hour: int = 9,
    end_hour: int = 17,
    slot_duration_minutes: int = 60,
) -> dict[str, list[str]]:
    """Generate available time slots for the next N days, excluding weekends and booked slots."""
    tz = ZoneInfo(timezone_str)

    booked_set = {
        slot.astimezone(tz).replace(tzinfo=None) for slot in booked_slots_utc
    }

    now = datetime.now(tz)

    if now.hour >= end_hour:
        start_date = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

    available: dict[str, list[str]] = {}

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)

        # Skip weekends
        if current_date.weekday() >= 5:
            continue

        date_str = current_date.strftime("%Y-%m-%d")
        times: list[str] = []

        slot_time = current_date.replace(hour=start_hour, minute=0)
        end_time = current_date.replace(hour=end_hour, minute=0)

        while slot_time < end_time:
            slot_with_tz = slot_time.replace(tzinfo=tz)
            if slot_with_tz > now and slot_time not in booked_set:
                times.append(slot_time.strftime("%H:%M"))
            slot_time += timedelta(minutes=slot_duration_minutes)

        if times:
            available[date_str] = times

    return available

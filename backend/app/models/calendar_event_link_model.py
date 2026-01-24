"""Model for linking Google Calendar events to CRM leads."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.lead_model import Lead
    from app.models.user_model import User


class CalendarEventLink(SQLModel, table=True):
    """Links Google Calendar events to CRM leads."""

    __tablename__ = "calendar_event_links"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    google_event_id: str = Field(index=True, max_length=255)
    lead_id: UUID | None = Field(default=None, foreign_key="leads.id", index=True)
    user_id: UUID = Field(foreign_key="users.id", index=True)
    event_title: str | None = Field(default=None, max_length=255)  # Cache for quick lookup
    event_start: datetime | None = None  # Cache for quick lookup
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    lead: "Lead | None" = Relationship(back_populates="calendar_events")
    user: "User" = Relationship(back_populates="calendar_event_links")

    class Config:
        # Ensure unique constraint on google_event_id per user
        pass

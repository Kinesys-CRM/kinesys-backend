from datetime import datetime
from sqlalchemy import func
from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4

class BaseUUIDModel(SQLModel):

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True, nullable=False)

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        sa_column_kwargs={"server_default": func.now()}
    )
    updated_at: datetime | None = Field(
        default=None,
        sa_column_kwargs={"onupdate": func.now()}
    )
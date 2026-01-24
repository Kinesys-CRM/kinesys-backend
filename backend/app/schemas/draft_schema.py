from pydantic import BaseModel
from uuid import UUID

class DraftCreate(BaseModel):
    draft: str
    summary: str | None = None

class DraftRead(BaseModel):
    id: UUID
    draft: str
    summary: str | None = None
    user_id: UUID
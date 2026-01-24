from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr

from .base_model import BaseUUIDModel

if TYPE_CHECKING:
    from .mail_model import Mail


class UserBase(SQLModel):
    username: str = Field(index=True)
    email: EmailStr = Field(unique=True, index=True)


class User(BaseUUIDModel, UserBase, table=True):
    __tablename__ = "users"

    # Google OAuth fields
    google_id: str = Field(unique=True, index=True)
    full_name: str | None = Field(default=None)
    picture_url: str | None = Field(default=None)
    google_credentials_json: str | None = Field(default=None)  # Serialized Google credentials

    # Relationships
    # mails: list["Mail"] = Relationship(
    #     back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"}
    # )

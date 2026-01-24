from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from pydantic import EmailStr

from .base_model import BaseUUIDModel

if TYPE_CHECKING:
    from .mail_model import Mail

class UserBase(SQLModel):
    username: str
    email: EmailStr = Field()

class User(BaseUUIDModel, UserBase, table=True):
    __tablename__ = "users"

    hashed_password: str | None = Field(default=None, nullable=False, index=True)
    mails: list["Mail"] = Relationship(back_populates="user", sa_relationship_kwargs={"cascade": "all, delete"})

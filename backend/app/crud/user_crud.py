"""CRUD operations for User module."""

from datetime import datetime
from uuid import UUID

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.user_model import User
from app.schemas.user_schema import UserCreate


class UserCRUD:

    async def get(self, db: AsyncSession, user_id: UUID) -> User | None:
        return await db.get(User, user_id)

    async def get_by_id(self, db: AsyncSession, user_id: str | UUID) -> User | None:
        if isinstance(user_id, str):
            user_id = UUID(user_id)
        return await db.get(User, user_id)

    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.exec(select(User).where(User.email == email))
        return result.first()

    async def get_by_google_id(self, db: AsyncSession, google_id: str) -> User | None:
        result = await db.exec(select(User).where(User.google_id == google_id))
        return result.first()

    async def get_by_google_id_or_email(
        self, db: AsyncSession, google_id: str, email: str
    ) -> User | None:
        result = await db.exec(
            select(User).where((User.google_id == google_id) | (User.email == email))
        )
        return result.first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> tuple[list[User], int]:
        # Get users
        query = select(User).offset(skip).limit(limit)
        result = await db.exec(query)
        users = list(result.all())

        # Get total count
        count_result = await db.exec(select(User))
        total = len(count_result.all())

        return users, total

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        db_obj = User(**obj_in.model_dump())
        db.add(db_obj)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        await db.refresh(db_obj)
        return db_obj

    async def update_google_credentials(
        self, db: AsyncSession, *, user: User, credentials_json: str
    ) -> User:
        user.google_credentials_json = credentials_json
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_refresh_token(
        self,
        db: AsyncSession,
        *,
        user: User,
        refresh_token: str | None,
        expires: datetime | None,
    ) -> User:
        user.refresh_token = refresh_token
        user.refresh_token_expires = expires
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def get_by_refresh_token(self, db: AsyncSession, refresh_token: str) -> User | None:
        result = await db.exec(select(User).where(User.refresh_token == refresh_token))
        return result.first()


user_crud = UserCRUD()

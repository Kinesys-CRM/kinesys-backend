from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserUpdate
from app.core.security import hash_password
from app.crud.base_crud import CRUDBase

class UserCRUD(CRUDBase[User, UserCreate, UserUpdate]):
    async def get_by_email(self, db: AsyncSession, email: str) -> User | None:
        result = await db.exec(select(User).where(User.email == email))
        return result.first()

    async def create(self, db: AsyncSession, *, obj_in: UserCreate) -> User:
        db_obj = User(
            username=obj_in.username,
            email=obj_in.email,
            hashed_password=hash_password(obj_in.password),
        )
        db.add(db_obj)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            raise
        await db.refresh(db_obj)
        return db_obj

user_crud = UserCRUD(User)
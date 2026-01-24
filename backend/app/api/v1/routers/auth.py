from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas.user_schema import UserCreate, UserRead, UserLogin
from app.crud.user_crud import user_crud
from app.core.security import verify_password
from app.core.jwt import create_access_token
from app.api.deps import get_db  # Your async session dependency

router = APIRouter()

@router.post("/register", response_model=UserRead, status_code=201)
async def register(user_create: UserCreate, db: AsyncSession = Depends(get_db)):
    if await user_crud.get_by_email(db, user_create.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = await user_crud.create(db, obj_in=user_create)
    return user

@router.post("/login")
async def login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await user_crud.get_by_email(db, user_login.email)
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
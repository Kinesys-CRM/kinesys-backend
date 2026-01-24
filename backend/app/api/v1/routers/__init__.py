from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel.ext.asyncio.session import AsyncSession
from app.schemas.user_schema import UserCreate, UserRead, UserLogin
from app.crud.user_crud import user_crud
from app.core.security import verify_password
from app.core.jwt import create_access_token
from app.api.deps import get_db  # Your async session dependency

router = APIRouter()
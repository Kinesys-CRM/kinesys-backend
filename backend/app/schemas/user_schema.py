from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    pass

class UserRead(BaseModel):
    id: UUID
    username: str
    email: EmailStr

class UserLogin(BaseModel):
    email: EmailStr
    password: str
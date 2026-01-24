from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.api import router
from app.core.config import settings
from app.api.deps import get_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Intellipost API"}

@app.get("/db_check")
async def db_check(db:AsyncSession = Depends(get_db)):
    try:
        result= await db.execute(text("SELECT 1"))

        result.scalar()
        return{
            "status":"healthy",
            "database":"connected"
        }
    except Exception as e:
        return {
            "status":"unhealthy",
            "database":"disconnected",
            "error":str(e)
        }
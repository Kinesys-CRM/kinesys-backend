from fastapi import FastAPI, Depends
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.api import router
from app.api.v1.routers.calls import ws_router
from app.core.config import settings
from app.api.deps import get_db

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

ALLOWED_ORIGINS = [
    # Development
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    # Production
    "https://remiscus.me",
    "https://www.remiscus.me",
    "https://app.remiscus.me",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix=settings.API_V1_STR)
app.include_router(ws_router)


@app.get("/")
def root():
    return {"message": f"Welcome to the {settings.PROJECT_NAME} API"}


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

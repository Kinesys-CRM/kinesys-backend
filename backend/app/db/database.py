from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

engine = create_async_engine(
    str(settings.ASYNC_DATABASE_URI),
    echo=False,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)

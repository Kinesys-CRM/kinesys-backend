from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool

from app.core.config import settings # Assuming you have a settings file

# These pooling settings are from your first example and are solid
DB_POOL_SIZE = 83
WEB_CONCURRENCY = 9
POOL_SIZE = max(DB_POOL_SIZE // WEB_CONCURRENCY, 5)

# Create the async engine
engine = create_async_engine(
    str(settings.ASYNC_DATABASE_URI),
    echo=False,
    poolclass=AsyncAdaptedQueuePool, # Use a standard pool
    pool_size=POOL_SIZE,
    max_overflow=10, # A reasonable overflow
)

# Create a sessionmaker factory
# This factory will create new AsyncSession objects when called
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)
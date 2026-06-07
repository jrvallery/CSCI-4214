import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Set when running on Cloud Run; absent in local Docker dev
CLOUD_SQL_INSTANCE = os.getenv("CLOUD_SQL_INSTANCE")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://skiware:skiware@db:5432/skiware",
)


class Base(DeclarativeBase):
    pass


if CLOUD_SQL_INSTANCE:
    # Production: Cloud SQL Python Connector avoids the asyncpg Unix-socket
    # path-length issue and handles TLS automatically.
    from google.cloud.sql.connector import Connector

    _connector = Connector()

    async def _getconn():
        return await _connector.connect_async(
            CLOUD_SQL_INSTANCE,
            "asyncpg",
            user=os.getenv("DB_USER", "skiware"),
            password=os.getenv("DB_PASS", ""),
            db=os.getenv("DB_NAME", "skiware"),
        )

    engine = create_async_engine("postgresql+asyncpg://", async_creator=_getconn)
else:
    engine = create_async_engine(DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

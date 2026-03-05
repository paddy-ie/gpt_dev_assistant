from collections.abc import AsyncGenerator, Generator
from contextlib import contextmanager

from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

settings = get_settings()

async_engine = create_async_engine(settings.database_url, echo=False, future=True)
sync_engine = create_engine(settings.sync_database_url, echo=False, future=True)


async def init_db() -> None:
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(async_engine) as session:
        yield session


@contextmanager
def get_session() -> Generator[Session, None, None]:
    with Session(sync_engine) as session:
        yield session

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from psycopg import AsyncConnection
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from typing_extensions import Any
from typing_extensions import AsyncIterator

from app.core.config import get_database_url


class DatabaseSessionManager:
    def __init__(self: str):
        self._engine = None
        self._sessionmaker = None

    async def close(self):
        if self._engine is None:
            raise ValueError("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            _engine_kwargs: Dict[str, Any] = {"echo": True}
            self._engine = create_async_engine(get_database_url(), **_engine_kwargs)

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:

        if self._sessionmaker is None:
            self._sessionmaker = async_sessionmaker(bind=self.engine, expire_on_commit=False)

        session = self._sessionmaker()
        try:
            async with session.begin():
                yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    @property
    def engine(self):
        if self._engine is None:
            _engine_kwargs: Dict[str, Any] = {"echo": False}
            self._engine = create_async_engine(get_database_url(), **_engine_kwargs)
        return self._engine


sessionmanager = DatabaseSessionManager()

@asynccontextmanager
async def database_lifespan(app: FastAPI):
    """
    Close the DB connection when the app is shut down to avoid resource leaks.
    """
    sessionmanager.connect()
    yield
    if sessionmanager.engine is not None:
        # Close the DB connection
        await sessionmanager.close()
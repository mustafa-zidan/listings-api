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
    """
    Database session manager to handle the database engine and session creation and cleanup.
    """
    def __init__(self: str):
        self._engine = None
        self._sessionmaker = None

    async def close(self) -> None:
        """
        Close and cleanup the database session manager with all its resources.
        """
        if self._engine is None:
            raise ValueError("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        """
        Create a new database connection.
        Returns:
            psycopg.AsyncConnection: The database connection instance.
        """
        async with self.engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        """
        Create a new session.
        Note: asynccontextmanager is used to define a factory function for async
        with statement asynchronous context managers, without needing to create a
        class or separate __aenter__() and __aexit__() methods. It must be applied to an asynchronous generator function.

        Returns:
            sqlalchemy.ext.asyncio.AsyncSession: The database session instance.
        """

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
        """
        Get the database engine instance.
        Returns:
            sqlalchemy.ext.asyncio.AsyncEngine: The database engine instance.
        """
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
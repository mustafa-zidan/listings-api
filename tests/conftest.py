import os
from typing import AsyncGenerator, Any, Generator

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncEngine, AsyncSession
from testcontainers.postgres import PostgresContainer

from app.main import app
from app.models import Base


# Set the event loop scope explicitly for AnyIO
@pytest.fixture(scope="session")
def anyio_backend() -> str:
    """
    Specify the backend to use for AnyIO.

    Returns:
        str: The name of the backend (e.g., "asyncio").
    """
    return "asyncio"


@pytest.fixture(scope="session")
async def async_client(anyio_backend: str) -> AsyncGenerator[AsyncClient, None]:
    """
    Create an HTTP client for testing the FastAPI app.

    This client simulates requests to the application without starting an actual server.

    Args:
        anyio_backend (str): The backend used by AnyIO.

    Yields:
        AsyncClient: An HTTP client for the test.
    """
    async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, Any, None]:
    """
    Spin up a PostgreSQL container for testing.

    Yields:
        PostgresContainer: A running PostgreSQL container.
    """
    with PostgresContainer("postgres:latest") as postgres:
        yield postgres


def get_container_database_url(postgres_container: PostgresContainer) -> str:
    """
    Helper to generate the database URL from the PostgreSQL container.

    Args:
        postgres_container (PostgresContainer): The running PostgreSQL container.

    Returns:
        str: A connection string for the test database using psycopg3 dirver since postgres container still users psycopg2
    """
    database_url = (
        f"postgresql+psycopg://{postgres_container.username}:{postgres_container.password}"
        f"@{postgres_container.get_container_host_ip()}:{postgres_container.get_exposed_port(postgres_container.port)}"
        f"/{postgres_container.dbname}"
    )
    os.environ["DATABASE_URL"] = database_url
    return database_url


@pytest.fixture(scope="module")
async def engine(postgres_container: PostgresContainer) -> AsyncGenerator[AsyncEngine, None]:
    """
    Create an async SQLAlchemy engine using the PostgreSQL container.

    This fixture sets up the database tables at the beginning of the module's tests
    and cleans them up after the module's teardown.

    Args:
        postgres_container (PostgresContainer): The running PostgreSQL container.

    Yields:
        AsyncEngine: The SQLAlchemy async engine connected to the test database.
    """
    database_url: str = get_container_database_url(postgres_container)
    engine: AsyncEngine = create_async_engine(database_url, echo=True)

    # Create all tables before tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture(scope="function")
async def session(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide a new database session for each test.

    This fixture ensures each test has its own isolated session and purges the database
    by truncating all tables after the test. It works with the provided `AsyncEngine`.

    Args:
        engine (AsyncEngine): The SQLAlchemy async engine connected to the test database.

    Yields:
        AsyncSession: A new SQLAlchemy async session for the test.
    """
    # Create a session factory bound to the provided engine
    session_factory = async_sessionmaker(
        bind=engine, expire_on_commit=False
    )

    # Provide the session to the test
    async with session_factory() as session:
        yield session

        # Truncate all tables in reverse order to avoid foreign key conflicts
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"TRUNCATE TABLE {table.name} CASCADE"))

        # Commit the truncation
        await session.commit()
        await session.close()
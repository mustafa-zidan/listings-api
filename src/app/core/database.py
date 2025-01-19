from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.core.config import get_database_url

engine = create_async_engine(get_database_url(), echo=True)

SessionFactory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False
)

@asynccontextmanager
async def get_session():
    """Provide an async transactional scope around a series of operations."""
    async with SessionFactory() as session:
        try:
            yield session
            await session.commit()
        except:
            await session.rollback()
            raise
        finally:
            await session.close()

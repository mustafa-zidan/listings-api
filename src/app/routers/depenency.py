"""
Define the dependencies for the Routes package.
"""
from typing import AsyncGenerator, Any

from fastapi import Depends
from sqlalchemy.sql.annotation import Annotated

from app.core.database import sessionmanager
from app.repositories.listing import ListingRepository


async def get_listing_repository() -> AsyncGenerator[ListingRepository, Any]:
    """
    Create a listing repository with a new session
    Returns:
        ListingRepository: The repository instance for Data Access layer operations.
    """
    async with sessionmanager.session() as session:
        yield ListingRepository(session)


"""
Dependency for the ListingRepository instance.
"""
ListingRepositoryDep = Annotated[ListingRepository, Depends(get_listing_repository)]

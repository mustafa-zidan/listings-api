from fastapi import Depends
from sqlalchemy.sql.annotation import Annotated

from app.core.database import sessionmanager
from app.repositories.listing import ListingRepository


async def get_listing_repository() -> ListingRepository:
    async with sessionmanager.session() as session:
        yield ListingRepository(session)




ListingRepositoryDep = Annotated[ListingRepository, Depends(get_listing_repository)]

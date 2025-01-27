from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from app.repositories.listing import ListingRepository
from app.routers.depenency import ListingRepositoryDep
from app.routers.depenency import get_listing_repository
from app.schemas.listing import ListingFilterSchema, UpsertListingsSchema
from app.schemas.listing import ListingResponse
from app.schemas.listing import ListingResult
from app.schemas.listing import UpsertResult

router = APIRouter()


@router.get("/{listing_id}", response_model=ListingResponse|None)
async def get_listing_by_id(
        listing_id: str,
        repo: ListingRepositoryDep = Depends(get_listing_repository),
) -> ListingResponse|None:
    """
    Retrieve a listing by its ID.

    Args:
        listing_id (str): The unique identifier for the listing.
        repo (ListingRepository): The repository instance for database operations.

    Returns:
        ListingResponse: The retrieved listing data.
    """
    try:
        return await repo.get_listing_by_id(listing_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during retrieval: {str(e)}")


@router.post("/", response_model=UpsertResult)
async def upsert_listings(
        listings: UpsertListingsSchema,
        repo: ListingRepositoryDep = Depends(get_listing_repository),
) -> UpsertResult:
    """
    Insert or update listings and their related data.

    Args:
        listings (UpsertListingsSchema): List of listings with associated properties and entities.
        repo (ListingRepository): The repository instance Dependency for database operations.

    Returns:
        dict: Success message with counts of inserted and updated records.
    """
    try:
        result = await repo.upsert_listings(listings.listings)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during upsert: {str(e)}")


@router.post("/filter", response_model=ListingResult)
async def get_listings(
        filters: ListingFilterSchema,
        page: int = Query(1, ge=1),
        limit: int = Query(100, ge=1, le=500),
        repo: ListingRepositoryDep = Depends(get_listing_repository),
) -> ListingResult:
    """
    Retrieve listings based on filters and pagination.

    Args:
        filters (ListingFilterSchema): Filters for listings.
        page (int): Page number for pagination.
        limit (int): Number of listings per page.
        repo (ListingRepository): The repository instance for database operations.
    Returns:
        ListingResult: Structured listings and total count.
    """
    return await repo.get_filtered_listings(filters, page, limit)
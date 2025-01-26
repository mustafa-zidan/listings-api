from typing import Dict, List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query

from app.repositories.listing import ListingRepository
from app.routers.depenency import get_listing_repository
from app.routers.depenency import ListingRepositoryDep
from app.schemas.listing import ListingFilterSchema
from app.schemas.listing import ListingResponse
from app.schemas.listing import ListingResult
from app.schemas.listing import ListingSchema
from app.schemas.listing import UpsertResult

router = APIRouter()


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing_by_id(
        listing_id: str,
        repo: ListingRepositoryDep = Depends(get_listing_repository),
) -> ListingResponse:
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


@router.post("/listings", response_model=UpsertResult)
async def upsert_listings(
        listings: list[ListingSchema],
        repo: ListingRepositoryDep = Depends(get_listing_repository),
) -> UpsertResult:
    """
    Insert or update listings and their related data.

    Args:
        listings (list[ListingSchema]): List of listings with associated properties and entities.
        repo (ListingRepository): The repository instance for database operations.

    Returns:
        dict: Success message with counts of inserted and updated records.
    """
    try:
        result = await repo.upsert_listings(listings)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during upsert: {str(e)}")


@router.get("/listings", response_model=ListingResult)
async def get_listings(
        page: int = Query(1, ge=1),
        limit: int = Query(100, ge=1, le=500),
        listing_id: str|None = None,
        scan_date_from: str|None = None,
        scan_date_to: str|None = None,
        is_active: bool|None = None,
        image_hashes: List[str]|None = Query(None),
        dataset_entities: Dict[str, str]|None = None,
        property_filters: Dict[int, str]|None = None,
        repo: ListingRepositoryDep = Depends(get_listing_repository),
):
    """
    Retrieve listings based on filters and pagination.

    Args:
        page (int): Page number for pagination.
        limit (int): Number of listings per page.
        listing_id (Optional[str]): Filter by listing ID.
        scan_date_from (Optional[str]): Filter by minimum scan date.
        scan_date_to (Optional[str]): Filter by maximum scan date.
        is_active (Optional[bool]): Filter by active status.
        image_hashes (Optional[List[str]]): Filter by image hashes.
        dataset_entities (Optional[Dict[str, str]]): Filter by dataset entities.
        property_filters (Optional[Dict[int, str]]): Filter by property ID and values.
        repo (ListingRepository): The repository instance for database operations.

    Returns:
        ListingResult: Structured listings and total count.
    """
    filters = ListingFilterSchema(
        listing_id=listing_id,
        scan_date_from=scan_date_from,
        scan_date_to=scan_date_to,
        is_active=is_active,
        image_hashes=image_hashes,
        dataset_entities=dataset_entities,
        property_filters=property_filters,
    )
    return await repo.get_filtered_listings(filters, page, limit)
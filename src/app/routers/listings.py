from fastapi import APIRouter, HTTPException, Depends

from app.repositories.listing import ListingRepository
from app.routers.depenency import ListingRepositoryDep, get_listing_repository
from app.schemas.listing import ListingResponse, ListingResult, ListingFilterSchema

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



# @router.post("/bulk")
# async def bulk_create_listings(
#         listings: List[ListingSchema],
#         # repo: ListingRepository = ListingRepositoryDep,
# ) -> Dict[str, str]:
#     """
#     Bulk create multiple listings in the database.
#
#     Args:
#         listings (List[ListingSchema]): List of listing data to be created.
#         repo (ListingRepository): The repository instance for database operations.
#
#     Returns:
#         dict: A response indicating the success of the operation.
#     """
#     try:
#         # await repo.bulk_create_listings(listings)
#         return {"message": f"{len(listings)} listings created successfully."}
#     except Exception as e:
#         raise HTTPException(status_code=400, detail=f"Error during bulk creation: {str(e)}")
#
#
@router.get("/")
async def query_listings_with_filters(
        filters: ListingFilterSchema,
        page: int = 1,
        limit: int = 100,
        repo: ListingRepositoryDep = Depends(get_listing_repository),
) -> ListingResult:
    """
    Query listings with filters and pagination.

    Args:
        filters (ListingFilterSchema): The filters for querying listings.
        page Page number for pagination (1-indexed).
        size Number of listings per page, default 100
        repo (ListingRepository): The repository instance for database operations.

    Returns:
        ListingResult: The filtered listings and total count.
    """
    try:
        values = await repo.get_filtered_listings(filters, page, limit)
        return ListingResult(listings=[], total_count=0)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error during query: {str(e)}")
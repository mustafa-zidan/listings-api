from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_listings(page: int = 1):
    offset = (page - 1) * 100
    return {"listings": f"Listings from {offset} to {offset + 100}"}
from fastapi import FastAPI


from app.core.database import database_lifespan
from app.routers import listings

app = FastAPI(
    title="Listings API",
    docs_url="/api/v1/docs",
    lifespan=database_lifespan,
)

@app.get("/")
async def root():
    return {"message": "Listings API"}

app.include_router(listings.router, prefix="/api/v1/listings", tags=["listings"])

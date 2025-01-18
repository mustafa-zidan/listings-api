from fastapi import FastAPI

from app.routers import listings

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Tomato"}

app.include_router(listings.router, prefix="/api/v1/listings", tags=["listings"])

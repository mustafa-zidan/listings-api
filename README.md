# Listings API 
This is a simple API that allows you to bulk create, read, update and delete listings.

## Features
- Create a new listing
- Read a listings based on the listing id
- Upsert a listings
- Delete a listing based on the listing id
- Search for listings based on the search query

## Technologies
- Python
- [uv](https://github.com/astral-sh/uv)
- FastAPI
- SQLAlchemy
- Alembic (for migrations)
- Docker / Docker Compose
- PostgreSQL
- Pytest

## Setup
1. Clone the repository
2. Use Pip to install the dependencies
```bash
pip install e ".test"
```
or if you fancy UV like me then 
```bash
uv venv
uv sync 
```
3. run the tests using
```bash
pytest
```
4. Start the server using
```bash
fastapi dev /src/app/main.py
```
## run docker compose
```bash
docker-compose up
```
## run alembic migrations
```bash
alembic upgrade head
```

## API Documentation
The API documentation is available at `http://localhost:8000/api/v1/docs`

## Notes on the implementation: 
- I choose Fastapi because of the asyncio support and the automatic generation of the API documentation
- I choose uv for the virtual environment because it is faster than venv
- I choose alembic for the migrations because it is the thing that work with SQLAlchemy
- I choose PostgreSQL because I am familiar with it.

- The whole implementation is async and the database is accessed using async functions.
- The tests are also async and they are run using pytest-asyncio
- I focused on making the application more modular and testable 
  than feature completeness. 

### Things I had to cut corners in:
- Creating more tests for the routers
- Adding indices to the database as part of the migration. 
- Adding logging and proper error handling.


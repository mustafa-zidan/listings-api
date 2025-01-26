# Listings API 
This is a simple API that allows you to bulk create, read, update and delete listings.

## Features
- Create a new listing
- Read a listing based on the listing id
- Upsert a listing
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
- I choose uv for the virtual environment because it is faster than pip and it uses lock file ensuring that the dependencies are the same across different builds.
- I choose alembic for the migrations because it is the thing that work with SQLAlchemy
- I choose PostgreSQL because I am familiar with it.

- The whole implementation is async and the database is accessed using async functions.
- The tests are also async, and they are run using pytest-asyncio
- I focused on making the application more modular and testable 
  than covering all the edge cases. 
- The tests are more focused on integration tests than unit tests.

### Things I had to cut corners in:
- Creating more tests for the routers
- Adding indices to the database as part of the migration. 
- Adding logging and proper error handling.


### Why FastAPI?
* Built on ASGI (Asynchronous Server Gateway Interface) and supports asyncio.
* Built-in Type Validation and Data Serialization using Pydantic.
* Automatic OpenAPI documentation generation.
* Dependency Injection system.

### Why SQLAlchemy?
* The most popular ORM for Python with a mature ecosystem.
* Database-agnostic and supports multiple databases.
* Provides a high-level ORM API as well as a low-level SQL expression language. which provides productivity and fing-grained control.
* Used Pydantic for data validation and serialization. which is also used by FastAPI. it allows for seamless integration between the two libraries.

> **NOTE**:
> Tortoise ORM is also a good alternative that has a native support for asyncio
> and is built on top of the asyncpg library, but I have limited experience with it.
>
> SQLModel also comes to mind especially it is built on to of SQLAlchemy, but it is not as mature.         

### Why PostgreSQL?
* The database that comes to mind when I think of a relational database that also supports JSONB storage.
* JSONB indexing and querying support. 

## Application Structure 

The application code is structured as follows:

```
alembic                         # Alembic database migrations 
├── versions                    # Migration scripts
├── env.py                      # Alembic environment configuration
├── script.py.mako              # Alembic script template
src
├── app   
│   ├── core
│   │   ├── config.py           # Application configuration
│   │   ├── database.py         # Database initialization and session management
│   ├── models                  # SQLAlchemy models 
│   ├── repositories            # Data access layer for the models 
│   ├── routers                 # FastAPI routers
│   ├── schemas                 # Pydantic models for request and response validation
│   ├── __init__.py
│   ├── main.py                 # FastAPI application instance
tests                           # Tests
```

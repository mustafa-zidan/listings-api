import logging
import os

logger = logging.getLogger(__name__)



def get_database_url() -> str:
    """
    Retrieve the database URL from the environment variables or construct it
    from separate components if the `DATABASE_URL` is not set.

    Raises:
        ValueError: If neither `DATABASE_URL` nor the individual components are set.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        logger.info("Using DATABASE_URL from environment.")
        return database_url

    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")

    if all([db_host, db_name, db_user, db_password]):
        logger.info("Constructing DATABASE_URL from individual components.")
        return f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

    logger.error(
        "DATABASE_URL is not set, and individual database variables "
        "(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD) are missing."
    )
    raise ValueError(
        "You must set either DATABASE_URL or the individual variables  "
        "database components: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD."
    )

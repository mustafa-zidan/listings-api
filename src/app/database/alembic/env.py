import asyncio
import os
import logging
from logging.config import fileConfig
from typing import Iterable, List, Optional

from alembic.operations import MigrationScript
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context as migration_context

from app.models.base import Base


def setup_logging():
    if migration_context.config.config_file_name is not None:
        fileConfig(migration_context.config.config_file_name)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    return logger


logger = setup_logging()

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
        "DATABASE_URL is not set, and individual database variables (DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD) are missing."
    )
    raise ValueError(
        "You must set either DATABASE_URL or the individual variables  database components: DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD."
    )


def setup_alembic_config() -> None:
    """
    Set up the Alembic configuration with the database URL.
    """
    database_url = get_database_url()
    migration_context.config.set_main_option("sqlalchemy.url", database_url)
    migration_context.configure(
        url=database_url,
        target_metadata=Base.metadata,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )
    logger.info("Alembic configuration set up with the database URL.")



def process_revision_directives(
        context: MigrationContext,
        revision: str | Iterable[str | None] | Iterable[str],
        directives: List[MigrationScript],
) -> None:
    """
    Assigns a sequential, zero-padded revision ID to an Alembic migration script.

    Args:
        context (MigrationContext): Alembic's migration context, carrying configuration details.
        revision (str | Iterable[str | None] | Iterable[str]): The revision(s) being processed.
        directives (List[MigrationScript]): The migration scripts being processed.

    Example:
        If the current head revision is `0003`, this function assigns `0004` as the next ID.
    """
    migration_script = directives[0]
    head_revision = ScriptDirectory.from_config(context.config).get_current_head()
    new_rev_id = 1 if head_revision is None else int(head_revision.lstrip("0")) + 1
    migration_script.rev_id = f"{new_rev_id:04}"
    logger.info(f"Generated new migration revision ID: {migration_script.rev_id}")


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This is ideal for environments without direct database access. The migrations are
    generated as raw SQL strings.
    """
    logger.info("Running migrations in offline mode.")
    migration_context.configure(
        url=migration_context.config.get_main_option("sqlalchemy.url"),
        target_metadata=Base.metadata,
        literal_binds=True,
        render_as_batch=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )
    with migration_context.begin_transaction():
        migration_context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """
    Run migrations using an active database connection.

    Args:
        connection (Connection): A SQLAlchemy connection to the database.
    """
    logger.info("Running migrations using an active connection.")
    migration_context.configure(connection=connection, target_metadata=Base.metadata)
    with migration_context.begin_transaction():
        migration_context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in an asynchronous context.

    Useful for applications using an async database engine.
    """
    logger.info("Running migrations in async mode.")
    connectable = async_engine_from_config(
        migration_context.config.get_section(
            migration_context.config.config_ini_section, {}
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()
    logger.info("Async migrations completed.")


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Connects to the database and applies migrations directly.
    """
    logger.info("Running migrations in online mode.")
    asyncio.run(run_async_migrations())



try:
    logger.info("Starting migration script.")
    setup_alembic_config()
    if migration_context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
except Exception as e:
    logger.error(f"An error occurred during migration: {e}")
    raise
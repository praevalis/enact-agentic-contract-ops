import asyncio
from logging.config import fileConfig

from alembic import context
from alembic.runtime.environment import NameFilterParentNames, NameFilterType
from enact.platform.database import metadata
from enact.platform.settings import Settings
from sqlalchemy import Connection, pool, text
from sqlalchemy.ext.asyncio import async_engine_from_config

APPLICATION_SCHEMA = 'enact'
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = metadata


def include_name(
    name: str | None,
    object_type: NameFilterType,
    parent_names: NameFilterParentNames,
) -> bool:
    """Limit Alembic reflection to the Enact-owned schema.

    Args:
        name: Reflected database object name.
        object_type: Kind of object being reflected.
        parent_names: Names of the reflected object's parent objects.

    Returns:
        Whether Alembic should include the object during autogeneration.
    """
    return object_type != 'schema' or name == APPLICATION_SCHEMA


def get_migration_settings() -> Settings:
    """Load settings for the privileged migration process.

    Returns:
        Validated settings supplied by the migration process environment.

    Raises:
        pydantic.ValidationError: If required migration configuration is missing or invalid.
    """
    # BaseSettings supplies required fields from the migration process environment.
    return Settings()  # pyright: ignore[reportCallIssue]


def run_migrations_offline() -> None:
    """Run migrations without creating a live database connection."""
    context.configure(
        url=get_migration_settings().database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
        compare_server_default=True,
        include_name=include_name,
        include_schemas=True,
        version_table_schema=APPLICATION_SCHEMA,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations through an established synchronous connection.

    Args:
        connection: Connection on which to assume the owner role and run migrations.
    """
    connection.execute(text('SET LOCAL ROLE enact_owner'))
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
        include_name=include_name,
        include_schemas=True,
        version_table_schema=APPLICATION_SCHEMA,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an asynchronous migration engine and run online migrations."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration['sqlalchemy.url'] = get_migration_settings().database_url
    connectable = async_engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run online migrations through the asynchronous database driver."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base

# Import all models so their metadata is registered with Base
import app.models.user           # noqa: F401
import app.models.goal           # noqa: F401
import app.models.nutrition_log  # noqa: F401
import app.models.restriction    # noqa: F401
import app.models.recommendation  # noqa: F401
import app.models.food             # noqa: F401

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

TARGET_METADATA = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in offline mode (generates SQL without a live DB)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=TARGET_METADATA,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Execute migrations synchronously within an async connection."""
    context.configure(connection=connection, target_metadata=TARGET_METADATA)
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations against a live async database connection."""
    connectable = create_async_engine(settings.DATABASE_URL)
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())

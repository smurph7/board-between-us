from functools import lru_cache

from sqlalchemy import Engine, create_engine, text

from app.config import get_settings


@lru_cache
def get_engine() -> Engine:
    """Create and cache the application's database engine."""
    settings = get_settings()
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
    )


def check_database_connection() -> int:
    """Run a minimal query to verify database connectivity."""
    with get_engine().connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return result.scalar_one()
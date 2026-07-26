from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from app.config import get_settings


def _database_identity(database_url: str) -> tuple[str, str | None, str | None]:
    """Return the database endpoint without passwords or pooler differences."""
    parsed_url = make_url(database_url)
    host = (parsed_url.host or "").replace("-pooler", "")

    return host, parsed_url.database, parsed_url.username


@pytest.fixture(scope="session")
def test_engine() -> Iterator[Engine]:
    """Create an engine connected only to the isolated test database."""
    settings = get_settings()

    if not settings.database_test_url:
        pytest.fail(
            "DATABASE_TEST_URL is missing. "
            "Add the Neon test-branch URL to .env."
        )

    if _database_identity(settings.database_test_url) == _database_identity(
        settings.database_url
    ):
        pytest.fail(
            "DATABASE_TEST_URL points to the application database. "
            "Use a separate Neon branch."
        )

    engine = create_engine(
        settings.database_test_url,
        pool_pre_ping=True,
    )

    required_tables = {
        "alembic_version",
        "games",
        "players",
        "moves",
    }
    existing_tables = set(inspect(engine).get_table_names())
    missing_tables = required_tables - existing_tables

    if missing_tables:
        pytest.fail(
            "The test database is missing migrations for: "
            f"{', '.join(sorted(missing_tables))}. "
            "Run USE_TEST_DATABASE=1 alembic upgrade head."
        )

    yield engine

    engine.dispose()


@pytest.fixture
def db_session(test_engine: Engine) -> Iterator[Session]:
    """Provide a database session whose changes are rolled back after each test."""
    connection = test_engine.connect()
    outer_transaction = connection.begin()

    session = Session(
        bind=connection,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )

    try:
        yield session
    finally:
        session.close()
        outer_transaction.rollback()
        connection.close()
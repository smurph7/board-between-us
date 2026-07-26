from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from app.database.client import get_engine


SessionFactory = sessionmaker(
    bind=get_engine(),
    class_=Session,
    expire_on_commit=False,
)


@contextmanager
def database_session() -> Iterator[Session]:
    """Provide a database session with commit and rollback handling."""
    session = SessionFactory()

    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
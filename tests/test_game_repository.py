from uuid import uuid4

from app.repositories.game_repository import get_game_version
from app.services.game_service import create_standard_game


def test_get_game_version_returns_current_version(db_session) -> None:
    created_game = create_standard_game(session=db_session)

    version = get_game_version(
        session=db_session,
        game_id=created_game.game.id,
    )

    assert version == created_game.game.version
    

def test_get_game_version_returns_none_for_missing_game(db_session) -> None:
    version = get_game_version(
        session=db_session,
        game_id=uuid4(),
    )

    assert version is None
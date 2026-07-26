from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.game import Game


def create_game(
    session: Session,
    *,
    board_state: dict[str, str],
    name: str | None = None,
    current_turn: str = "white",
    status: str = "active",
) -> Game:
    """Create a game in the current database transaction."""
    game = Game(
        id=uuid4(),
        name=name,
        board_state=board_state,
        current_turn=current_turn,
        status=status,
    )

    session.add(game)
    session.flush()

    return game


def get_game(session: Session, game_id: UUID) -> Game | None:
    """Return a game by ID, or None if it does not exist."""
    return session.get(Game, game_id)
from sqlalchemy.orm import Session

from app.models.game import Game
from app.repositories.game_repository import create_game
from app.utils.board import create_standard_board


def create_standard_game(
    session: Session,
    *,
    name: str | None = None,
) -> Game:
    """Create an active game using the standard starting position."""
    return create_game(
        session,
        name=name,
        board_state=create_standard_board(),
        current_turn="white",
        status="active",
    )
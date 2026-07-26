from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.player import Player
from app.repositories.game_repository import create_game
from app.repositories.player_repository import create_player
from app.services.token_service import generate_access_token, hash_access_token
from app.utils.board import create_standard_board


@dataclass(frozen=True)
class CreatedGame:
    """A newly created game and its private player credentials."""

    game: Game
    white_player: Player
    black_player: Player
    white_access_token: str
    black_access_token: str


def create_standard_game(
    session: Session,
    *,
    name: str | None = None,
    white_display_name: str | None = None,
    black_display_name: str | None = None,
) -> CreatedGame:
    """Create a standard game with White and Black player seats."""
    game = create_game(
        session,
        name=name,
        board_state=create_standard_board(),
        current_turn="white",
        status="active",
    )

    white_access_token = generate_access_token()
    black_access_token = generate_access_token()

    white_player = create_player(
        session,
        game_id=game.id,
        colour="white",
        display_name=white_display_name,
        access_token_hash=hash_access_token(white_access_token),
    )

    black_player = create_player(
        session,
        game_id=game.id,
        colour="black",
        display_name=black_display_name,
        access_token_hash=hash_access_token(black_access_token),
    )

    return CreatedGame(
        game=game,
        white_player=white_player,
        black_player=black_player,
        white_access_token=white_access_token,
        black_access_token=black_access_token,
    )
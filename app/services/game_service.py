from dataclasses import dataclass
from uuid import UUID
from typing import Literal

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.game import Game
from app.models.player import Player
from app.repositories.game_repository import (
    create_game,
    delete_game, 
    get_game,
    get_game_for_update,
)
from app.repositories.player_repository import (
    create_player,
    get_player_by_token_hash,
)
from app.services.move_service import GameNotFoundError, StaleGameError
from app.services.token_service import generate_access_token, hash_access_token
from app.utils.board import BoardState, Colour, create_standard_board

class GameNotInSetupError(Exception):
    """Raised when a setup-only operation targets an active game."""
    
@dataclass(frozen=True)
class CreatedGame:
    """A newly created game and its private player credentials."""

    game: Game
    white_player: Player
    black_player: Player
    white_access_token: str
    black_access_token: str

@dataclass(frozen=True)
class CreatedGameLinks:
    game: Game
    creator_colour: Colour
    creator_url: str
    opponent_url: str
    

def create_standard_game(
    session: Session,
    *,
    name: str | None = None,
    white_display_name: str | None = None,
    black_display_name: str | None = None,
    status: str = "active",
) -> CreatedGame:
    """Create a standard game with White and Black player seats."""
    game = create_game(
        session,
        name=name,
        board_state=create_standard_board(),
        current_turn="white",
        status=status,
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


type StartMode = Literal["standard", "setup"]


def create_game_for_players(
    session: Session,
    *,
    creator_display_name: str,
    opponent_display_name: str | None,
    creator_colour: Colour,
    app_base_url: str,
    name: str | None = None,
    start_mode: StartMode = "standard",
) -> CreatedGameLinks:
    """Create a standard game and assign private links by creator colour."""
    board_state = create_standard_board()
    status = "setup" if start_mode == "setup" else "active"
    
    if creator_colour == "white":
        white_display_name = creator_display_name
        black_display_name = opponent_display_name
    else:
        white_display_name = opponent_display_name
        black_display_name = creator_display_name
    
    created_game = create_standard_game(
        session,
        name=name,
        white_display_name=white_display_name,
        black_display_name=black_display_name,
        status=status,
    )
    
    if creator_colour == "white":
        creator_token = created_game.white_access_token
        opponent_token = created_game.black_access_token
    else:
        creator_token = created_game.black_access_token
        opponent_token = created_game.white_access_token
        
    base_url = app_base_url.rstrip("/")
    creator_url = (
        f"{base_url}/play/"
        f"{created_game.game.id}/{creator_token}"
    )

    opponent_url = (
        f"{base_url}/play/"
        f"{created_game.game.id}/{opponent_token}"
    )
    
    return CreatedGameLinks(
        game=created_game.game,
        creator_colour=creator_colour,
        creator_url=creator_url,
        opponent_url=opponent_url,      
    )


@dataclass(frozen=True)
class PlayerGame:
    """A game loaded through one player's private access token."""

    game: Game
    player: Player


def load_player_game(
    session: Session,
    *,
    game_id: UUID,
    access_token: str,
) -> PlayerGame | None:
    """Load a game and player using a private raw access token."""
    player = get_player_by_token_hash(
        session,
        hash_access_token(access_token),
    )

    if player is None or player.game_id != game_id:
        return None

    game = get_game(session, game_id)

    if game is None:
        return None

    return PlayerGame(
        game=game,
        player=player,
    )
    
    
def confirm_game_setup(
    session: Session,
    *,
    game_id: UUID,
    board_state: BoardState,
    next_turn: Colour,
    expected_version: int,
) -> Game:
    """Save a configured starting position and activate the game."""
    game = get_game_for_update(session, game_id)
    
    if game is None: 
        raise GameNotFoundError("Game does not exist") 
    
    if game.version != expected_version:
        raise StaleGameError("The board changed on another device")
    
    game.board_state = dict(board_state)
    game.current_turn = next_turn
    game.status = "active"
    game.version += 1
    
    session.flush()
    
    return game


def cancel_game_setup(
    session: Session,
    *,
    game_id: UUID,
    expected_version: int,
) -> None:
    """Delete a game whose initial setup has not been confirmed."""
    game = get_game_for_update(session, game_id)

    if game is None:
        raise GameNotFoundError("Game does not exist")

    if game.version != expected_version:
        raise StaleGameError("The board changed on another device")

    if game.status != "setup":
        raise GameNotInSetupError(
            "This game setup has already finished"
        )

    delete_game(session, game)
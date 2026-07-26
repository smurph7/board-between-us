from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from typing import cast

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.persisted_move import Move
from app.models.move import MoveRecord
from app.repositories.game_repository import get_game_for_update
from app.repositories.move_repository import (
    create_move,
    get_next_sequence_number,
    list_moves
)
from app.repositories.player_repository import get_player
from app.utils.board import apply_move, next_turn, piece_belongs_to, Colour

class MoveError(Exception):
    """Base error for rejected moves."""


class GameNotFoundError(MoveError):
    """Raised when the requested game does not exist."""


class PlayerNotFoundError(MoveError):
    """Raised when the requested player does not exist."""


class WrongTurnError(MoveError):
    """Raised when a player attempts to move out of turn."""


class StaleGameError(MoveError):
    """Raised when the client has an outdated game version."""


class InvalidMoveError(MoveError):
    """Raised when a requested board move is invalid."""


@dataclass(frozen=True)
class CompletedMove:
    """The updated game and persisted move-history row."""

    game: Game
    move: Move


def make_move(
    session: Session,
    *,
    game_id: UUID,
    player_id: UUID,
    from_square: str,
    to_square: str,
    expected_version: int,
) -> CompletedMove:
    """Apply and persist one ordinary move."""
    game = get_game_for_update(session, game_id)

    if game is None:
        raise GameNotFoundError("Game does not exist")

    player = get_player(session, player_id)

    if player is None or player.game_id != game.id:
        raise PlayerNotFoundError("Player does not belong to this game")

    if game.version != expected_version:
        raise StaleGameError(
            "The board changed on another device"
        )

    if player.colour != game.current_turn:
        raise WrongTurnError(
            f"It is currently {game.current_turn}'s turn"
        )

    moving_piece = game.board_state.get(from_square)

    if moving_piece is None:
        raise InvalidMoveError(
            f"No piece exists at {from_square}"
        )

    if not piece_belongs_to(moving_piece, player.colour):
        raise InvalidMoveError(
            "The selected piece belongs to the other player"
        )

    destination_piece = game.board_state.get(to_square)

    if (
        destination_piece is not None
        and piece_belongs_to(destination_piece, player.colour)
    ):
        raise InvalidMoveError(
            "A player cannot capture their own piece"
        )

    board_before = game.board_state.copy()

    try:
        board_after, captured_piece = apply_move(
            board_before,
            from_square,
            to_square,
        )
    except ValueError as error:
        raise InvalidMoveError(str(error)) from error

    resulting_turn = next_turn(game.current_turn)
    sequence_number = get_next_sequence_number(
        session,
        game.id,
    )

    move = create_move(
        session,
        game_id=game.id,
        player_id=player.id,
        sequence_number=sequence_number,
        move_type="capture" if captured_piece else "move",
        piece=moving_piece,
        from_square=from_square,
        to_square=to_square,
        captured_piece=captured_piece,
        board_state_before=board_before,
        board_state_after=board_after,
        previous_turn=game.current_turn,
        resulting_turn=resulting_turn,
    )

    game.board_state = board_after
    game.current_turn = resulting_turn
    game.version += 1
    game.updated_at = datetime.now(timezone.utc)

    session.flush()

    return CompletedMove(
        game=game,
        move=move,
    )
    

def get_move_history(
    session: Session,
    game_id: UUID,
) -> list[MoveRecord]:
    """Return persisted ordinary moves in the UI's history format."""
    records: list[MoveRecord] = []

    for move in list_moves(session, game_id):
        if (
            move.piece is None
            or move.from_square is None
            or move.to_square is None
        ):
            continue

        records.append(
            MoveRecord(
                number=move.sequence_number,
                colour=cast(Colour, move.previous_turn),
                piece=move.piece,
                from_square=move.from_square,
                to_square=move.to_square,
                captured_piece=move.captured_piece,
            )
        )

    return records
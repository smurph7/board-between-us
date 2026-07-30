from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID
from typing import cast

from sqlalchemy.orm import Session

from app.models.game import Game
from app.models.persisted_move import Move
from app.models.move import MoveRecord, MoveType
from app.repositories.game_repository import get_game_for_update
from app.repositories.move_repository import (
    create_move,
    get_next_sequence_number,
    list_moves,
    get_latest_undoable_event,
)
from app.repositories.player_repository import get_player
from app.utils.board import (
    CastleSide,
    Colour,
    apply_castle,
    apply_move,
    get_castling_movements,
    next_turn,
    piece_belongs_to,
)
from app.utils.formatting import describe_board_changes

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

class NoUndoableEventError(MoveError):
    """Raised when a game has no event which can be undone."""

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
    

def make_castle(
    session: Session,
    *,
    game_id: UUID,
    player_id: UUID,
    side: CastleSide,
    expected_version: int,
) -> CompletedMove:
    """Apply and persist one compound castling action."""

    game = get_game_for_update(session, game_id)

    if game is None:
        raise GameNotFoundError("Game does not exist")

    player = get_player(session, player_id)

    if player is None or player.game_id != game.id:
        raise PlayerNotFoundError(
            "Player does not belong to this game"
        )

    if game.version != expected_version:
        raise StaleGameError(
            "The board changed on another device"
        )

    if player.colour != game.current_turn:
        raise WrongTurnError(
            f"It is currently {game.current_turn}'s turn"
        )

    colour = cast(Colour, player.colour)
    board_before = game.board_state.copy()

    try:
        board_after = apply_castle(
            board_before,
            colour=colour,
            side=side,
        )
    except ValueError as error:
        raise InvalidMoveError(str(error)) from error

    king_move, rook_move = get_castling_movements(
        colour,
        side,
    )

    resulting_turn = next_turn(
        cast(Colour, game.current_turn)
    )

    sequence_number = get_next_sequence_number(
        session,
        game.id,
    )

    move = create_move(
        session,
        game_id=game.id,
        player_id=player.id,
        sequence_number=sequence_number,
        move_type="castle",
        piece=king_move.piece,
        from_square=king_move.from_square,
        to_square=king_move.to_square,
        captured_piece=None,
        changes=[
            {
                "piece": king_move.piece,
                "from": king_move.from_square,
                "to": king_move.to_square,
            },
            {
                "piece": rook_move.piece,
                "from": rook_move.from_square,
                "to": rook_move.to_square,
            },
        ],
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
  

def undo_latest_event(
    session: Session,
    *,
    game_id: UUID,
    player_id: UUID,
    expected_version: int,
) -> CompletedMove:
    """Undo the latest active move, castle, or correction."""

    game = get_game_for_update(session, game_id)

    if game is None:
        raise GameNotFoundError("Game does not exist")

    player = get_player(session, player_id)

    if player is None or player.game_id != game.id:
        raise PlayerNotFoundError(
            "Player does not belong to this game"
        )

    if game.version != expected_version:
        raise StaleGameError(
            "The board changed on another device"
        )

    if game.status != "active":
        raise InvalidMoveError(
            "Only active games can be undone"
        )

    target = get_latest_undoable_event(
        session,
        game.id,
    )

    if target is None:
        raise NoUndoableEventError(
            "There is nothing to undo"
        )

    if (
        game.board_state != target.board_state_after
        or game.current_turn != target.resulting_turn
    ):
        raise InvalidMoveError(
            "The latest history event does not match "
            "the current game state"
        )

    board_before = game.board_state.copy()
    board_after = target.board_state_before.copy()
    restored_turn = cast(Colour, target.previous_turn)

    sequence_number = get_next_sequence_number(
        session,
        game.id,
    )

    undo_move = create_move(
        session,
        game_id=game.id,
        player_id=player.id,
        sequence_number=sequence_number,
        move_type="undo",
        piece=None,
        from_square=None,
        to_square=None,
        captured_piece=None,
        changes=[
            {
                "undone_move_id": str(target.id),
                "undone_sequence_number": target.sequence_number,
                "undone_move_type": target.move_type,
            }
        ],
        board_state_before=board_before,
        board_state_after=board_after,
        previous_turn=game.current_turn,
        resulting_turn=restored_turn,
    )

    target.is_undone = True

    game.board_state = board_after
    game.current_turn = restored_turn
    game.version += 1
    game.updated_at = datetime.now(timezone.utc)

    session.flush()

    return CompletedMove(
        game=game,
        move=undo_move,
    )
      

def get_move_history(
    session: Session,
    game_id: UUID,
) -> list[MoveRecord]:
    """Return persisted game events in the UI's history format."""

    records: list[MoveRecord] = []
    player_colours: dict[UUID, Colour] = {}

    for move in list_moves(session, game_id):
        actor_colour = player_colours.get(move.player_id)

        if actor_colour is None:
            player = get_player(session, move.player_id)

            if player is None:
                continue

            actor_colour = cast(Colour, player.colour)
            player_colours[move.player_id] = actor_colour

        move_type = cast(MoveType, move.move_type)
        
        if move_type == "undo":
            undo_details = move.changes[0] if move.changes else {}

            records.append(
                MoveRecord(
                    number=move.sequence_number,
                    colour=actor_colour,
                    move_type=move_type,
                    piece=None,
                    from_square=None,
                    to_square=None,
                    captured_piece=None,
                    previous_turn=cast(
                        Colour,
                        move.previous_turn,
                    ),
                    resulting_turn=cast(
                        Colour,
                        move.resulting_turn,
                    ),
                    undo_target_number=cast(
                        int | None,
                        undo_details.get("undone_sequence_number"),
                    ),
                    undo_target_type=cast(
                        str | None,
                        undo_details.get("undone_move_type"),
                    ),
                    is_undone=move.is_undone,
                )
            )
            continue

        if move_type == "correction":
            records.append(
                MoveRecord(
                    number=move.sequence_number,
                    colour=actor_colour,
                    move_type=move_type,
                    piece=None,
                    from_square=None,
                    to_square=None,
                    captured_piece=None,
                    correction_changes=describe_board_changes(
                        move.board_state_before,
                        move.board_state_after,
                    ),
                    previous_turn=cast(
                        Colour,
                        move.previous_turn,
                    ),
                    resulting_turn=cast(
                        Colour,
                        move.resulting_turn,
                    ),
                    is_undone=move.is_undone,
                )
            )
            continue

        if (
            move.piece is None
            or move.from_square is None
            or move.to_square is None
        ):
            continue

        castle_side: CastleSide | None = None

        if move_type == "castle":
            castle_side = (
                "kingside"
                if move.to_square in {"g1", "g8"}
                else "queenside"
            )

        records.append(
            MoveRecord(
                number=move.sequence_number,
                colour=actor_colour,
                move_type=move_type,
                piece=move.piece,
                from_square=move.from_square,
                to_square=move.to_square,
                captured_piece=move.captured_piece,
                castle_side=castle_side,
                previous_turn=cast(
                    Colour,
                    move.previous_turn,
                ),
                resulting_turn=cast(
                    Colour,
                    move.resulting_turn,
                ),
                is_undone=move.is_undone,
            )
        )

    return records
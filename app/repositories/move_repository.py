from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from app.models.move import Move


def create_move(
    session: Session,
    *,
    game_id: UUID,
    player_id: UUID,
    sequence_number: int,
    move_type: str,
    piece: str | None,
    from_square: str | None,
    to_square: str | None,
    captured_piece: str | None,
    board_state_before: dict[str, str],
    board_state_after: dict[str, str],
    previous_turn: str,
    resulting_turn: str,
    changes: list[dict[str, Any]] | None = None,
) -> Move:
    """Create a move-history row in the current transaction."""
    move = Move(
        id=uuid4(),
        game_id=game_id,
        player_id=player_id,
        sequence_number=sequence_number,
        move_type=move_type,
        piece=piece,
        from_square=from_square,
        to_square=to_square,
        captured_piece=captured_piece,
        changes=changes or [],
        board_state_before=board_state_before,
        board_state_after=board_state_after,
        previous_turn=previous_turn,
        resulting_turn=resulting_turn,
    )

    session.add(move)
    session.flush()

    return move
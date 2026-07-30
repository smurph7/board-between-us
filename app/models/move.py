from dataclasses import dataclass
from typing import Literal

from app.utils.board import CastleSide, Colour, Piece, Square


MoveType = Literal[
    "move",
    "capture",
    "castle",
    "correction",
    "undo",
]


@dataclass
class MoveRecord:
    """Describe one completed local move."""

    number: int
    colour: Colour
    move_type: MoveType
    piece: Piece | None
    from_square: Square | None
    to_square: Square | None
    captured_piece: Piece | None
    castle_side: CastleSide | None = None
    correction_changes: tuple[str, ...] = ()
    previous_turn: Colour | None = None
    resulting_turn: Colour | None = None
    is_undone: bool = False
    undo_target_number: int | None = None
    undo_target_type: str | None = None
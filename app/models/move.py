from dataclasses import dataclass
from typing import Literal

from app.utils.board import CastleSide, Colour, Piece, Square


MoveType = Literal["move", "capture", "castle"]


@dataclass
class MoveRecord:
    """Describe one completed local move."""

    number: int
    colour: Colour
    move_type: MoveType
    piece: Piece
    from_square: Square
    to_square: Square
    captured_piece: Piece | None
    castle_side: CastleSide | None = None
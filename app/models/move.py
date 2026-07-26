from dataclasses import dataclass

from app.utils.board import Colour, Piece, Square


@dataclass
class MoveRecord:
    """Describe one completed local move."""

    number: int
    colour: Colour
    piece: Piece
    from_square: Square
    to_square: Square
    captured_piece: Piece | None
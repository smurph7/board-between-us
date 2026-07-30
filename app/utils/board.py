from typing import Literal
from dataclasses import dataclass
from typing import Literal

type Square = str
type Piece = str
type BoardState = dict[Square, Piece]

Colour = Literal["white", "black"]
CastleSide = Literal["kingside", "queenside"]

_CASTLING_SQUARES: dict[
    tuple[Colour, CastleSide],
    tuple[Square, Square, Square, Square],
] = {
    ("white", "kingside"): ("e1", "g1", "h1", "f1"),
    ("white", "queenside"): ("e1", "c1", "a1", "d1"),
    ("black", "kingside"): ("e8", "g8", "h8", "f8"),
    ("black", "queenside"): ("e8", "c8", "a8", "d8"),
}


@dataclass(frozen=True)
class PieceMovement:
    """Describe one piece moving between two squares."""

    piece: Piece
    from_square: Square
    to_square: Square


def create_standard_board() -> BoardState:
    """Return a new board containing the standard chess starting position."""

    board: BoardState = {}

    white_back_rank = [
        "white_rook",
        "white_knight",
        "white_bishop",
        "white_queen",
        "white_king",
        "white_bishop",
        "white_knight",
        "white_rook",
    ]

    black_back_rank = [
        "black_rook",
        "black_knight",
        "black_bishop",
        "black_queen",
        "black_king",
        "black_bishop",
        "black_knight",
        "black_rook",
    ]

    files = "abcdefgh"

    for index, file in enumerate(files):
        board[f"{file}1"] = white_back_rank[index]
        board[f"{file}2"] = "white_pawn"

        board[f"{file}7"] = "black_pawn"
        board[f"{file}8"] = black_back_rank[index]

    return board


def piece_belongs_to(piece: Piece, colour: Colour) -> bool:
    """Return whether a piece belongs to the specified colour."""
    return piece.startswith(f"{colour}_")


def next_turn(current_turn: Colour) -> Colour:
    """Return the colour whose turn follows the current turn."""
    return {"white": "black", "black": "white"}[current_turn]


def apply_move(
    board: BoardState,
    from_square: Square,
    to_square: Square,
) -> tuple[BoardState, Piece | None]:
    """Move a piece without mutating the input board or validating chess legality."""

    if from_square == to_square:
        raise ValueError("Source and destination must be different")

    new_board = board.copy()

    if from_square not in new_board:
        raise ValueError(f"No piece at {from_square}")
    
    captured_piece = new_board.get(to_square)
    moving_piece = new_board.pop(from_square)
    
    new_board[to_square] = moving_piece
    
    return new_board, captured_piece


def apply_castle(
    board: BoardState,
    colour: Colour,
    side: CastleSide,
) -> BoardState:
    """Move the king and rook for castling without mutating the input board."""

    king_move, rook_move = get_castling_movements(
        colour,
        side,
    )

    expected_king = f"{colour}_king"
    expected_rook = f"{colour}_rook"

    if board.get(king_move.from_square) != expected_king:
        raise ValueError(
            f"Expected {expected_king} at {king_move.from_square}"
        )

    if board.get(rook_move.from_square) != expected_rook:
        raise ValueError(
            f"Expected {expected_rook} at {rook_move.from_square}"
        )

    occupied_destinations = [
        square
        for square in (king_move.to_square, rook_move.to_square)
        if square in board
    ]

    if occupied_destinations:
        occupied_squares = ", ".join(occupied_destinations)
        raise ValueError(
            f"Castling destination occupied: {occupied_squares}"
        )

    new_board = board.copy()

    king = new_board.pop(king_move.from_square)
    rook = new_board.pop(rook_move.from_square)

    new_board[king_move.to_square] = king
    new_board[rook_move.to_square] = rook

    return new_board


def can_castle(
    board: BoardState,
    colour: Colour,
    side: CastleSide,
) -> bool:
    """Return whether the board can safely record the requested castle."""
    king_move, rook_move = get_castling_movements(
        colour,
        side,
    )

    return (
        board.get(king_move.from_square) == f"{colour}_king"
        and board.get(rook_move.from_square) == f"{colour}_rook"
        and king_move.to_square not in board
        and rook_move.to_square not in board
    )
    
    
def get_castling_movements(
    colour: Colour,
    side: CastleSide,
) -> tuple[PieceMovement, PieceMovement]:
    """Return the king and rook movements for a castle."""

    king_from, king_to, rook_from, rook_to = _CASTLING_SQUARES[
        (colour, side)
    ]

    return (
        PieceMovement(
            piece=f"{colour}_king",
            from_square=king_from,
            to_square=king_to,
        ),
        PieceMovement(
            piece=f"{colour}_rook",
            from_square=rook_from,
            to_square=rook_to,
        ),
    )
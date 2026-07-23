type Square = str
type Piece = str
type BoardState = dict[Square, Piece]

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

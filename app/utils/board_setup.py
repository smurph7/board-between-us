from app.utils.board import BoardState, Piece, Square


def place_piece(
    board: BoardState,
    square: Square,
    piece: Piece,
) -> BoardState:
    """Return a new board with the piece placed on the square."""
    return {
        **board,
        square: piece,
    }


def remove_piece(
    board: BoardState,
    square: Square,
) -> BoardState:
    """Return a new board without a piece on the specified square."""
    return {
        existing_square: existing_piece
        for existing_square, existing_piece in board.items()
        if existing_square != square
    }
    

def move_piece(
    board: BoardState,
    from_square: Square,
    to_square: Square,
) -> BoardState:
    """Return a new board with a setup piece moved between squares."""
    piece = board[from_square]
    updated_board = remove_piece(board, from_square)
    return place_piece(updated_board, to_square, piece)
from app.utils.board import BoardState, Piece, Square, create_standard_board
from app.utils.board_setup import clear_board, move_piece, place_piece, remove_piece, reset_board


def test_place_piece_adds_piece_without_mutating_original_board() -> None:
    original_board: BoardState = {
        "e1": "white_king",
    }

    updated_board = place_piece(
        original_board,
        "d4",
        "black_queen",
    )

    assert updated_board == {
        "e1": "white_king",
        "d4": "black_queen",
    }
    assert original_board == {
        "e1": "white_king",
    }
    
    
def test_place_piece_replaces_existing_piece() -> None:
    original_board: BoardState = {
        "e1": "white_king",
        "d4": "white_pawn",
    }

    updated_board = place_piece(
        original_board,
        "d4",
        "black_queen",
    )

    assert updated_board == {
        "e1": "white_king",
        "d4": "black_queen",
    }
    assert original_board == {
        "e1": "white_king",
        "d4": "white_pawn",
    }
    

def test_remove_piece_removes_piece_without_mutating_original_board() -> None:
    original_board: BoardState = {
        "e1": "white_king",
        "d4": "black_queen",
    }

    updated_board = remove_piece(original_board, "d4")

    assert updated_board == {
        "e1": "white_king",
    }
    assert original_board == {
        "e1": "white_king",
        "d4": "black_queen",
    }
    
    
def test_remove_piece_from_empty_square_returns_unchanged_copy() -> None:
    original_board: BoardState = {
        "e1": "white_king",
    }

    updated_board = remove_piece(original_board, "d4")

    assert updated_board == original_board
    assert updated_board is not original_board
    

def test_move_piece_moves_piece_without_mutating_original_board() -> None:
    original_board: BoardState = {
        "e1": "white_king",
        "d4": "black_queen",
    }

    updated_board = move_piece(
        original_board,
        from_square="d4",
        to_square="d5",
    )

    assert updated_board == {
        "e1": "white_king",
        "d5": "black_queen",
    }
    assert original_board == {
        "e1": "white_king",
        "d4": "black_queen",
    }
    
    
def test_move_piece_replaces_piece_on_destination_square() -> None:
    original_board: BoardState = {
        "e1": "white_king",
        "d4": "black_queen",
        "d5": "white_pawn",
    }

    updated_board = move_piece(
        original_board,
        from_square="d4",
        to_square="d5",
    )

    assert updated_board == {
        "e1": "white_king",
        "d5": "black_queen",
    }
    assert original_board == {
        "e1": "white_king",
        "d4": "black_queen",
        "d5": "white_pawn",
    }
    
    
def test_clear_board_returns_empty_board_without_mutating_original() -> None:
    original_board: BoardState = {
        "e1": "white_king",
        "d4": "black_queen",
    }

    updated_board = clear_board(original_board)

    assert updated_board == {}
    assert original_board == {
        "e1": "white_king",
        "d4": "black_queen",
    }
    
    
def test_reset_board_returns_standard_board_without_mutating_original() -> None:
    original_board: BoardState = {
        "e1": "white_king",
        "d4": "black_queen",
    }

    updated_board = reset_board(original_board)

    assert updated_board == create_standard_board()
    assert original_board == {
        "e1": "white_king",
        "d4": "black_queen",
    }
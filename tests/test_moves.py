import pytest
from app.utils.board import apply_move, create_standard_board, next_turn, piece_belongs_to

def test_standard_board_has_expected_pieces():
    board = create_standard_board()

    assert len(board) == 32
    assert board["a1"] == "white_rook"
    assert board["e1"] == "white_king"
    assert board["e8"] == "black_king"
    assert board["a8"] == "black_rook"

def test_ordinary_move_updates_board():
    board = {
        "e2": "white_pawn",
    }

    updated_board, captured_piece = apply_move(
        board,
        from_square="e2",
        to_square="e4",
    )

    assert updated_board == {
        "e4": "white_pawn",
    }
    assert captured_piece is None

def test_capture_returns_removed_piece():
    board = {
        "e4": "white_pawn",
        "d5": "black_pawn",
    }

    updated_board, captured_piece = apply_move(
        board,
        from_square="e4",
        to_square="d5",
    )

    assert updated_board == {
        "d5": "white_pawn",
    }
    assert captured_piece == "black_pawn"


def test_move_does_not_mutate_original_board():
    board = {
        "e2": "white_pawn",
    }

    updated_board, _ = apply_move(
        board,
        from_square="e2",
        to_square="e4",
    )

    assert board == {
        "e2": "white_pawn",
    }
    assert updated_board == {
        "e4": "white_pawn",
    }
    assert updated_board is not board

def test_empty_source_is_rejected():
    board = {
        "e2": "white_pawn",
    }

    with pytest.raises(ValueError):
        apply_move(
            board,
            from_square="e4",
            to_square="e5",
        )

def test_same_source_and_destination_is_rejected():
    board = {"e2": "white_pawn"}

    with pytest.raises(ValueError):
        apply_move(
            board,
            from_square="e2",
            to_square="e2",
        )

def test_piece_belongs_to_colour():
    assert piece_belongs_to("white_pawn", "white")
    assert not piece_belongs_to("black_pawn", "white")


def test_next_turn_alternates_colour():
    assert next_turn("white") == "black"
    assert next_turn("black") == "white"
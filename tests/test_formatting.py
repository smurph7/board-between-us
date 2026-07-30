from app.models.move import MoveRecord
from app.utils.formatting import (
    describe_board_changes,
    format_move,
)


def test_formats_ordinary_move():
    move = MoveRecord(
        number=1,
        colour='white', 
        move_type="move",
        piece='white_pawn', 
        from_square='e2', 
        to_square='e4', 
        captured_piece=None
    )
    assert format_move(move) == "1. White: pawn e2 → e4"


def test_formats_capture():
    move = MoveRecord(
        number=2,
        colour='black', 
        move_type="move",
        piece='black_pawn', 
        from_square='d5', 
        to_square='e4', 
        captured_piece="white_pawn"
    )
    assert format_move(move) == "2. Black: pawn d5 × e4 (captured white pawn)"
    

def test_format_move_formats_castling() -> None:
    move = MoveRecord(
        number=1,
        colour="white",
        move_type="castle",
        piece="white_king",
        from_square="e1",
        to_square="g1",
        captured_piece=None,
        castle_side="kingside",
    )

    assert format_move(move) == "1. White: castled kingside"
    

def test_describe_board_changes_reports_added_and_removed_pieces() -> None:
    changes = describe_board_changes(
        {
            "e1": "white_king",
            "d4": "white_queen",
        },
        {
            "e1": "white_king",
            "e5": "black_queen",
        },
    )

    assert changes == (
        "d4: white queen → empty",
        "e5: empty → black queen",
    )


def test_format_move_formats_correction_summary() -> None:
    move = MoveRecord(
        number=3,
        colour="black",
        move_type="correction",
        piece=None,
        from_square=None,
        to_square=None,
        captured_piece=None,
        correction_changes=(
            "d4: white queen → empty",
            "e5: empty → black queen",
        ),
        previous_turn="black",
        resulting_turn="white",
    )

    assert format_move(move) == (
        "3. Black: board position corrected "
        "(2 squares changed; White to move)"
    )
    

def test_format_move_marks_undone_move() -> None:
    move = MoveRecord(
        number=1,
        colour="white",
        move_type="move",
        piece="white_pawn",
        from_square="e2",
        to_square="e4",
        captured_piece=None,
        is_undone=True,
    )

    assert format_move(move) == (
        "1. White: pawn e2 → e4 (undone)"
    )


def test_format_move_formats_undo_event() -> None:
    move = MoveRecord(
        number=2,
        colour="black",
        move_type="undo",
        piece=None,
        from_square=None,
        to_square=None,
        captured_piece=None,
        undo_target_number=1,
        undo_target_type="move",
    )

    assert format_move(move) == (
        "2. Black: undid move 1"
    )
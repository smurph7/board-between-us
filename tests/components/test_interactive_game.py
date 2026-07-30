from app.components.interactive_game import (
    InteractiveGameState,
    apply_external_state,
    latest_undoable_record,
    undo_button_label,
    undo_confirmation_text,
)
from app.models.move import MoveRecord


def test_apply_external_state_preserves_state_when_no_update() -> None:
    current_state = InteractiveGameState(
        board={"e2": "white_pawn"},
        current_turn="white",
        move_history=[],
    )

    result = apply_external_state(
        current_state=current_state,
        selected_square="e2",
        external_state=None,
    )

    assert result.state is current_state
    assert result.selected_square == "e2"
    assert result.changed is False


def test_apply_external_state_replaces_state_and_clears_selection() -> None:
    current_state = InteractiveGameState(
        board={"e2": "white_pawn"},
        current_turn="white",
        move_history=[],
    )
    external_state = InteractiveGameState(
        board={"e4": "white_pawn"},
        current_turn="black",
        move_history=[],
    )

    result = apply_external_state(
        current_state=current_state,
        selected_square="e2",
        external_state=external_state,
    )

    assert result.state is external_state
    assert result.selected_square is None
    assert result.changed is True
    

def test_latest_undoable_record_skips_undo_and_undone_events() -> None:
    history = [
        MoveRecord(
            number=1,
            colour="white",
            move_type="move",
            piece="white_pawn",
            from_square="e2",
            to_square="e4",
            captured_piece=None,
        ),
        MoveRecord(
            number=2,
            colour="black",
            move_type="move",
            piece="black_pawn",
            from_square="e7",
            to_square="e5",
            captured_piece=None,
            is_undone=True,
        ),
        MoveRecord(
            number=3,
            colour="white",
            move_type="undo",
            piece=None,
            from_square=None,
            to_square=None,
            captured_piece=None,
            undo_target_number=2,
            undo_target_type="move",
        ),
    ]

    result = latest_undoable_record(history)

    assert result is history[0]


def test_undo_button_label_describes_correction() -> None:
    correction = MoveRecord(
        number=1,
        colour="black",
        move_type="correction",
        piece=None,
        from_square=None,
        to_square=None,
        captured_piece=None,
    )

    assert undo_button_label(correction) == "Undo correction"


def test_undo_confirmation_describes_ordinary_move() -> None:
    move = MoveRecord(
        number=1,
        colour="white",
        move_type="move",
        piece="white_pawn",
        from_square="e2",
        to_square="e4",
        captured_piece=None,
    )

    assert undo_confirmation_text(move) == (
        "Undo White's pawn move from e2 to e4?"
    )


def test_apply_external_state_ignores_older_matching_state_object() -> None:
    current_state = InteractiveGameState(
        board={"e2": "white_pawn"},
        current_turn="white",
        move_history=[],
    )

    result = apply_external_state(
        current_state=current_state,
        selected_square=None,
        external_state=current_state,
    )

    assert result.state is current_state
    assert result.selected_square is None
    assert result.changed is False

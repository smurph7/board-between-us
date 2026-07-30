from uuid import uuid4

from app.components.interactive_game import InteractiveGameState
from app.models.move import MoveRecord
from app.models.persisted_move import Move
from app.pages.game import (
    append_persisted_move,
    append_persisted_undo,
)
from app.services.move_service import persisted_move_to_record


def make_persisted_move(**overrides) -> Move:
    values = {
        "id": uuid4(),
        "game_id": uuid4(),
        "player_id": uuid4(),
        "sequence_number": 1,
        "move_type": "move",
        "piece": "white_pawn",
        "from_square": "e2",
        "to_square": "e4",
        "captured_piece": None,
        "changes": [],
        "board_state_before": {"e2": "white_pawn"},
        "board_state_after": {"e4": "white_pawn"},
        "previous_turn": "white",
        "resulting_turn": "black",
        "is_undone": False,
    }
    values.update(overrides)
    return Move(**values)


def test_move_record_from_persisted_move_describes_castle_side() -> None:
    move = make_persisted_move(
        move_type="castle",
        piece="white_king",
        from_square="e1",
        to_square="g1",
        board_state_before={
            "e1": "white_king",
            "h1": "white_rook",
        },
        board_state_after={
            "g1": "white_king",
            "f1": "white_rook",
        },
    )

    record = persisted_move_to_record(
        move,
        colour="white",
    )

    assert record.move_type == "castle"
    assert record.castle_side == "kingside"


def test_append_persisted_move_preserves_existing_history() -> None:
    previous = MoveRecord(
        number=1,
        colour="white",
        move_type="move",
        piece="white_pawn",
        from_square="e2",
        to_square="e4",
        captured_piece=None,
    )
    state = InteractiveGameState(
        board={"e4": "white_pawn"},
        current_turn="black",
        move_history=[previous],
    )
    move = make_persisted_move(
        sequence_number=2,
        move_type="move",
        piece="black_pawn",
        from_square="e7",
        to_square="e5",
        board_state_before={"e4": "white_pawn", "e7": "black_pawn"},
        board_state_after={"e4": "white_pawn", "e5": "black_pawn"},
        previous_turn="black",
        resulting_turn="white",
    )

    updated = append_persisted_move(
        state=state,
        board={"e4": "white_pawn", "e5": "black_pawn"},
        current_turn="white",
        move=move,
        actor_colour="black",
    )

    assert updated.move_history[0] is previous
    assert updated.move_history[1].number == 2
    assert updated.move_history[1].colour == "black"


def test_append_persisted_undo_marks_target_undone() -> None:
    target = MoveRecord(
        number=1,
        colour="white",
        move_type="move",
        piece="white_pawn",
        from_square="e2",
        to_square="e4",
        captured_piece=None,
    )
    state = InteractiveGameState(
        board={"e4": "white_pawn"},
        current_turn="black",
        move_history=[target],
    )
    undo = make_persisted_move(
        sequence_number=2,
        move_type="undo",
        piece=None,
        from_square=None,
        to_square=None,
        changes=[
            {
                "undone_sequence_number": 1,
                "undone_move_type": "move",
            }
        ],
        board_state_before={"e4": "white_pawn"},
        board_state_after={"e2": "white_pawn"},
        previous_turn="black",
        resulting_turn="white",
    )

    updated = append_persisted_undo(
        state=state,
        board={"e2": "white_pawn"},
        current_turn="white",
        move=undo,
        actor_colour="black",
    )

    assert updated.move_history[0].is_undone is True
    assert updated.move_history[1].move_type == "undo"
    assert updated.move_history[1].undo_target_number == 1
    assert target.is_undone is False

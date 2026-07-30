from uuid import UUID
import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.persisted_move import Move
from app.repositories.game_repository import get_game
from app.services.game_service import create_standard_game
from app.services.move_service import (
    InvalidMoveError,
    PlayerNotFoundError,
    StaleGameError,
    WrongTurnError,
    make_move,
    make_castle,
)


def move_count(session: Session, game_id: UUID) -> int:
    """Return the number of persisted moves for one game."""
    count = session.scalar(
        select(func.count(Move.id)).where(
            Move.game_id == game_id,
        )
    )

    return count or 0


def prepare_white_kingside_castle(
    session: Session,
    game_id: UUID,
) -> None:
    """Replace the board with a minimal White kingside castle position."""
    game = get_game(session, game_id)

    assert game is not None

    game.board_state = {
        "e1": "white_king",
        "h1": "white_rook",
        "e8": "black_king",
    }

    session.flush()


def test_move_updates_board_turn_version_and_history(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id
    white_player_id = created.white_player.id

    completed = make_move(
        db_session,
        game_id=game_id,
        player_id=white_player_id,
        from_square="e2",
        to_square="e4",
        expected_version=0,
    )

    assert completed.move.sequence_number == 1
    assert completed.move.move_type == "move"
    assert completed.move.piece == "white_pawn"
    assert completed.move.captured_piece is None

    db_session.flush()
    db_session.expire_all()

    game = get_game(db_session, game_id)

    assert game is not None
    assert "e2" not in game.board_state
    assert game.board_state["e4"] == "white_pawn"
    assert game.current_turn == "black"
    assert game.version == 1
    assert move_count(db_session, game_id) == 1


def test_capture_is_persisted(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id

    make_move(
        db_session,
        game_id=game_id,
        player_id=created.white_player.id,
        from_square="e2",
        to_square="e4",
        expected_version=0,
    )
    make_move(
        db_session,
        game_id=game_id,
        player_id=created.black_player.id,
        from_square="d7",
        to_square="d5",
        expected_version=1,
    )
    completed = make_move(
        db_session,
        game_id=game_id,
        player_id=created.white_player.id,
        from_square="e4",
        to_square="d5",
        expected_version=2,
    )

    assert completed.move.sequence_number == 3
    assert completed.move.move_type == "capture"
    assert completed.move.captured_piece == "black_pawn"

    db_session.flush()
    db_session.expire_all()

    game = get_game(db_session, game_id)

    assert game is not None
    assert "e4" not in game.board_state
    assert game.board_state["d5"] == "white_pawn"
    assert game.current_turn == "black"
    assert game.version == 3
    assert move_count(db_session, game_id) == 3


def test_wrong_turn_is_rejected_without_changes(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id
    original_board = created.game.board_state.copy()

    with pytest.raises(WrongTurnError):
        make_move(
            db_session,
            game_id=game_id,
            player_id=created.black_player.id,
            from_square="e7",
            to_square="e5",
            expected_version=0,
        )

    db_session.expire_all()
    game = get_game(db_session, game_id)

    assert game is not None
    assert game.board_state == original_board
    assert game.current_turn == "white"
    assert game.version == 0
    assert move_count(db_session, game_id) == 0


def test_stale_version_is_rejected_without_changes(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id
    original_board = created.game.board_state.copy()

    with pytest.raises(StaleGameError):
        make_move(
            db_session,
            game_id=game_id,
            player_id=created.white_player.id,
            from_square="e2",
            to_square="e4",
            expected_version=99,
        )

    db_session.expire_all()
    game = get_game(db_session, game_id)

    assert game is not None
    assert game.board_state == original_board
    assert game.current_turn == "white"
    assert game.version == 0
    assert move_count(db_session, game_id) == 0


def test_player_cannot_move_opponents_piece(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id

    with pytest.raises(InvalidMoveError):
        make_move(
            db_session,
            game_id=game_id,
            player_id=created.white_player.id,
            from_square="a7",
            to_square="a6",
            expected_version=0,
        )

    assert move_count(db_session, game_id) == 0


def test_player_cannot_capture_own_piece(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id

    with pytest.raises(InvalidMoveError):
        make_move(
            db_session,
            game_id=game_id,
            player_id=created.white_player.id,
            from_square="b1",
            to_square="a1",
            expected_version=0,
        )

    assert move_count(db_session, game_id) == 0


def test_player_from_another_game_is_rejected(
    db_session: Session,
) -> None:
    first_game = create_standard_game(db_session)
    second_game = create_standard_game(db_session)

    with pytest.raises(PlayerNotFoundError):
        make_move(
            db_session,
            game_id=first_game.game.id,
            player_id=second_game.white_player.id,
            from_square="e2",
            to_square="e4",
            expected_version=0,
        )

    assert move_count(db_session, first_game.game.id) == 0
    
    
def test_castle_updates_board_turn_version_and_history(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id

    prepare_white_kingside_castle(
        db_session,
        game_id,
    )

    completed = make_castle(
        db_session,
        game_id=game_id,
        player_id=created.white_player.id,
        side="kingside",
        expected_version=0,
    )

    assert completed.move.sequence_number == 1
    assert completed.move.move_type == "castle"
    assert completed.move.piece == "white_king"
    assert completed.move.from_square == "e1"
    assert completed.move.to_square == "g1"
    assert completed.move.captured_piece is None
    assert completed.move.changes == [
        {
            "piece": "white_king",
            "from": "e1",
            "to": "g1",
        },
        {
            "piece": "white_rook",
            "from": "h1",
            "to": "f1",
        },
    ]

    assert completed.move.board_state_before == {
        "e1": "white_king",
        "h1": "white_rook",
        "e8": "black_king",
    }

    assert completed.move.board_state_after == {
        "g1": "white_king",
        "f1": "white_rook",
        "e8": "black_king",
    }

    db_session.flush()
    db_session.expire_all()

    game = get_game(db_session, game_id)

    assert game is not None
    assert game.board_state == {
        "g1": "white_king",
        "f1": "white_rook",
        "e8": "black_king",
    }
    assert game.current_turn == "black"
    assert game.version == 1
    assert move_count(db_session, game_id) == 1
    

def test_castle_with_missing_rook_is_rejected_without_changes(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id

    original_board = {
        "e1": "white_king",
        "e8": "black_king",
    }

    game = get_game(db_session, game_id)
    assert game is not None

    game.board_state = original_board.copy()
    db_session.flush()

    with pytest.raises(
        InvalidMoveError,
        match="Expected white_rook at h1",
    ):
        make_castle(
            db_session,
            game_id=game_id,
            player_id=created.white_player.id,
            side="kingside",
            expected_version=0,
        )

    db_session.expire_all()
    game = get_game(db_session, game_id)

    assert game is not None
    assert game.board_state == original_board
    assert game.current_turn == "white"
    assert game.version == 0
    assert move_count(db_session, game_id) == 0
    

def test_castle_on_wrong_turn_is_rejected_without_changes(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id

    prepare_white_kingside_castle(
        db_session,
        game_id,
    )

    original_board = created.game.board_state.copy()

    with pytest.raises(WrongTurnError):
        make_castle(
            db_session,
            game_id=game_id,
            player_id=created.black_player.id,
            side="kingside",
            expected_version=0,
        )

    db_session.expire_all()
    game = get_game(db_session, game_id)

    assert game is not None
    assert game.board_state == original_board
    assert game.current_turn == "white"
    assert game.version == 0
    assert move_count(db_session, game_id) == 0
    

def test_castle_with_stale_version_is_rejected_without_changes(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    game_id = created.game.id

    prepare_white_kingside_castle(
        db_session,
        game_id,
    )

    original_board = created.game.board_state.copy()

    with pytest.raises(StaleGameError):
        make_castle(
            db_session,
            game_id=game_id,
            player_id=created.white_player.id,
            side="kingside",
            expected_version=99,
        )

    db_session.expire_all()
    game = get_game(db_session, game_id)

    assert game is not None
    assert game.board_state == original_board
    assert game.current_turn == "white"
    assert game.version == 0
    assert move_count(db_session, game_id) == 0
import pytest

from app.utils.board import (
    BoardState,
    CastleSide,
    Colour,
    Square,
    apply_castle,
    can_castle,
    PieceMovement, 
    get_castling_movements
)


@pytest.mark.parametrize(
    (
        "colour",
        "side",
        "king_from",
        "king_to",
        "rook_from",
        "rook_to",
    ),
    [
        ("white", "kingside", "e1", "g1", "h1", "f1"),
        ("white", "queenside", "e1", "c1", "a1", "d1"),
        ("black", "kingside", "e8", "g8", "h8", "f8"),
        ("black", "queenside", "e8", "c8", "a8", "d8"),
    ],
)


def test_apply_castle_moves_king_and_rook(
    colour: Colour,
    side: CastleSide,
    king_from: Square,
    king_to: Square,
    rook_from: Square,
    rook_to: Square,
) -> None:
    original_board: BoardState = {
        king_from: f"{colour}_king",
        rook_from: f"{colour}_rook",
        "d4": "white_pawn",
    }

    updated_board = apply_castle(
        original_board,
        colour=colour,
        side=side,
    )

    assert updated_board == {
        king_to: f"{colour}_king",
        rook_to: f"{colour}_rook",
        "d4": "white_pawn",
    }

    assert original_board == {
        king_from: f"{colour}_king",
        rook_from: f"{colour}_rook",
        "d4": "white_pawn",
    }
    
    
def test_apply_castle_rejects_missing_expected_rook() -> None:
    original_board: BoardState = {
        "e1": "white_king",
    }

    with pytest.raises(
        ValueError,
        match="Expected white_rook at h1",
    ):
        apply_castle(
            original_board,
            colour="white",
            side="kingside",
        )

    assert original_board == {
        "e1": "white_king",
    }


def test_apply_castle_rejects_occupied_destination() -> None:
    original_board: BoardState = {
        "e1": "white_king",
        "h1": "white_rook",
        "f1": "white_bishop",
    }

    with pytest.raises(
        ValueError,
        match="Castling destination occupied: f1",
    ):
        apply_castle(
            original_board,
            colour="white",
            side="kingside",
        )

    assert original_board == {
        "e1": "white_king",
        "h1": "white_rook",
        "f1": "white_bishop",
    }
    

def test_can_castle_returns_true_when_required_squares_are_available() -> None:
    board: BoardState = {
        "e1": "white_king",
        "h1": "white_rook",
    }

    assert can_castle(
        board,
        colour="white",
        side="kingside",
    )


def test_can_castle_returns_false_when_rook_is_missing() -> None:
    board: BoardState = {
        "e1": "white_king",
    }

    assert not can_castle(
        board,
        colour="white",
        side="kingside",
    )


def test_can_castle_returns_false_when_destination_is_occupied() -> None:
    board: BoardState = {
        "e1": "white_king",
        "h1": "white_rook",
        "f1": "white_bishop",
    }

    assert not can_castle(
        board,
        colour="white",
        side="kingside",
    )
    
    
def test_get_castling_movements_describes_both_piece_moves() -> None:
    movements = get_castling_movements(
        colour="white",
        side="kingside",
    )

    assert movements == (
        PieceMovement(
            piece="white_king",
            from_square="e1",
            to_square="g1",
        ),
        PieceMovement(
            piece="white_rook",
            from_square="h1",
            to_square="f1",
        ),
    )
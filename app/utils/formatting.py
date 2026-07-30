from app.models.move import MoveRecord
from app.utils.board import BoardState, Piece



def format_piece(piece: Piece | None) -> str:
    """Return a readable piece name or an empty-square label."""
    if piece is None:
        return "empty"

    return piece.replace("_", " ")


def describe_board_changes(
    board_before: BoardState,
    board_after: BoardState,
) -> tuple[str, ...]:
    """Describe the squares changed between two board positions."""

    changed_squares = sorted(
        set(board_before) | set(board_after)
    )

    return tuple(
        (
            f"{square}: "
            f"{format_piece(board_before.get(square))} → "
            f"{format_piece(board_after.get(square))}"
        )
        for square in changed_squares
        if board_before.get(square) != board_after.get(square)
    )


def format_move(move: MoveRecord) -> str:
    """Return a readable description of a completed history event."""

    if move.move_type == "undo":
        target_type = move.undo_target_type or "event"

        target = (
            f"{target_type} {move.undo_target_number}"
            if move.undo_target_number is not None
            else target_type
        )

        return (
            f"{move.number}. {move.colour.capitalize()}: "
            f"undid {target}"
        )
    
    if move.move_type == "correction":
        change_count = len(move.correction_changes)
        change_word = "square" if change_count == 1 else "squares"

        turn_text = (
            f"; {move.resulting_turn.capitalize()} to move"
            if move.resulting_turn is not None
            else ""
        )

        text = (
            f"{move.number}. {move.colour.capitalize()}: "
            f"board position corrected "
            f"({change_count} {change_word} changed{turn_text})"
        )
        
        return mark_undone(text, move)

    if move.move_type == "castle":
        text = (
            f"{move.number}. {move.colour.capitalize()}: "
            f"castled {move.castle_side}"
        )
        
        return mark_undone(text, move)
        
    if (
        move.piece is None
        or move.from_square is None
        or move.to_square is None
    ):
        return (
            f"{move.number}. {move.colour.capitalize()}: "
            f"recorded {move.move_type}"
        )

    piece_name = move.piece.removeprefix(
        f"{move.colour}_"
    )
    separator = "×" if move.captured_piece is not None else "→"

    capture_text = (
        f" (captured {move.captured_piece.replace('_', ' ')})"
        if move.captured_piece
        else ""
    )

    text = (
        f"{move.number}. {move.colour.capitalize()}: "
        f"{piece_name} {move.from_square} "
        f"{separator} {move.to_square}{capture_text}"
    )
    
    return mark_undone(text, move)

def mark_undone(
    text: str,
    move: MoveRecord,
) -> str:
    """Append an undone marker when the event was reversed."""

    if move.is_undone:
        return f"{text} (undone)"

    return text
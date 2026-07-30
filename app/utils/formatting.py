from app.models.move import MoveRecord


def format_move(move: MoveRecord) -> str:
    """Return a readable description of a completed history event."""
    if move.move_type == "castle":
        return (
            f"{move.number}. {move.colour.capitalize()}: "
            f"castled {move.castle_side}"
        )
        
    piece_name = move.piece.removeprefix(f"{move.colour}_")
    separator = "×" if move.captured_piece is not None else "→"

    capture_text = (
        f" (captured {move.captured_piece.replace('_', ' ')})"
        if move.captured_piece
        else ""
    )

    return (
        f"{move.number}. {move.colour.capitalize()}: "
        f"{piece_name} {move.from_square} "
        f"{separator} {move.to_square}{capture_text}"
    )
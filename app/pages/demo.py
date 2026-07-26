from nicegui import ui

from app.components.interactive_game import (
    InteractiveGameState,
    MoveSubmission,
    render_interactive_game,
)
from app.models.move import MoveRecord
from app.utils.board import (
    Square,
    apply_move,
    create_standard_board,
    next_turn,
)


@ui.page("/demo")
def game_page() -> None:
    """Render the local, non-persisted developer board."""

    def submit_local_move(
        from_square: Square,
        to_square: Square,
        state: InteractiveGameState,
    ) -> MoveSubmission:
        """Apply one move using local in-memory state."""
        moving_piece = state.board[from_square]

        board_after, captured_piece = apply_move(
            state.board,
            from_square=from_square,
            to_square=to_square,
        )

        move = MoveRecord(
            number=len(state.move_history) + 1,
            colour=state.current_turn,
            piece=moving_piece,
            from_square=from_square,
            to_square=to_square,
            captured_piece=captured_piece,
        )

        return MoveSubmission(
            state=InteractiveGameState(
                board=board_after,
                current_turn=next_turn(state.current_turn),
                move_history=[
                    *state.move_history,
                    move,
                ],
            ),
        )

    render_interactive_game(
        title="Board Between Us",
        initial_state=InteractiveGameState(
            board=create_standard_board(),
            current_turn="white",
            move_history=[],
        ),
        submit_move=submit_local_move,
    )
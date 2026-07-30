from collections.abc import Callable

from nicegui import ui

from app.components.chess_board import render_chess_board
from app.components.move_history import render_move_history
from app.models.move import MoveRecord
from app.theme import SECONDARY_BUTTON_PROPS
from app.utils.board import BoardState, Colour, Square


def render_game_view(
    *,
    board: BoardState,
    selected_square: Square | None,
    current_turn: Colour,
    move_history: list[MoveRecord],
    flipped: bool,
    on_square_click: Callable[[Square], None],
    on_flip: Callable[[], None],
    player_colour: Colour | None = None,
    on_undo: Callable[[], None] | None = None,
    undo_label: str = "Undo",
) -> None:
    """Render the shared game board, controls, and move history."""
    if player_colour is not None:
        ui.label(f"Playing as {player_colour.title()}")

    ui.label(f"{current_turn.title()} to move")

    with ui.column().classes("board-shell"):
        render_chess_board(
            board=board,
            selected_square=selected_square,
            on_square_click=on_square_click,
            flipped=flipped,
        )

    ui.button("Flip board", on_click=on_flip).props(
        SECONDARY_BUTTON_PROPS
    )

    render_move_history(
        move_history,
        on_undo=on_undo,
        undo_label=undo_label,
    )

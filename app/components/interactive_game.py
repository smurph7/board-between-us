from collections.abc import Callable
from dataclasses import dataclass

from nicegui import ui

from app.components.game_view import render_game_view
from app.models.move import MoveRecord
from app.utils.board import (
    BoardState,
    Colour,
    Square,
    piece_belongs_to,
)


@dataclass(frozen=True)
class InteractiveGameState:
    """State needed by the interactive board UI."""

    board: BoardState
    current_turn: Colour
    move_history: list[MoveRecord]


@dataclass(frozen=True)
class MoveSubmission:
    """Result returned after attempting a move."""

    state: InteractiveGameState
    success_message: str | None = None
    error_message: str | None = None


type SubmitMove = Callable[
    [Square, Square, InteractiveGameState],
    MoveSubmission,
]


def render_interactive_game(
    *,
    initial_state: InteractiveGameState,
    submit_move: SubmitMove,
    title: str | None = None,
    player_colour: Colour | None = None,
    initial_flipped: bool = False,
) -> None:
    """Render shared selection, movement, flipping, and refresh behaviour."""
    state = initial_state
    selected_square: Square | None = None
    flipped = initial_flipped

    def active_colour() -> Colour:
        """Return the colour this page may currently select."""
        return player_colour or state.current_turn

    def handle_square_click(square: Square) -> None:
        nonlocal state, selected_square

        if player_colour is not None and player_colour != state.current_turn:
            return

        if selected_square is None:
            piece = state.board.get(square)

            if piece is None:
                return

            if not piece_belongs_to(piece, active_colour()):
                return

            selected_square = square

        elif square == selected_square:
            selected_square = None

        else:
            destination_piece = state.board.get(square)

            if (
                destination_piece is not None
                and piece_belongs_to(
                    destination_piece,
                    active_colour(),
                )
            ):
                selected_square = square

            else:
                result = submit_move(
                    selected_square,
                    square,
                    state,
                )

                state = result.state
                selected_square = None

                if result.success_message:
                    ui.notify(result.success_message)

                if result.error_message:
                    ui.notify(
                        result.error_message,
                        type="negative",
                    )

        game_view.refresh()

    def toggle_orientation() -> None:
        nonlocal flipped

        flipped = not flipped
        game_view.refresh()

    def clear_selection() -> None:
        nonlocal selected_square

        if selected_square is None:
            return

        selected_square = None
        game_view.refresh()

    @ui.refreshable
    def game_view() -> None:
        ui.label(title or "Board Between Us").classes("text-h5")

        render_game_view(
            board=state.board,
            selected_square=selected_square,
            current_turn=state.current_turn,
            move_history=state.move_history,
            flipped=flipped,
            on_square_click=handle_square_click,
            on_flip=toggle_orientation,
            player_colour=player_colour,
        )

    with ui.column().classes("w-full min-h-screen").on(
        "click",
        clear_selection,
    ):
        game_view()
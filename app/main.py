from nicegui import ui

from app.components.chess_board import render_chess_board
from app.utils.board import Square, create_standard_board, apply_move

@ui.page("/")
def game_page() -> None:
    """Render the local game page."""
    board = create_standard_board()
    selected_square: Square | None = None

    def handle_square_click(square: Square) -> None:
        nonlocal board, selected_square

        if selected_square is None:
            if square not in board:
                return

            selected_square = square

        elif square == selected_square:
            selected_square = None

        else:
            board, _ = apply_move(
                board,
                from_square=selected_square,
                to_square=square,
            )
            selected_square = None

        board_view.refresh()

    @ui.refreshable
    def board_view() -> None:
        render_chess_board(
            board=board,
            selected_square=selected_square,
            on_square_click=handle_square_click,
        )
    
    def clear_selection() -> None:
        nonlocal selected_square

        if selected_square is None:
            return

        selected_square = None
        board_view.refresh()

    with ui.column().classes("w-full min-h-screen").on(
        "click",
        clear_selection,
    ):
        ui.label("Board Between Us")
        board_view()


def main() -> None:
    """Build and run the Board Between Us web application."""
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
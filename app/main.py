from nicegui import ui

from app.components.chess_board import render_chess_board
from app.utils.board import Square, create_standard_board

@ui.page("/")
def game_page() -> None:
    """Render the local game page."""
    board = create_standard_board()
    selected_square: Square | None = None

    def handle_square_click(square: Square) -> None:
        nonlocal selected_square

        if square not in board:
            return

        if selected_square == square:
            selected_square = None
        else:
            selected_square = square

        board_view.refresh()

    @ui.refreshable
    def board_view() -> None:
        render_chess_board(
            board=board,
            selected_square=selected_square,
            on_square_click=handle_square_click,
        )

    board_view()


def main() -> None:
    """Build and run the Board Between Us web application."""
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
from nicegui import ui

from app.components.chess_board import render_chess_board
from app.utils.board import create_standard_board

def main() -> None:
    """Build and run the Board Between Us web application."""
    ui.label("Board Between Us")
    ui.label("Python project setup is working.")

    board = create_standard_board()
    render_chess_board(board)
    
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
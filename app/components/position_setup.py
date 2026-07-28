from nicegui import ui

from app.components.chess_board import render_chess_board
from app.utils.board import BoardState, Colour, Square
from app.utils.board_setup import (
    clear_board,
    move_piece,
    remove_piece,
    reset_board,
)


def render_position_setup(
    *,
    initial_board: BoardState,
    initial_turn: Colour,
    initial_flipped: bool,
) -> None:
    """Render an editable starting-position interface."""
    board = initial_board.copy()
    selected_square: Square | None = None
    flipped = initial_flipped

    ui.label("Set up starting position")
    
    def remove_selected_piece() -> None:
        nonlocal board, selected_square

        if selected_square is None:
            return

        board = remove_piece(board, selected_square)
        selected_square = None
        render_editable_board.refresh()

    
    def handle_square_click(square: Square) -> None:
        nonlocal board, selected_square

        if selected_square is None:
            if square in board:
                selected_square = square
                render_editable_board.refresh()
            return

        if square == selected_square:
            selected_square = None
            render_editable_board.refresh()
            return

        if square in board:
            selected_square = square
            render_editable_board.refresh()
            return

        board = move_piece(
            board,
            from_square=selected_square,
            to_square=square,
        )
        selected_square = None
        render_editable_board.refresh()
        
        
    def clear_setup_board() -> None:
        nonlocal board, selected_square

        board = clear_board(board)
        selected_square = None
        render_editable_board.refresh()


    def reset_setup_board() -> None:
        nonlocal board, selected_square

        board = reset_board(board)
        selected_square = None
        render_editable_board.refresh()
        

    with ui.row():
        ui.button("Clear board", on_click=clear_setup_board)
        ui.button("Reset to standard", on_click=reset_setup_board)
    
    @ui.refreshable
    def render_editable_board() -> None:
        render_chess_board(
            board=board,
            selected_square=selected_square,
            on_square_click=handle_square_click,
            flipped=flipped,
        )
        
        if selected_square is not None:
            ui.button(
                "Remove selected piece",
                on_click=remove_selected_piece,
            )
        
    render_editable_board()
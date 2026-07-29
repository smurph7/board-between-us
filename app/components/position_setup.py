from functools import partial
from nicegui import ui
from collections.abc import Callable
from typing import cast

from app.components.chess_board import PIECE_SYMBOLS, render_chess_board
from app.utils.board import BoardState, Colour, Piece, Square
from app.utils.board_setup import (
    clear_board,
    move_piece,
    place_piece,
    remove_piece,
    reset_board,
)

WHITE_TRAY_PIECES: tuple[Piece, ...] = (
    "white_king",
    "white_queen",
    "white_rook",
    "white_bishop",
    "white_knight",
    "white_pawn",
)

BLACK_TRAY_PIECES: tuple[Piece, ...] = (
    "black_king",
    "black_queen",
    "black_rook",
    "black_bishop",
    "black_knight",
    "black_pawn",
)


type ConfirmSetup = Callable[[BoardState, Colour], None]
type CancelSetup = Callable[[], None]

def render_position_setup(
    *,
    initial_board: BoardState,
    initial_turn: Colour,
    initial_flipped: bool,
    confirm_setup: ConfirmSetup,
    cancel_setup: CancelSetup,
) -> None:
    """Render an editable starting-position interface."""
    board = initial_board.copy()
    selected_square: Square | None = None
    selected_piece: Piece | None = None
    flipped = initial_flipped
    next_turn: Colour = initial_turn

    ui.label("Set up starting position")
    
    def remove_selected_piece() -> None:
        nonlocal board, selected_square

        if selected_square is None:
            return

        board = remove_piece(board, selected_square)
        selected_square = None
        render_editable_board.refresh()
        

    def select_tray_piece(piece: Piece) -> None:
        nonlocal selected_piece, selected_square

        selected_piece = None if selected_piece == piece else piece
        selected_square = None

        render_piece_tray.refresh()
        render_editable_board.refresh()

    
    def handle_square_click(square: Square) -> None:
        nonlocal board, selected_square, selected_piece
        
        if selected_piece is not None:
            board = place_piece(
                board,
                square,
                selected_piece,
            )
            selected_piece = None
            selected_square = None
            
            render_piece_tray.refresh()
            render_editable_board.refresh()
            return

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
        
        
    def select_next_turn(colour: Colour) -> None:
        nonlocal next_turn
        next_turn = colour
    
    
    with ui.row():
        ui.button("Clear board", on_click=clear_setup_board)
        ui.button("Reset to standard", on_click=reset_setup_board)
    
    @ui.refreshable
    def render_piece_tray() -> None:
        ui.label("White pieces")

        with ui.row().classes("gap-2"):
            for piece in WHITE_TRAY_PIECES:
                button = ui.button(
                    PIECE_SYMBOLS[piece],
                    on_click=partial(select_tray_piece, piece),
                )

                if piece == selected_piece:
                    button.props("unelevated")
                else:
                    button.props("outline")

        ui.label("Black pieces")

        with ui.row().classes("gap-2"):
            for piece in BLACK_TRAY_PIECES:
                button = ui.button(
                    PIECE_SYMBOLS[piece],
                    on_click=partial(select_tray_piece, piece),
                )

                if piece == selected_piece:
                    button.props("unelevated")
                else:
                    button.props("outline")
    
    
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
        
        ui.label("Who moves next?")

        turn_selector = ui.radio(
            {
                "white": "White to move",
                "black": "Black to move",
            },
            value=next_turn,
        ).props("inline")
        
        def confirm_position() -> None:
            confirm_setup(
                board.copy(),
                cast(Colour, turn_selector.value),
            )
            
        with ui.row():
            ui.button(
                "Start online game",
                on_click=confirm_position,
            )

            ui.button(
                "Cancel setup",
                on_click=cancel_setup,
            ).props("outline")
    
    render_piece_tray()
    render_editable_board()
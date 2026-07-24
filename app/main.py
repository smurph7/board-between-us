from nicegui import ui

from app.components.chess_board import render_chess_board
from app.components.move_history import render_move_history
from app.models.move import MoveRecord
from app.utils.board import Colour, Square, create_standard_board, apply_move, piece_belongs_to, next_turn

@ui.page("/")
def game_page() -> None:
    """Render the local game page."""
    ui.label("Board Between Us")
    board = create_standard_board()
    selected_square: Square | None = None
    current_turn: Colour = "white"
    move_history: list[MoveRecord] = []

    def handle_square_click(square: Square) -> None:
        nonlocal board, selected_square, current_turn

        if selected_square is None:
            piece = board.get(square)

            if piece is None:
                return

            if not piece_belongs_to(piece, current_turn):
                return

            selected_square = square

        elif square == selected_square:
            selected_square = None

        else:
            from_square = selected_square
            moving_piece = board[from_square]
            
            board, captured_piece = apply_move(
                board,
                from_square=from_square,
                to_square=square,
            )

            move_history.append(
                MoveRecord(
                    number=len(move_history) + 1,
                    colour=current_turn,
                    piece=moving_piece,
                    from_square=from_square,
                    to_square=square,
                    captured_piece=captured_piece,
                )
            )

            print(move_history)
            selected_square = None
            current_turn = next_turn(current_turn)

        game_view.refresh()

    @ui.refreshable
    def game_view() -> None:
        ui.label(f"{current_turn.title()} to move")
        
        render_chess_board(
            board=board,
            selected_square=selected_square,
            on_square_click=handle_square_click,
        )
        
        render_move_history(move_history)
    
    def clear_selection() -> None:
        nonlocal selected_square

        if selected_square is None:
            return

        selected_square = None
        game_view.refresh()

    with ui.column().classes("w-full min-h-screen").on(
        "click",
        clear_selection,
    ):

        game_view()


def main() -> None:
    """Build and run the Board Between Us web application."""
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
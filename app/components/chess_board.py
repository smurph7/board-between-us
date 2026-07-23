from nicegui import ui
from app.utils.board import BoardState

PIECE_SYMBOLS = {
        "white_king": "♔",
        "white_queen": "♕",
        "white_rook": "♖",
        "white_bishop": "♗",
        "white_knight": "♘",
        "white_pawn": "♙",
        "black_king": "♚",
        "black_queen": "♛",
        "black_rook": "♜",
        "black_bishop": "♝",
        "black_knight": "♞",
        "black_pawn": "♟",
    }

def render_chess_board(board: BoardState) -> None:
    """Render an 8×8 read-only chessboard with coordinates on all sides."""

    with ui.column().classes("gap-0"):
        # Top file labels
        with ui.row().classes("gap-0"):
            ui.label("").classes("w-6")

            for file_letter in "abcdefgh":
                ui.label(file_letter).classes(
                    "w-12 h-6 flex items-center justify-center"
                )

            ui.label("").classes("w-6")

        # Board rows, with rank labels on both sides
        for rank in range(8, 0, -1):
            with ui.row().classes("gap-0 items-center"):
                ui.label(str(rank)).classes(
                    "w-6 h-12 flex items-center justify-center"
                )

                for file_index, file_letter in enumerate("abcdefgh"):
                    square = f"{file_letter}{rank}"
                    piece = board.get(square)
                    symbol = PIECE_SYMBOLS.get(piece, "")

                    is_light_square = (file_index + rank) % 2 == 0
                    background = (
                        "bg-amber-100"
                        if is_light_square
                        else "bg-amber-700"
                    )

                    ui.label(symbol).classes(
                        f"{background} "
                        "w-12 h-12 "
                        "flex items-center justify-center "
                        "text-3xl"
                    )

                ui.label(str(rank)).classes(
                    "w-6 h-12 flex items-center justify-center"
                )

        # Bottom file labels
        with ui.row().classes("gap-0"):
            ui.label("").classes("w-6")

            for file_letter in "abcdefgh":
                ui.label(file_letter).classes(
                    "w-12 h-6 flex items-center justify-center"
                )

            ui.label("").classes("w-6")

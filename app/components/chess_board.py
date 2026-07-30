from collections.abc import Callable
from functools import partial

from nicegui import ui

from app.utils.board import BoardState, Square

BOARD_SQUARE_CLASSES = (
    "w-[clamp(2.1rem,10vw,3.75rem)] "
    "aspect-square "
    "flex items-center justify-center "
    "text-[clamp(1.5rem,7vw,2.75rem)] "
    "board-square "
    "piece-symbol"
)
FILE_LABEL_CLASSES = (
    "w-[clamp(2.1rem,10vw,3.75rem)] "
    "h-6 flex items-center justify-center "
    "board-coordinate"
)
RANK_LABEL_CLASSES = (
    "w-6 h-[clamp(2.1rem,10vw,3.75rem)] "
    "flex items-center justify-center "
    "board-coordinate"
)

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


def render_chess_board(
    board: BoardState,
    selected_square: Square | None,
    on_square_click: Callable[[Square], None],
    flipped: bool,
) -> None:
    """Render an 8x8 read-only chessboard with coordinates on all sides."""

    files = "hgfedcba" if flipped else "abcdefgh"
    ranks = range(1, 9) if flipped else range(8, 0, -1)

    with ui.column().classes("gap-0").on(
        "click",
        js_handler="(event) => event.stopPropagation()",
    ):
        # Top file labels
        with ui.row().classes("gap-0 flex-nowrap"):
            ui.label("").classes("w-6")

            for file_letter in files:
                ui.label(file_letter).classes(FILE_LABEL_CLASSES)

            ui.label("").classes("w-6")

        # Board rows, with rank labels on both sides
        for rank in ranks:
            with ui.row().classes("gap-0 items-center flex-nowrap"):
                ui.label(str(rank)).classes(RANK_LABEL_CLASSES)

                for file_letter in files:
                    file_index = "abcdefgh".index(file_letter)
                    square = f"{file_letter}{rank}"
                    piece = board.get(square)
                    symbol = PIECE_SYMBOLS.get(piece, "")

                    is_light_square = (file_index + rank) % 2 == 0
                    square_class = (
                        "board-square-light"
                        if is_light_square
                        else "board-square-dark"
                    )

                    selection_class = (
                        "board-square-selected"
                        if square == selected_square
                        else ""
                    )

                    ui.label(symbol).classes(
                        f"{square_class} {selection_class} "
                        f"{BOARD_SQUARE_CLASSES}"
                    ).on("click", partial(on_square_click, square))

                ui.label(str(rank)).classes(RANK_LABEL_CLASSES)

        # Bottom file labels
        with ui.row().classes("gap-0 flex-nowrap"):
            ui.label("").classes("w-6")

            for file_letter in files:
                ui.label(file_letter).classes(FILE_LABEL_CLASSES)

            ui.label("").classes("w-6")

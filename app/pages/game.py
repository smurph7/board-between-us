from typing import cast
from uuid import UUID

from nicegui import ui

from app.components.game_view import render_game_view
from app.database.session import database_session
from app.models.move import MoveRecord
from app.services.game_service import load_player_game
from app.services.move_service import (
    MoveError,
    get_move_history,
    make_move,
)
from app.utils.board import (
    BoardState,
    Colour,
    Square,
    piece_belongs_to,
)


@ui.page("/play/{game_id}/{access_token}")
def persisted_game_page(
    game_id: str,
    access_token: str,
) -> None:
    """Render a shared game loaded through a private player link."""
    try:
        parsed_game_id = UUID(game_id)
    except ValueError:
        ui.label("This player link is invalid or no longer available.")
        return

    with database_session() as session:
        player_game = load_player_game(
            session,
            game_id=parsed_game_id,
            access_token=access_token,
        )

        if player_game is None:
            ui.label("This player link is invalid or no longer available.")
            return

        persisted_game_id = player_game.game.id
        player_id = player_game.player.id
        player_colour = cast(Colour, player_game.player.colour)
        game_name = player_game.game.name or "Untitled game"

        board: BoardState = player_game.game.board_state.copy()
        current_turn = cast(Colour, player_game.game.current_turn)
        version = player_game.game.version
        move_history = get_move_history(
            session,
            persisted_game_id,
        )

    selected_square: Square | None = None
    flipped = player_colour == "black"

    def reload_game_state() -> None:
        """Reload canonical state from the database."""
        nonlocal board, current_turn, version, move_history

        with database_session() as session:
            loaded = load_player_game(
                session,
                game_id=persisted_game_id,
                access_token=access_token,
            )

            if loaded is None:
                return

            board = loaded.game.board_state.copy()
            current_turn = cast(
                Colour,
                loaded.game.current_turn,
            )
            version = loaded.game.version
            move_history = get_move_history(
                session,
                persisted_game_id,
            )

    def handle_square_click(square: Square) -> None:
        nonlocal selected_square
        nonlocal board, current_turn, version, move_history

        if selected_square is None:
            if player_colour != current_turn:
                return

            piece = board.get(square)

            if piece is None:
                return

            if not piece_belongs_to(piece, player_colour):
                return

            selected_square = square

        elif square == selected_square:
            selected_square = None

        else:
            destination_piece = board.get(square)

            if (
                destination_piece is not None
                and piece_belongs_to(
                    destination_piece,
                    player_colour,
                )
            ):
                selected_square = square

            else:
                from_square = selected_square

                try:
                    with database_session() as session:
                        completed = make_move(
                            session,
                            game_id=persisted_game_id,
                            player_id=player_id,
                            from_square=from_square,
                            to_square=square,
                            expected_version=version,
                        )

                        board = completed.game.board_state.copy()
                        current_turn = cast(
                            Colour,
                            completed.game.current_turn,
                        )
                        version = completed.game.version
                        move_history = get_move_history(
                            session,
                            persisted_game_id,
                        )

                    ui.notify("Move saved")

                except MoveError as error:
                    reload_game_state()
                    ui.notify(str(error), type="negative")

                selected_square = None

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
        ui.label(game_name).classes("text-h5")

        render_game_view(
            board=board,
            selected_square=selected_square,
            current_turn=current_turn,
            move_history=move_history,
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
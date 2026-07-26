from typing import cast
from uuid import UUID

from nicegui import ui

from app.components.interactive_game import (
    InteractiveGameState,
    MoveSubmission,
    render_interactive_game,
)
from app.database.session import database_session
from app.services.game_service import load_player_game
from app.services.move_service import (
    MoveError,
    get_move_history,
    make_move,
)
from app.utils.board import Colour, Square


@ui.page("/play/{game_id}/{access_token}")
def persisted_game_page(
    game_id: str,
    access_token: str,
) -> None:
    """Render a persisted game through a private player link."""
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
        player_colour = cast(
            Colour,
            player_game.player.colour,
        )
        game_name = player_game.game.name

        initial_state = InteractiveGameState(
            board=player_game.game.board_state.copy(),
            current_turn=cast(
                Colour,
                player_game.game.current_turn,
            ),
            move_history=get_move_history(
                session,
                persisted_game_id,
            ),
        )

        initial_version = player_game.game.version

    version = initial_version

    def load_current_state() -> InteractiveGameState | None:
        """Reload the canonical game state from the database."""
        nonlocal version

        with database_session() as session:
            loaded = load_player_game(
                session,
                game_id=persisted_game_id,
                access_token=access_token,
            )

            if loaded is None:
                return None

            version = loaded.game.version

            return InteractiveGameState(
                board=loaded.game.board_state.copy(),
                current_turn=cast(
                    Colour,
                    loaded.game.current_turn,
                ),
                move_history=get_move_history(
                    session,
                    persisted_game_id,
                ),
            )

    def submit_persisted_move(
        from_square: Square,
        to_square: Square,
        state: InteractiveGameState,
    ) -> MoveSubmission:
        """Persist one move and return the latest shared state."""
        nonlocal version

        try:
            with database_session() as session:
                completed = make_move(
                    session,
                    game_id=persisted_game_id,
                    player_id=player_id,
                    from_square=from_square,
                    to_square=to_square,
                    expected_version=version,
                )

                version = completed.game.version

                updated_state = InteractiveGameState(
                    board=completed.game.board_state.copy(),
                    current_turn=cast(
                        Colour,
                        completed.game.current_turn,
                    ),
                    move_history=get_move_history(
                        session,
                        persisted_game_id,
                    ),
                )

            return MoveSubmission(
                state=updated_state,
                success_message="Move saved",
            )

        except MoveError as error:
            latest_state = load_current_state()

            return MoveSubmission(
                state=latest_state or state,
                error_message=str(error),
            )

    render_interactive_game(
        title=game_name,
        initial_state=initial_state,
        submit_move=submit_persisted_move,
        player_colour=player_colour,
        initial_flipped=player_colour == "black",
    )
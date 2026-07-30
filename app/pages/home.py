import logging
from functools import partial
from typing import cast

from nicegui import ui

from app.config import get_settings
from app.database.session import database_session
from app.components.position_setup import render_position_setup
from app.services.game_service import (
    CreatedGameLinks,
    GameNotInSetupError,
    cancel_game_setup,
    confirm_game_setup,
    create_game_for_players,
)
from app.services.move_service import (
    GameNotFoundError,
    StaleGameError,
)
from app.theme import PRIMARY_BUTTON_PROPS, SECONDARY_BUTTON_PROPS
from app.utils.board import BoardState, Colour


logger = logging.getLogger(__name__)


@ui.page("/")
def home_page() -> None:
    """Render the game creation page."""
    settings = get_settings()

    with ui.column().classes("w-full max-w-md mx-auto gap-6 p-4"):
        ui.label("Board Between Us").classes("text-2xl font-semibold")
        ui.label("A private shared chessboard for slow games.")

        form_area = ui.column().classes("w-full gap-6")
        result_area = ui.column().classes("w-full gap-4")

    result_area.set_visibility(False)

    def copy_link(url: str, message: str) -> None:
        """Copy a private game URL to the browser clipboard."""
        ui.clipboard.write(url)
        ui.notify(message, type="positive")

    def render_created_links(created_links: CreatedGameLinks) -> None:
        """Render the links produced after game creation."""
        with result_area:
            ui.label("Game created").classes("text-xl font-semibold")

            ui.label(
                "Keep your link private. Anyone with it can play as you."
            ).classes("text-sm")

            with ui.row().classes(
                "w-full items-end gap-2 flex-nowrap"
            ):
                ui.input(
                    label="Your private link",
                    value=created_links.creator_url,
                ).props("readonly").classes("flex-1 min-w-0")

                ui.button(
                    "Copy link",
                    icon="content_copy",
                    on_click=partial(
                        copy_link,
                        created_links.creator_url,
                        "Your link copied",
                    ),
                ).props(SECONDARY_BUTTON_PROPS)

            ui.link(
                "Open my board",
                target=created_links.creator_url,
                new_tab=True,
            ).classes("font-medium")

            ui.separator()

            ui.label(
                "Send this invitation link to your opponent."
            ).classes("text-sm")

            with ui.row().classes(
                "w-full items-end gap-2 flex-nowrap"
            ):
                ui.input(
                    label="Opponent invitation link",
                    value=created_links.opponent_url,
                ).props("readonly").classes("flex-1 min-w-0")

                ui.button(
                    "Copy opponent link",
                    icon="content_copy",
                    on_click=partial(
                        copy_link,
                        created_links.opponent_url,
                        "Invitation link copied",
                    ),
                ).props(SECONDARY_BUTTON_PROPS)
            
            ui.label(
                "Copy these links now. They cannot be shown again after you leave this page."
            ).classes("text-sm font-medium pt-4")

    def render_created_setup(
        created_links: CreatedGameLinks,
        *,
        initial_board: BoardState,
        initial_turn: Colour,
        expected_version: int,
    ) -> None:
        """Render setup before revealing the private links."""

        def handle_confirm_setup(
            board_state: BoardState,
            next_turn: Colour,
        ) -> None:
            try:
                with database_session() as session:
                    confirm_game_setup(
                        session,
                        game_id=created_links.game.id,
                        board_state=board_state,
                        next_turn=next_turn,
                        expected_version=expected_version,
                    )
            except (GameNotFoundError, StaleGameError) as error:
                ui.notify(str(error), type="negative")
                return
            except Exception:
                logger.exception("Position setup confirmation failed")
                ui.notify(
                    "The starting position could not be saved.",
                    type="negative",
                )
                return

            ui.notify(
                "Starting position saved",
                type="positive",
            )
            
            result_area.clear()
            render_created_links(created_links)

        def handle_cancel_setup() -> None:
            try:
                with database_session() as session:
                    cancel_game_setup(
                        session,
                        game_id=created_links.game.id,
                        expected_version=expected_version,
                    )
            except (
                GameNotFoundError,
                StaleGameError,
                GameNotInSetupError,
            ) as error:
                ui.notify(str(error), type="negative")
                return
            except Exception:
                logger.exception("Position setup cancellation failed")
                ui.notify(
                    "The game setup could not be cancelled.",
                    type="negative",
                )
                return

            ui.notify("Game setup cancelled")
            
            result_area.clear()
            result_area.set_visibility(False)
            form_area.set_visibility(True)
            create_button.enable()


        with result_area:
            render_position_setup(
                initial_board=initial_board,
                initial_turn=initial_turn,
                initial_flipped=created_links.creator_colour == "black",
                confirm_setup=handle_confirm_setup,
                cancel_setup=handle_cancel_setup,
            )
            

    with form_area:
        creator_name = (
            ui.input(
                label="Your name",
                placeholder="e.g. Mark",
                validation=lambda value: (
                    "Your name is required"
                    if not value.strip()
                    else None
                ),
            )
            .classes("w-full")
            .props('data-1p-ignore autocomplete="off"')
        )

        opponent_name = (
            ui.input(
                label="Your opponent's name",
                placeholder="e.g. Sarah",
            )
            .classes("w-full")
            .props('data-1p-ignore autocomplete="off"')
        )

        creator_colour = ui.radio(
            {"white": "White", "black": "Black"},
            value="white",
        )
        
        start_mode = ui.radio(
            {
                "standard": "Standard position",
                "setup": "Set up existing position",
            },
            value="standard",
        ).props("inline")

        def handle_create_game() -> None:
            """Validate the form and create a persisted game."""
            creator_display_name = (
                creator_name.value or ""
            ).strip()

            opponent_display_name = (
                (opponent_name.value or "").strip() or None
            )

            selected_colour = creator_colour.value

            if not creator_display_name:
                creator_name.validate()
                return

            if selected_colour not in ("white", "black"):
                ui.notify(
                    "Choose a colour",
                    type="negative",
                )
                return
            
            selected_start_mode = start_mode.value
            if selected_start_mode not in ("standard", "setup"):
                ui.notify(
                    "Choose a starting position",
                    type="negative",
                )
                return

            create_button.disable()

            try:
                with database_session() as session:
                    created_links = create_game_for_players(
                        session,
                        creator_display_name=creator_display_name,
                        opponent_display_name=opponent_display_name,
                        creator_colour=cast(
                            Colour,
                            selected_colour,
                        ),
                        start_mode=start_mode.value,
                        app_base_url=settings.app_base_url,
                    )
                    
                    initial_board = created_links.game.board_state.copy()
                    initial_turn = cast(
                        Colour,
                        created_links.game.current_turn,
                    )
                    initial_version = created_links.game.version
            except Exception:
                logger.exception("Game creation failed")
                create_button.enable()

                ui.notify(
                    "The game could not be created. Please try again.",
                    type="negative",
                )
                return

            form_area.set_visibility(False)

            result_area.clear()

            if selected_start_mode == "setup":
                render_created_setup(
                    created_links,
                    initial_board=initial_board,
                    initial_turn=initial_turn,
                    expected_version=initial_version,
                )
            else:
                render_created_links(created_links)

            result_area.set_visibility(True)

        create_button = ui.button(
            "Create game",
            on_click=handle_create_game,
        ).props(PRIMARY_BUTTON_PROPS)

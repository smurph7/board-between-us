import logging
from typing import cast

from nicegui import ui

from app.config import get_settings
from app.database.session import database_session
from app.services.game_service import (
    CreatedGameLinks,
    create_game_for_players,
)
from app.utils.board import Colour


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
                    "Copy",
                    icon="content_copy",
                    on_click=lambda: copy_link(
                        created_links.creator_url,
                        "Your link copied",
                    ),
                )

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
                    "Copy",
                    icon="content_copy",
                    on_click=lambda: copy_link(
                        created_links.opponent_url,
                        "Invitation link copied",
                    ),
                )
            
            ui.label(
                "Copy these links now. They cannot be shown again after you leave this page."
            ).classes("text-sm font-medium pt-4")

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
                        app_base_url=settings.app_base_url,
                    )
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
            render_created_links(created_links)
            result_area.set_visibility(True)

        create_button = ui.button(
            "Create game",
            on_click=handle_create_game,
        )
from collections.abc import Callable

from nicegui import ui

from app.models.move import MoveRecord
from app.theme import SECONDARY_BUTTON_PROPS
from app.utils.formatting import format_move


def render_move_history(
    moves: list[MoveRecord],
    *,
    on_undo: Callable[[], None] | None = None,
    undo_label: str = "Undo",
) -> None:
    """Render completed events with the latest event first."""

    with ui.row().classes(
        "items-center gap-2"
    ):
        ui.label("Move history").classes(
            "text-lg font-semibold"
        )

        if on_undo is not None:
            ui.button(
                undo_label,
                on_click=on_undo,
            ).props(f"{SECONDARY_BUTTON_PROPS} dense")

    if not moves:
        ui.label("No moves yet")
        return

    for move in reversed(moves):
        if move.move_type != "correction":
            ui.label(format_move(move))
            continue

        with ui.expansion(
            format_move(move),
        ).classes("w-full"):
            for change in move.correction_changes:
                ui.label(change).classes("text-sm")

            if (
                move.previous_turn is not None
                and move.resulting_turn is not None
                and move.previous_turn != move.resulting_turn
            ):
                ui.label(
                    "Turn: "
                    f"{move.previous_turn.capitalize()} → "
                    f"{move.resulting_turn.capitalize()}"
                ).classes("text-sm")

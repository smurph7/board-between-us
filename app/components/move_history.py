from nicegui import ui

from app.models.move import MoveRecord
from app.utils.formatting import format_move


def render_move_history(moves: list[MoveRecord]) -> None:
    """Render completed moves with the latest move first."""
    ui.label("Move history").classes("text-lg font-semibold")

    if not moves:
        ui.label("No moves yet")
        return

    for move in reversed(moves):
        ui.label(format_move(move))
from nicegui import ui


@ui.page("/")
def home_page() -> None:
    """Render the public home page."""
    ui.label("Board Between Us")
    ui.label("A private shared chessboard for slow games between two people.")
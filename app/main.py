import os
from nicegui import ui

from app.pages import demo, game, home  # noqa: F401
from app import telegram  # noqa: F401
from app.theme import configure_theme


configure_theme()


def main() -> None:
    """Run the Board Between Us web application."""
    ui.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8080")),
        reload=False,
        title="Board Between Us",
        favicon="♞",
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()

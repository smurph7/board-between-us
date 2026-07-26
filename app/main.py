from nicegui import ui

from app.pages import demo, game, home  # noqa: F401


def main() -> None:
    """Run the Board Between Us web application."""
    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
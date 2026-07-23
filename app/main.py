from nicegui import ui


def main() -> None:
    """Build and run the Board Between Us web application."""
    ui.label("Board Between Us")
    ui.label("Python project setup is working.")

    ui.run()


if __name__ in {"__main__", "__mp_main__"}:
    main()
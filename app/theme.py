from nicegui import app, ui


PRIMARY_BUTTON_PROPS = "unelevated color=primary"
SECONDARY_BUTTON_PROPS = "outline color=primary"
DANGER_BUTTON_PROPS = "outline color=negative"


APP_CSS = """
:root {
    --app-background: #F6F1E7;
    --app-surface: #FFFDF8;
    --app-text: #26332D;
    --app-muted: #68756F;
    --app-border: #D8D2C5;
    --board-light: #FEF3C7;
    --board-dark: #B45309;
    --board-selected: #365C4A;
}

body {
    background: var(--app-background);
    color: var(--app-text);
    padding-bottom:
        calc(2rem + env(safe-area-inset-bottom));
}

.q-card {
    background: var(--app-surface);
    border-radius: 0.75rem;
}

.q-btn .q-btn__content {
    white-space: normal;
    line-height: 1.2;
}

.board-shell {
    width: 100%;
    max-width: 36rem;
    margin-inline: auto;
    align-items: center;
}

.board-coordinate {
    color: var(--app-muted);
    font-size: 0.75rem;
    font-weight: 600;
}

.board-square {
    cursor: pointer;
    line-height: 1;
    transition: filter 180ms ease, opacity 180ms ease;
    user-select: none;
}

.board-square-light {
    background: var(--board-light);
}

.board-square-dark {
    background: var(--board-dark);
}

.board-square-selected {
    box-shadow: inset 0 0 0 4px var(--board-selected);
}

.board-grid.board-busy .board-square {
    filter: grayscale(0.35) brightness(0.95);
    opacity: 0.82;
    pointer-events: none;
}

.piece-symbol,
.piece-button .q-btn__content {
    color: #111111;
}

.piece-button .q-btn__content {
    font-size: 1.5rem;
    line-height: 1;
}
"""


def configure_theme() -> None:
    """Configure app-wide colours, button defaults, and shared CSS."""

    app.colors(
        primary="#365C4A",
        secondary="#A86F45",
        accent="#D4AE68",
        positive="#4F7A59",
        negative="#A44747",
    )

    ui.button.default_props("no-caps")
    ui.button.default_classes(
        "px-4 min-h-10 rounded-lg "
        "text-sm font-medium touch-manipulation"
    )

    def add_shared_css() -> None:
        ui.add_css(APP_CSS, shared=True)

    app.on_startup(add_shared_css)

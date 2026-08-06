from collections.abc import Callable
from dataclasses import dataclass
from functools import partial
from nicegui import ui

from app.components.game_view import render_game_view
from app.components.position_setup import render_position_setup
from app.models.move import MoveRecord
from app.theme import PRIMARY_BUTTON_PROPS, SECONDARY_BUTTON_PROPS
from app.utils.board import (
    BoardState,
    CastleSide,
    Colour,
    Square,
    can_castle,
    piece_belongs_to,
)

@dataclass(frozen=True)
class InteractiveGameState:
    """State needed by the interactive board UI."""

    board: BoardState
    current_turn: Colour
    move_history: list[MoveRecord]


@dataclass(frozen=True)
class MoveSubmission:
    """Result returned after attempting a move."""

    state: InteractiveGameState
    success_message: str | None = None
    error_message: str | None = None


type SubmitMove = Callable[
    [Square, Square, InteractiveGameState],
    MoveSubmission,
]

type SubmitCastle = Callable[
    [CastleSide, InteractiveGameState],
    MoveSubmission,
]


type SubmitCorrection = Callable[
    [BoardState, Colour, InteractiveGameState],
    MoveSubmission,
]


type SubmitUndo = Callable[
    [InteractiveGameState],
    MoveSubmission,
]


@dataclass(frozen=True)
class RenameResult:
    """Result returned after attempting to rename the board."""

    name: str | None
    success_message: str | None = None
    error_message: str | None = None


type SubmitRename = Callable[[str], RenameResult]

@dataclass(frozen=True)
class ExternalStateUpdate:
    """Result of applying a possible external game update."""

    state: InteractiveGameState
    selected_square: Square | None
    changed: bool


type LoadExternalState = Callable[
    [],
    InteractiveGameState | None,
]


def latest_undoable_record(
    move_history: list[MoveRecord],
) -> MoveRecord | None:
    """Return the latest history event which has not been undone."""

    return next(
        (
            move
            for move in reversed(move_history)
            if move.move_type != "undo"
            and not move.is_undone
        ),
        None,
    )


def undo_button_label(move: MoveRecord) -> str:
    """Return a contextual label for the undo action."""

    if move.move_type == "correction":
        return "Undo correction"

    if move.move_type == "castle":
        return "Undo castle"

    return "Undo latest move"


def undo_confirmation_text(move: MoveRecord) -> str:
    """Return a readable confirmation question."""

    actor = move.colour.capitalize()

    if move.move_type == "correction":
        return f"Undo {actor}'s board correction?"

    if move.move_type == "castle":
        return (
            f"Undo {actor}'s "
            f"{move.castle_side or ''} castle?"
        )

    if (
        move.piece is not None
        and move.from_square is not None
        and move.to_square is not None
    ):
        piece_name = move.piece.removeprefix(
            f"{move.colour}_"
        )

        return (
            f"Undo {actor}'s {piece_name} move "
            f"from {move.from_square} to {move.to_square}?"
        )

    return f"Undo {actor}'s latest event?"


def apply_external_state(
    *,
    current_state: InteractiveGameState,
    selected_square: Square | None,
    external_state: InteractiveGameState | None,
) -> ExternalStateUpdate:
    """Apply external state when one is available."""
    if external_state is None or external_state is current_state:
        return ExternalStateUpdate(
            state=current_state,
            selected_square=selected_square,
            changed=False,
        )
    
    return ExternalStateUpdate(
        state=external_state,
        selected_square=None,
        changed=True,
    )    


def render_interactive_game(
    *,
    initial_state: InteractiveGameState,
    submit_move: SubmitMove,
    submit_castle: SubmitCastle | None = None,
    submit_correction: SubmitCorrection | None = None,
    submit_undo: SubmitUndo | None = None,
    submit_rename: SubmitRename | None = None,
    title: str | None = None,
    player_colour: Colour | None = None,
    initial_flipped: bool = False,
    load_external_state: LoadExternalState | None = None,
    render_status: Callable[[], None] | None = None,
) -> None:
    """Render shared selection, movement, flipping, and refresh behaviour."""
    state = initial_state
    selected_square: Square | None = None
    flipped = initial_flipped
    correcting_position = False

    def active_colour() -> Colour:
        """Return the colour this page may currently select."""
        return player_colour or state.current_turn


    def available_castle_sides() -> list[CastleSide]:
        """Return castle actions available for the selected king."""

        if submit_castle is None or selected_square is None:
            return []

        colour = active_colour()
        selected_piece = state.board.get(selected_square)

        if selected_piece != f"{colour}_king":
            return []

        sides: tuple[CastleSide, ...] = (
            "kingside",
            "queenside",
        )

        return [
            side
            for side in sides
            if can_castle(
                state.board,
                colour=colour,
                side=side,
            )
        ]


    def handle_square_click(square: Square) -> None:
        nonlocal state, selected_square

        if player_colour is not None and player_colour != state.current_turn:
            return

        if selected_square is None:
            piece = state.board.get(square)

            if piece is None:
                return

            if not piece_belongs_to(piece, active_colour()):
                return

            selected_square = square

        elif square == selected_square:
            selected_square = None

        else:
            destination_piece = state.board.get(square)

            if (
                destination_piece is not None
                and piece_belongs_to(
                    destination_piece,
                    active_colour(),
                )
            ):
                selected_square = square

            else:
                from_square = selected_square

                result = submit_move(
                    from_square,
                    square,
                    state,
                )

                state = result.state
                selected_square = None

                if result.success_message:
                    ui.notify(result.success_message)

                if result.error_message:
                    ui.notify(
                        result.error_message,
                        type="negative",
                    )

        game_view.refresh()

    def toggle_orientation() -> None:
        nonlocal flipped

        flipped = not flipped
        game_view.refresh()

    def clear_selection() -> None:
        nonlocal selected_square

        if selected_square is None:
            return

        selected_square = None
        game_view.refresh()
        
    def refresh_external_state() -> None:
        nonlocal state, selected_square, correcting_position
        
        if load_external_state is None:
            return
        
        external_state = load_external_state()
        
        update = apply_external_state(
            current_state=state,
            selected_square=selected_square,
            external_state=external_state,
        )
        
        if not update.changed:
            return
        
        state = update.state
        selected_square = update.selected_square
        correcting_position = False
        game_view.refresh()


    def show_castle_confirmation(side: CastleSide) -> None:
        """Ask the player to confirm a compound castling action."""
        nonlocal state, selected_square

        if submit_castle is None:
            return

        colour = active_colour()
        rank = "1" if colour == "white" else "8"

        if side == "kingside":
            king_move = f"e{rank} → g{rank}"
            rook_move = f"h{rank} → f{rank}"
        else:
            king_move = f"e{rank} → c{rank}"
            rook_move = f"a{rank} → d{rank}"

        def confirm_castle() -> None:
            nonlocal state, selected_square

            result = submit_castle(
                side,
                state,
            )

            state = result.state
            selected_square = None
            dialog.close()

            if result.success_message:
                ui.notify(result.success_message)

            if result.error_message:
                ui.notify(
                    result.error_message,
                    type="negative",
                )

            game_view.refresh()

        with ui.dialog() as dialog, ui.card():
            ui.label(
                f"Castle {side}?"
            ).classes("text-h6")

            ui.label(f"King {king_move}")
            ui.label(f"Rook {rook_move}")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Cancel",
                    on_click=dialog.close,
                ).props("flat")

                ui.button(
                    "Confirm castle",
                    on_click=confirm_castle,
                ).props(PRIMARY_BUTTON_PROPS)

        dialog.open()
        
    
    def enter_correction_mode() -> None:
        """Open the correction editor from the latest displayed state."""
        nonlocal correcting_position, selected_square

        if submit_correction is None:
            return

        selected_square = None
        correcting_position = True
        game_view.refresh()


    def cancel_correction() -> None:
        """Discard local correction edits and return to the game."""
        nonlocal correcting_position

        correcting_position = False
        game_view.refresh()


    def save_correction(
        corrected_board: BoardState,
        corrected_turn: Colour,
    ) -> None:
        """Submit a corrected board and return to the normal game view."""
        nonlocal state, selected_square, correcting_position

        if submit_correction is None:
            return

        result = submit_correction(
            corrected_board,
            corrected_turn,
            state,
        )

        state = result.state
        selected_square = None
        correcting_position = False

        if result.success_message:
            ui.notify(
                result.success_message,
                type="positive",
            )

        if result.error_message:
            ui.notify(
                result.error_message,
                type="negative",
            )

        game_view.refresh()
        
    
    def show_undo_confirmation() -> None:
        """Ask the player to confirm undoing the latest active event."""
        nonlocal state, selected_square

        if submit_undo is None:
            return

        target = latest_undoable_record(
            state.move_history,
        )

        if target is None:
            return

        def confirm_undo() -> None:
            nonlocal state, selected_square

            result = submit_undo(state)

            state = result.state
            selected_square = None
            dialog.close()

            if result.success_message:
                ui.notify(
                    result.success_message,
                    type="positive",
                )

            if result.error_message:
                ui.notify(
                    result.error_message,
                    type="negative",
                )

            game_view.refresh()

        with ui.dialog() as dialog, ui.card():
            ui.label("Confirm undo").classes("text-h6")
            ui.label(undo_confirmation_text(target))

            with ui.row().classes(
                "w-full justify-end gap-2"
            ):
                ui.button(
                    "Cancel",
                    on_click=dialog.close,
                ).props("flat")

                ui.button(
                    "Undo",
                    on_click=confirm_undo,
                ).props(PRIMARY_BUTTON_PROPS)

        dialog.open()


    def show_rename_dialog() -> None:
        """Ask the player for a new board name and persist it."""
        nonlocal title

        if submit_rename is None:
            return

        def confirm_rename() -> None:
            nonlocal title

            result = submit_rename(name_input.value or "")

            title = result.name
            dialog.close()

            if result.success_message:
                ui.notify(
                    result.success_message,
                    type="positive",
                )

            if result.error_message:
                ui.notify(
                    result.error_message,
                    type="negative",
                )

            game_view.refresh()

        with ui.dialog() as dialog, ui.card().classes(
            "w-96 max-w-[90vw] gap-3"
        ):
            ui.label("Rename board").classes("text-h6")

            name_input = ui.input(
                label="Board name",
                value=title or "",
                placeholder="Board Between Us",
            ).classes("w-full")

            with ui.row().classes("w-full justify-end gap-2"):
                ui.button(
                    "Cancel",
                    on_click=dialog.close,
                ).props("flat")

                ui.button(
                    "Save",
                    on_click=confirm_rename,
                ).props(PRIMARY_BUTTON_PROPS)

        dialog.open()


    @ui.refreshable
    def game_view() -> None:
        if correcting_position:
            render_position_setup(
                initial_board=state.board,
                initial_turn=state.current_turn,
                initial_flipped=flipped,
                confirm_setup=save_correction,
                cancel_setup=cancel_correction,
                title="Correct board position",
                confirm_label="Save correction",
                cancel_label="Cancel",
            )
            return
        
        with ui.row().classes("items-center gap-1"):
            ui.label(title or "Board Between Us").classes(
                "text-h5 font-semibold"
            )

            if submit_rename is not None:
                ui.button(
                    icon="edit",
                    on_click=show_rename_dialog,
                ).props("flat round dense size=sm")

        castle_sides = available_castle_sides()

        if castle_sides:
            ui.label("Special move").classes(
                "text-subtitle2 mt-2"
            )

            with ui.row().classes(
                "w-full gap-2 flex-wrap"
            ) as castle_actions:
                for side in castle_sides:
                    label = (
                        "Castle kingside"
                        if side == "kingside"
                        else "Castle queenside"
                    )

                    ui.button(
                        label,
                        on_click=partial(
                            show_castle_confirmation,
                            side,
                        ),
                    ).props(PRIMARY_BUTTON_PROPS)

            castle_actions.on(
                "click",
                js_handler="(event) => event.stopPropagation()",
            )
            
        if submit_correction is not None:
            ui.button(
                "Correct position",
                on_click=enter_correction_mode,
            ).props(SECONDARY_BUTTON_PROPS)
        
            
        undo_target = latest_undoable_record(
            state.move_history
        )
            
        render_game_view(
            board=state.board,
            selected_square=selected_square,
            current_turn=state.current_turn,
            move_history=state.move_history,
            flipped=flipped,
            on_square_click=handle_square_click,
            on_flip=toggle_orientation,
            player_colour=player_colour,
            on_undo=(
                show_undo_confirmation
                if submit_undo is not None
                and undo_target is not None
                else None
            ),
            undo_label=(
                undo_button_label(undo_target)
                if undo_target is not None
                else "Undo"
            ),
            render_status=render_status,
        )
    
    
    with ui.column().classes(
        "w-full min-h-screen gap-4 p-4 sm:p-6"
    ).on(
        "click",
        clear_selection,
    ):
        game_view()
        
        if load_external_state is not None:
            ui.timer(2.0, refresh_external_state)

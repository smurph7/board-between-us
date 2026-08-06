from dataclasses import dataclass, replace
import logging
from time import perf_counter
from typing import cast
from uuid import UUID

from nicegui import ui
from sqlalchemy.orm import Session

from app.config import get_settings
from app.components.interactive_game import (
    InteractiveGameState,
    MoveSubmission,
    RenameResult,
    latest_undoable_record,
    render_interactive_game,
)
from app.models.persisted_move import Move
from app.database.session import database_session
from app.services.game_service import (
    GameNotActiveError,
    correct_game_position,
    load_player_game,
)
from app.services.move_service import (
    MoveError,
    get_move_history,
    make_move,
    make_castle,
    persisted_move_to_record,
    undo_latest_event,
)
from app.repositories.game_repository import (
    get_game,
    get_game_version,
    update_game_name,
)
from app.repositories.player_repository import (
    disconnect_telegram,
    ensure_telegram_link_token,
    get_other_player,
    get_player,
    set_notifications_enabled,
)
from app.services.telegram_service import (
    TelegramMessage,
    build_move_notification,
    send_telegram_message,
    telegram_deep_link,
)
from app.services.token_service import generate_telegram_link_token
from app.utils.game_sync import game_version_changed
from app.utils.board import BoardState, CastleSide, Colour, Square


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TelegramPlayerStatus:
    """Telegram state displayed on one private player page."""

    link_token: str
    connected: bool
    notifications_enabled: bool


def append_persisted_move(
    *,
    state: InteractiveGameState,
    board: BoardState,
    current_turn: Colour,
    move: Move,
    actor_colour: Colour,
) -> InteractiveGameState:
    """Append a successfully persisted event without reloading history."""
    return InteractiveGameState(
        board=board,
        current_turn=current_turn,
        move_history=[
            *state.move_history,
            persisted_move_to_record(
                move,
                colour=actor_colour,
            ),
        ],
    )


def append_persisted_undo(
    *,
    state: InteractiveGameState,
    board: BoardState,
    current_turn: Colour,
    move: Move,
    actor_colour: Colour,
) -> InteractiveGameState:
    """Mark the local target as undone and append the undo event."""
    history = [*state.move_history]
    target = latest_undoable_record(history)

    if target is not None:
        target_index = history.index(target)
        history[target_index] = replace(
            target,
            is_undone=True,
        )

    return InteractiveGameState(
        board=board,
        current_turn=current_turn,
        move_history=[
            *history,
            persisted_move_to_record(
                move,
                colour=actor_colour,
            ),
        ],
    )


@ui.page("/play/{game_id}/{access_token}")
def persisted_game_page(
    game_id: str,
    access_token: str,
) -> None:
    """Render a persisted game through a private player link."""
    settings = get_settings()
    try:
        parsed_game_id = UUID(game_id)
    except ValueError:
        ui.label("This player link is invalid or no longer available.")
        return

    with database_session() as session:
        player_game = load_player_game(
            session,
            game_id=parsed_game_id,
            access_token=access_token,
        )

        if player_game is None:
            ui.label("This player link is invalid or no longer available.")
            return

        persisted_game_id = player_game.game.id
        player_id = player_game.player.id
        player_colour = cast(
            Colour,
            player_game.player.colour,
        )
        game_name = player_game.game.name
        game_status = player_game.game.status
        telegram_link_token = ensure_telegram_link_token(
            session,
            player_game.player,
            token=generate_telegram_link_token(),
        )
        initial_telegram_status = TelegramPlayerStatus(
            link_token=telegram_link_token,
            connected=player_game.player.telegram_chat_id is not None,
            notifications_enabled=player_game.player.notifications_enabled,
        )

        initial_state = InteractiveGameState(
            board=player_game.game.board_state.copy(),
            current_turn=cast(
                Colour,
                player_game.game.current_turn,
            ),
            move_history=get_move_history(
                session,
                persisted_game_id,
            ),
        )

        initial_version = player_game.game.version

    version = initial_version
    telegram_status = initial_telegram_status

    def deliver_notification(
        message: TelegramMessage | None,
    ) -> bool:
        """Deliver a prepared message after its move transaction committed."""
        if message is None:
            return True
        if settings.telegram_bot_token is None:
            logger.warning(
                "Telegram delivery skipped because the bot is not configured"
            )
            return False
        return send_telegram_message(
            bot_token=settings.telegram_bot_token,
            message=message,
        )

    def prepare_notification(
        session: Session,
        move: Move,
    ) -> TelegramMessage | None:
        """Snapshot recipient data while the successful transaction is open."""
        actor = get_player(session, player_id)
        recipient = get_other_player(
            session,
            game_id=persisted_game_id,
            player_id=player_id,
        )
        if actor is None or recipient is None:
            return None
        return build_move_notification(
            move=move,
            actor=actor,
            recipient=recipient,
            app_base_url=settings.app_base_url,
            game_name=game_name,
        )

    def load_current_state() -> InteractiveGameState | None:
        """Reload the canonical game state from the database."""
        nonlocal version

        with database_session() as session:
            loaded = load_player_game(
                session,
                game_id=persisted_game_id,
                access_token=access_token,
            )

            if loaded is None:
                return None

            version = loaded.game.version

            return InteractiveGameState(
                board=loaded.game.board_state.copy(),
                current_turn=cast(
                    Colour,
                    loaded.game.current_turn,
                ),
                move_history=get_move_history(
                    session,
                    persisted_game_id,
                ),
            )

    def submit_persisted_move(
        from_square: Square,
        to_square: Square,
        state: InteractiveGameState,
    ) -> MoveSubmission:
        """Persist one move and return the latest shared state."""
        nonlocal version
        started_at = perf_counter()

        try:
            notification = None
            with database_session() as session:
                completed = make_move(
                    session,
                    game_id=persisted_game_id,
                    player_id=player_id,
                    from_square=from_square,
                    to_square=to_square,
                    expected_version=version,
                )

                version = completed.game.version

                updated_state = append_persisted_move(
                    state=state,
                    board=completed.game.board_state.copy(),
                    current_turn=cast(
                        Colour,
                        completed.game.current_turn,
                    ),
                    move=completed.move,
                    actor_colour=player_colour,
                )

                notification = prepare_notification(
                    session,
                    completed.move,
                )

            delivered = deliver_notification(notification)

            return MoveSubmission(
                state=updated_state,
                success_message=(
                    "Move saved"
                    if delivered
                    else (
                        "Move saved, but Telegram notification "
                        "could not be sent"
                    )
                ),
            )

        except MoveError as error:
            latest_state = load_current_state()

            return MoveSubmission(
                state=latest_state or state,
                error_message=str(error),
            )
        finally:
            elapsed_ms = (perf_counter() - started_at) * 1000
            logger.info(
                "Persisted move %s-%s in %.0fms",
                from_square,
                to_square,
                elapsed_ms,
            )

    def submit_persisted_castle(
        side: CastleSide,
        state: InteractiveGameState,
    ) -> MoveSubmission:
        """Persist one castle and return the latest shared state."""
        nonlocal version
        started_at = perf_counter()

        try:
            notification = None
            with database_session() as session:
                completed = make_castle(
                    session,
                    game_id=persisted_game_id,
                    player_id=player_id,
                    side=side,
                    expected_version=version,
                )

                version = completed.game.version

                updated_state = append_persisted_move(
                    state=state,
                    board=completed.game.board_state.copy(),
                    current_turn=cast(
                        Colour,
                        completed.game.current_turn,
                    ),
                    move=completed.move,
                    actor_colour=player_colour,
                )

                notification = prepare_notification(
                    session,
                    completed.move,
                )

            delivered = deliver_notification(notification)

            return MoveSubmission(
                state=updated_state,
                success_message=(
                    f"Castled {side}"
                    if delivered
                    else (
                        "Castle saved, but Telegram notification "
                        "could not be sent"
                    )
                ),
            )

        except MoveError as error:
            latest_state = load_current_state()

            return MoveSubmission(
                state=latest_state or state,
                error_message=str(error),
            )
        finally:
            elapsed_ms = (perf_counter() - started_at) * 1000
            logger.info(
                "Persisted %s castle in %.0fms",
                side,
                elapsed_ms,
            )

    def submit_persisted_correction(
        corrected_board: BoardState,
        corrected_turn: Colour,
        state: InteractiveGameState,
    ) -> MoveSubmission:
        """Persist a board correction and return the shared state."""
        nonlocal version
        started_at = perf_counter()

        try:
            with database_session() as session:
                completed = correct_game_position(
                    session,
                    game_id=persisted_game_id,
                    player_id=player_id,
                    board_state=corrected_board,
                    next_turn=corrected_turn,
                    expected_version=version,
                )

                version = completed.game.version

                updated_state = append_persisted_move(
                    state=state,
                    board=completed.game.board_state.copy(),
                    current_turn=cast(
                        Colour,
                        completed.game.current_turn,
                    ),
                    move=completed.move,
                    actor_colour=player_colour,
                )

            return MoveSubmission(
                state=updated_state,
                success_message="Board position corrected",
            )

        except (MoveError, GameNotActiveError) as error:
            latest_state = load_current_state()

            return MoveSubmission(
                state=latest_state or state,
                error_message=str(error),
            )
        finally:
            elapsed_ms = (perf_counter() - started_at) * 1000
            logger.info(
                "Persisted correction in %.0fms",
                elapsed_ms,
            )

    def submit_persisted_undo(
        state: InteractiveGameState,
    ) -> MoveSubmission:
        """Undo the latest active event and return shared state."""
        nonlocal version
        started_at = perf_counter()

        try:
            with database_session() as session:
                completed = undo_latest_event(
                    session,
                    game_id=persisted_game_id,
                    player_id=player_id,
                    expected_version=version,
                )

                version = completed.game.version

                updated_state = append_persisted_undo(
                    state=state,
                    board=completed.game.board_state.copy(),
                    current_turn=cast(
                        Colour,
                        completed.game.current_turn,
                    ),
                    move=completed.move,
                    actor_colour=player_colour,
                )

            return MoveSubmission(
                state=updated_state,
                success_message="Latest event undone",
            )

        except MoveError as error:
            latest_state = load_current_state()

            return MoveSubmission(
                state=latest_state or state,
                error_message=str(error),
            )
        finally:
            elapsed_ms = (perf_counter() - started_at) * 1000
            logger.info(
                "Persisted undo in %.0fms",
                elapsed_ms,
            )

    def submit_persisted_rename(new_name: str) -> RenameResult:
        """Persist a new board name and return the saved result."""
        nonlocal game_name

        trimmed = new_name.strip() or None

        with database_session() as session:
            game = get_game(session, persisted_game_id)

            if game is None:
                return RenameResult(
                    name=game_name,
                    error_message="Game not found",
                )

            update_game_name(session, game, name=trimmed)

        game_name = trimmed

        return RenameResult(
            name=trimmed,
            success_message="Board renamed",
        )

    def load_external_state() -> InteractiveGameState | None:
        """Return canonical state only when the persisted version changed."""
        with database_session() as session:
            database_version = get_game_version(
                session,
                persisted_game_id,
            )

        if database_version is None:
            return None

        if not game_version_changed(version, database_version):
            return None

        return load_current_state()

    def load_telegram_status() -> TelegramPlayerStatus | None:
        """Load the current player's Telegram connection state."""
        with database_session() as session:
            player = get_player(session, player_id)
            if player is None or player.telegram_link_token is None:
                return None
            return TelegramPlayerStatus(
                link_token=player.telegram_link_token,
                connected=player.telegram_chat_id is not None,
                notifications_enabled=player.notifications_enabled,
            )

    def refresh_telegram_status() -> None:
        """Refresh Telegram controls when the webhook changes the seat."""
        nonlocal telegram_status
        current = load_telegram_status()
        if current is None or current == telegram_status:
            return
        telegram_status = current
        telegram_controls.refresh()

    def update_notification_preference(event) -> None:
        """Persist this player's Telegram notification preference."""
        nonlocal telegram_status
        enabled = bool(event.value)
        with database_session() as session:
            player = get_player(session, player_id)
            if player is None:
                return
            set_notifications_enabled(
                session,
                player,
                enabled=enabled,
            )
        telegram_status = replace(
            telegram_status,
            notifications_enabled=enabled,
        )

    def show_disconnect_confirmation() -> None:
        """Confirm Telegram disconnection and credential revocation."""
        def confirm_disconnect() -> None:
            nonlocal telegram_status
            replacement_token = generate_telegram_link_token()
            with database_session() as session:
                player = get_player(session, player_id)
                if player is None:
                    return
                disconnect_telegram(
                    session,
                    player,
                    replacement_token=replacement_token,
                )
            telegram_status = TelegramPlayerStatus(
                link_token=replacement_token,
                connected=False,
                notifications_enabled=True,
            )
            dialog.close()
            telegram_controls.refresh()

        with ui.dialog() as dialog, ui.card():
            ui.label("Disconnect Telegram?").classes("text-h6")
            ui.label("Old Telegram board links will stop working.")
            with ui.row().classes("w-full justify-end gap-2"):
                ui.button("Cancel", on_click=dialog.close).props("flat")
                ui.button(
                    "Disconnect",
                    on_click=confirm_disconnect,
                ).props("outline color=negative")
        dialog.open()

    @ui.refreshable
    def telegram_controls() -> None:
        """Render seat-specific Telegram connection controls."""
        with ui.expansion("Telegram", value=False).classes("w-full"):
            with ui.column().classes("w-full gap-2 pb-2"):

                if (
                    not settings.telegram_bot_token
                    or not settings.telegram_bot_username
                ):
                    ui.label("Telegram is not configured.").classes(
                        "text-sm text-grey-7"
                    )
                    return

                if not telegram_status.connected:
                    deep_link = telegram_deep_link(
                        settings.telegram_bot_username,
                        telegram_status.link_token,
                    )
                    ui.button(
                        "Connect Telegram",
                        on_click=lambda: ui.navigate.to(
                            deep_link,
                            new_tab=True,
                        ),
                    ).props("outline color=primary")
                    return

                ui.label("Telegram connected").classes(
                    "text-sm text-positive"
                )
                ui.switch(
                    "Move notifications",
                    value=telegram_status.notifications_enabled,
                    on_change=update_notification_preference,
                )
                ui.button(
                    "Disconnect Telegram",
                    on_click=show_disconnect_confirmation,
                ).props("flat color=negative")

    if game_status == "setup":
        ui.label(
            "This game is still being set up by its creator."
        )
        return

    render_interactive_game(
        title=game_name,
        initial_state=initial_state,
        submit_move=submit_persisted_move,
        submit_castle=submit_persisted_castle,
        submit_correction=submit_persisted_correction,
        submit_undo=submit_persisted_undo,
        submit_rename=submit_persisted_rename,
        player_colour=player_colour,
        initial_flipped=player_colour == "black",
        load_external_state=load_external_state,
        render_status=telegram_controls,
    )
    ui.timer(2.0, refresh_telegram_status)

from dataclasses import dataclass
import logging
from typing import Any, Literal

import httpx
from sqlalchemy.orm import Session

from app.models.persisted_move import Move
from app.models.player import Player
from app.repositories.player_repository import (
    connect_telegram,
    get_player_by_telegram_link_token,
)


logger = logging.getLogger(__name__)

type TelegramConnectionStatus = Literal[
    "connected",
    "already_connected",
    "conflict",
    "invalid_token",
]


@dataclass(frozen=True)
class TelegramStart:
    """A supported private-chat Telegram start request."""

    chat_id: str
    token: str


@dataclass(frozen=True)
class TelegramConnection:
    """The result of associating a Telegram chat with a seat."""

    status: TelegramConnectionStatus
    player: Player | None = None


@dataclass(frozen=True)
class TelegramMessage:
    """A Telegram message and its optional private board link."""

    chat_id: str
    text: str
    board_url: str | None = None


def telegram_deep_link(bot_username: str, token: str) -> str:
    """Return a Telegram bot start link for one player seat."""
    username = bot_username.removeprefix("@")
    return f"https://t.me/{username}?start={token}"


def telegram_board_url(app_base_url: str, token: str) -> str:
    """Return the dedicated private board URL for a Telegram seat."""
    return f"{app_base_url.rstrip('/')}/telegram/play/{token}"


def parse_telegram_start(update: dict[str, Any]) -> TelegramStart | None:
    """Parse a private-chat `/start TOKEN` update, if supported."""
    message = update.get("message")
    if not isinstance(message, dict):
        return None

    chat = message.get("chat")
    text = message.get("text")
    if not isinstance(chat, dict) or not isinstance(text, str):
        return None
    if chat.get("type") != "private":
        return None

    chat_id = chat.get("id")
    if not isinstance(chat_id, (int, str)):
        return None

    command, separator, token = text.strip().partition(" ")
    command = command.split("@", maxsplit=1)[0]
    if command != "/start" or not separator or not token:
        return None
    if len(token) > 64:
        return None
    if any(character not in _TOKEN_CHARACTERS for character in token):
        return None

    return TelegramStart(chat_id=str(chat_id), token=token)


def _attach_chat_or_detect_conflict(
    session: Session,
    player: Player,
    chat_id: str,
) -> TelegramConnectionStatus:
    """Attach a chat id to an unclaimed seat, or report why it can't be."""
    if player.telegram_chat_id == chat_id:
        return "already_connected"
    if player.telegram_chat_id is not None:
        return "conflict"
    connect_telegram(session, player, chat_id=chat_id)
    return "connected"


def connect_player_from_telegram(
    session: Session,
    start: TelegramStart,
) -> TelegramConnection:
    """Connect an unclaimed seat, or accept an idempotent repeat."""
    player = get_player_by_telegram_link_token(session, start.token)
    if player is None:
        return TelegramConnection(status="invalid_token")

    status = _attach_chat_or_detect_conflict(session, player, start.chat_id)
    if status == "conflict":
        return TelegramConnection(status="conflict")
    return TelegramConnection(status=status, player=player)


def attach_cached_telegram_chat(
    session: Session,
    *,
    player: Player,
    other_player: Player | None,
    chat_id: str,
) -> TelegramConnection:
    """Auto-attach a device-cached chat id to a fresh, unconnected seat."""
    if other_player is not None and other_player.telegram_chat_id == chat_id:
        return TelegramConnection(status="conflict", player=player)

    status = _attach_chat_or_detect_conflict(session, player, chat_id)
    return TelegramConnection(status=status, player=player)


def build_move_notification(
    *,
    move: Move,
    actor: Player,
    recipient: Player,
    app_base_url: str,
    game_name: str | None = None,
) -> TelegramMessage | None:
    """Build an opponent notification for a supported committed move."""
    if move.move_type not in {"move", "capture", "castle"}:
        return None
    if recipient.telegram_chat_id is None:
        return None
    if recipient.telegram_link_token is None:
        return None
    if not recipient.notifications_enabled:
        return None
    if recipient.colour != move.resulting_turn:
        return None

    actor_name = actor.display_name or actor.colour.title()
    prefix = f"🎲 {game_name}\n\n" if game_name else ""

    if move.move_type == "castle":
        destination = move.to_square or ""
        side = (
            "kingside"
            if destination.endswith("g1") or destination.endswith("g8")
            else "queenside"
        )
        text = f"{prefix}♟ {actor_name} castled {side}\n\nIt’s your turn."
    else:
        if move.piece is None or move.from_square is None or move.to_square is None:
            return None
        piece_name = move.piece.removeprefix(f"{actor.colour}_").title()
        separator = "×" if move.move_type == "capture" else "→"
        text = (
            f"{prefix}♟ {actor_name} moved\n\n"
            f"{piece_name}: {move.from_square} {separator} {move.to_square}\n\n"
            "It’s your turn."
        )

    return TelegramMessage(
        chat_id=recipient.telegram_chat_id,
        text=text,
        board_url=telegram_board_url(
            app_base_url,
            recipient.telegram_link_token,
        ),
    )


def send_telegram_message(
    *,
    bot_token: str,
    message: TelegramMessage,
    timeout: float = 3.0,
) -> bool:
    """Send one Bot API message, returning False on any delivery failure."""
    payload: dict[str, Any] = {
        "chat_id": message.chat_id,
        "text": message.text,
    }
    if message.board_url is not None:
        payload["reply_markup"] = {
            "inline_keyboard": [[{
                "text": "Open board",
                "url": message.board_url,
            }]],
        }

    try:
        response = httpx.post(
            f"https://api.telegram.org/bot{bot_token}/sendMessage",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        body = response.json()
        if not isinstance(body, dict) or body.get("ok") is not True:
            logger.warning(
                "Telegram rejected a message: %s",
                body.get("description") if isinstance(body, dict) else body,
            )
            return False
    except httpx.HTTPStatusError as error:
        try:
            description = error.response.json().get("description")
        except ValueError:
            description = error.response.text
        logger.warning(
            "Telegram message delivery failed (HTTP %s): %s",
            error.response.status_code,
            description,
        )
        return False
    except (httpx.HTTPError, ValueError) as error:
        logger.warning(
            "Telegram message delivery failed (%s)",
            type(error).__name__,
        )
        return False

    return True


def register_telegram_webhook(
    *,
    bot_token: str,
    app_base_url: str,
    webhook_secret: str,
    timeout: float = 10.0,
) -> bool:
    """Register this application as the bot's webhook target."""
    payload = {
        "url": f"{app_base_url.rstrip('/')}/api/telegram/webhook",
        "secret_token": webhook_secret,
        "allowed_updates": ["message"],
    }
    try:
        response = httpx.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        body = response.json()
        return isinstance(body, dict) and body.get("ok") is True
    except (httpx.HTTPError, ValueError) as error:
        logger.warning(
            "Telegram webhook registration failed (%s)",
            type(error).__name__,
        )
        return False


_TOKEN_CHARACTERS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
)

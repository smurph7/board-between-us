from uuid import uuid4
from types import SimpleNamespace

import httpx
import pytest
from fastapi import HTTPException
from starlette.requests import Request
from sqlalchemy.orm import Session

from app.models.persisted_move import Move
from app.models.player import Player
from app.services.telegram_service import (
    TelegramStart,
    TelegramMessage,
    build_move_notification,
    connect_player_from_telegram,
    parse_telegram_start,
    register_telegram_webhook,
    send_telegram_message,
    telegram_board_url,
    telegram_deep_link,
)
from app.services.game_service import create_standard_game
from app import telegram as telegram_routes


def player(
    *,
    colour: str,
    display_name: str | None = None,
    chat_id: str | None = None,
    notifications_enabled: bool = True,
) -> Player:
    """Build a player model for pure Telegram service tests."""
    return Player(
        id=uuid4(),
        game_id=uuid4(),
        colour=colour,
        display_name=display_name,
        access_token_hash="hash",
        telegram_link_token=f"{colour}-telegram-token",
        telegram_chat_id=chat_id,
        notifications_enabled=notifications_enabled,
    )


def move(
    *,
    move_type: str = "move",
    piece: str | None = "white_pawn",
    from_square: str | None = "e2",
    to_square: str | None = "e4",
    resulting_turn: str = "black",
) -> Move:
    """Build a persisted move model for pure formatter tests."""
    return Move(
        id=uuid4(),
        game_id=uuid4(),
        player_id=uuid4(),
        sequence_number=1,
        move_type=move_type,
        piece=piece,
        from_square=from_square,
        to_square=to_square,
        captured_piece=None,
        changes=[],
        board_state_before={},
        board_state_after={},
        previous_turn="white",
        resulting_turn=resulting_turn,
    )


def test_telegram_links_are_seat_specific() -> None:
    assert telegram_deep_link("@board_bot", "seat-token") == (
        "https://t.me/board_bot?start=seat-token"
    )
    assert telegram_board_url("https://board.example/", "seat-token") == (
        "https://board.example/telegram/play/seat-token"
    )


def test_parse_private_start_update() -> None:
    parsed = parse_telegram_start({
        "message": {
            "chat": {"id": 12345, "type": "private"},
            "text": "/start seat-token_123",
        },
    })

    assert parsed is not None
    assert parsed.chat_id == "12345"
    assert parsed.token == "seat-token_123"


def test_webhook_rejects_invalid_secret_before_processing(monkeypatch) -> None:
    monkeypatch.setattr(
        telegram_routes,
        "get_settings",
        lambda: SimpleNamespace(
            telegram_webhook_secret="expected-secret",
            telegram_bot_token="bot-token",
        ),
    )
    request = Request({
        "type": "http",
        "headers": [
            (b"x-telegram-bot-api-secret-token", b"wrong-secret"),
        ],
    })

    with pytest.raises(HTTPException) as error:
        telegram_routes.telegram_webhook({}, request)

    assert error.value.status_code == 403


def test_connect_player_is_idempotent_and_rejects_another_chat(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)
    token = created.white_player.telegram_link_token
    assert token is not None

    connected = connect_player_from_telegram(
        db_session,
        TelegramStart(chat_id="100", token=token),
    )
    repeated = connect_player_from_telegram(
        db_session,
        TelegramStart(chat_id="100", token=token),
    )
    conflict = connect_player_from_telegram(
        db_session,
        TelegramStart(chat_id="200", token=token),
    )

    assert connected.status == "connected"
    assert repeated.status == "already_connected"
    assert conflict.status == "conflict"
    assert created.white_player.telegram_chat_id == "100"
    assert created.white_player.telegram_connected_at is not None


def test_connect_player_rejects_unknown_token(
    db_session: Session,
) -> None:
    connection = connect_player_from_telegram(
        db_session,
        TelegramStart(chat_id="100", token="unknown-token"),
    )

    assert connection.status == "invalid_token"
    assert connection.player is None


@pytest.mark.parametrize(
    "update",
    [
        {},
        {"message": {"chat": {"id": 1, "type": "group"}, "text": "/start token"}},
        {"message": {"chat": {"id": 1, "type": "private"}, "text": "/help"}},
        {"message": {"chat": {"id": 1, "type": "private"}, "text": "/start bad token"}},
    ],
)
def test_parse_telegram_start_ignores_unsupported_updates(update: dict) -> None:
    assert parse_telegram_start(update) is None


def test_build_ordinary_move_notification() -> None:
    notification = build_move_notification(
        move=move(),
        actor=player(colour="white", display_name="Sarah"),
        recipient=player(colour="black", chat_id="99"),
        app_base_url="https://board.example",
    )

    assert notification == TelegramMessage(
        chat_id="99",
        text="♟ Sarah moved\n\nPawn: e2 → e4\n\nIt’s your turn.",
        board_url=(
            "https://board.example/telegram/play/black-telegram-token"
        ),
    )


def test_build_move_notification_omits_prefix_without_game_name() -> None:
    notification = build_move_notification(
        move=move(),
        actor=player(colour="white", display_name="Sarah"),
        recipient=player(colour="black", chat_id="99"),
        app_base_url="https://board.example",
    )

    assert notification is not None
    assert notification.text == "♟ Sarah moved\n\nPawn: e2 → e4\n\nIt’s your turn."


def test_build_move_notification_includes_game_name_when_set() -> None:
    notification = build_move_notification(
        move=move(),
        actor=player(colour="white", display_name="Sarah"),
        recipient=player(colour="black", chat_id="99"),
        app_base_url="https://board.example",
        game_name="Mark vs Sarah",
    )

    assert notification is not None
    assert notification.text == (
        "🎲 Mark vs Sarah\n\n♟ Sarah moved\n\nPawn: e2 → e4\n\nIt’s your turn."
    )


def test_build_capture_notification() -> None:
    notification = build_move_notification(
        move=move(
            move_type="capture",
            piece="white_bishop",
            from_square="c4",
            to_square="f7",
        ),
        actor=player(colour="white"),
        recipient=player(colour="black", chat_id="99"),
        app_base_url="https://board.example",
    )

    assert notification is not None
    assert "Bishop: c4 × f7" in notification.text


def test_build_castle_notification() -> None:
    notification = build_move_notification(
        move=move(
            move_type="castle",
            piece="white_king",
            from_square="e1",
            to_square="g1",
        ),
        actor=player(colour="white", display_name="Sarah"),
        recipient=player(colour="black", chat_id="99"),
        app_base_url="https://board.example",
    )

    assert notification is not None
    assert notification.text == (
        "♟ Sarah castled kingside\n\nIt’s your turn."
    )


@pytest.mark.parametrize(
    ("move_type", "chat_id", "notifications_enabled", "resulting_turn"),
    [
        ("correction", "99", True, "black"),
        ("undo", "99", True, "black"),
        ("move", None, True, "black"),
        ("move", "99", False, "black"),
        ("move", "99", True, "white"),
    ],
)
def test_notification_exclusions(
    move_type: str,
    chat_id: str | None,
    notifications_enabled: bool,
    resulting_turn: str,
) -> None:
    notification = build_move_notification(
        move=move(move_type=move_type, resulting_turn=resulting_turn),
        actor=player(colour="white"),
        recipient=player(
            colour="black",
            chat_id=chat_id,
            notifications_enabled=notifications_enabled,
        ),
        app_base_url="https://board.example",
    )

    assert notification is None


class FakeResponse:
    def __init__(self, body: dict, status_code: int = 200) -> None:
        self.body = body
        self.status_code = status_code

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            request = httpx.Request("POST", "https://api.telegram.org")
            response = httpx.Response(self.status_code, request=request)
            raise httpx.HTTPStatusError(
                "request failed",
                request=request,
                response=response,
            )

    def json(self) -> dict:
        return self.body


def test_send_message_posts_inline_board_button(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url: str, *, json: dict, timeout: float) -> FakeResponse:
        captured.update(url=url, json=json, timeout=timeout)
        return FakeResponse({"ok": True})

    monkeypatch.setattr(httpx, "post", fake_post)

    sent = send_telegram_message(
        bot_token="secret-token",
        message=TelegramMessage(
            chat_id="99",
            text="Your turn",
            board_url="https://board.example/private",
        ),
    )

    assert sent is True
    assert captured["url"].endswith("/botsecret-token/sendMessage")
    assert captured["json"]["reply_markup"] == {
        "inline_keyboard": [[{
            "text": "Open board",
            "url": "https://board.example/private",
        }]],
    }


def test_register_webhook_uses_secret_and_message_updates(monkeypatch) -> None:
    captured: dict = {}

    def fake_post(url: str, *, json: dict, timeout: float) -> FakeResponse:
        captured.update(url=url, json=json, timeout=timeout)
        return FakeResponse({"ok": True})

    monkeypatch.setattr(httpx, "post", fake_post)

    registered = register_telegram_webhook(
        bot_token="secret-token",
        app_base_url="https://board.example/",
        webhook_secret="webhook-secret",
    )

    assert registered is True
    assert captured["json"] == {
        "url": "https://board.example/api/telegram/webhook",
        "secret_token": "webhook-secret",
        "allowed_updates": ["message"],
    }


@pytest.mark.parametrize(
    "response",
    [
        FakeResponse({"ok": False}),
        FakeResponse({"ok": False}, status_code=500),
    ],
)
def test_send_message_returns_false_for_telegram_failures(
    monkeypatch,
    response: FakeResponse,
) -> None:
    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: response)

    assert send_telegram_message(
        bot_token="secret-token",
        message=TelegramMessage(chat_id="99", text="Your turn"),
    ) is False

import secrets
from typing import Any

from fastapi import HTTPException, Request
from nicegui import app
from starlette.responses import RedirectResponse

from app.config import get_settings
from app.database.session import database_session
from app.repositories.player_repository import get_player_by_telegram_link_token
from app.services.telegram_service import (
    TelegramMessage,
    connect_player_from_telegram,
    parse_telegram_start,
    send_telegram_message,
    telegram_board_url,
)


@app.post("/api/telegram/webhook", include_in_schema=False)
def telegram_webhook(
    update: dict[str, Any],
    request: Request,
) -> dict[str, bool]:
    """Accept authenticated Telegram bot updates."""
    settings = get_settings()
    expected_secret = settings.telegram_webhook_secret
    if not expected_secret or not settings.telegram_bot_token:
        raise HTTPException(status_code=503)

    supplied_secret = request.headers.get(
        "X-Telegram-Bot-Api-Secret-Token",
        "",
    )
    if not secrets.compare_digest(supplied_secret, expected_secret):
        raise HTTPException(status_code=403)

    start = parse_telegram_start(update)
    if start is None:
        return {"ok": True}

    with database_session() as session:
        connection = connect_player_from_telegram(session, start)
        player = connection.player

    if player is not None and player.telegram_link_token is not None:
        text = (
            "Telegram is connected to your Board Between Us seat."
            if connection.status == "connected"
            else "Telegram is already connected to this seat."
        )
        message = TelegramMessage(
            chat_id=start.chat_id,
            text=text,
            board_url=telegram_board_url(
                settings.app_base_url,
                player.telegram_link_token,
            ),
        )
    elif connection.status == "conflict":
        message = TelegramMessage(
            chat_id=start.chat_id,
            text=(
                "This Board Between Us seat is already connected to "
                "another Telegram chat. Disconnect it from the board first."
            ),
        )
    else:
        message = TelegramMessage(
            chat_id=start.chat_id,
            text="This Board Between Us connection link is invalid or expired.",
        )

    send_telegram_message(
        bot_token=settings.telegram_bot_token,
        message=message,
    )
    return {"ok": True}


@app.get("/telegram/play/{telegram_link_token}", include_in_schema=False)
def telegram_player_redirect(
    telegram_link_token: str,
) -> RedirectResponse:
    """Resolve a Telegram credential to the shared player-page route."""
    with database_session() as session:
        player = get_player_by_telegram_link_token(
            session,
            telegram_link_token,
        )
        if player is None:
            return RedirectResponse(url="/", status_code=303)
        game_id = player.game_id

    return RedirectResponse(
        url=f"/play/{game_id}/{telegram_link_token}",
        status_code=303,
    )

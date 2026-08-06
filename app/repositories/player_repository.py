from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.player import Player


def create_player(
    session: Session,
    *,
    game_id: UUID,
    colour: str,
    access_token_hash: str,
    telegram_link_token: str | None = None,
    display_name: str | None = None,
) -> Player:
    """Create a player seat in the current database transaction."""
    player = Player(
        id=uuid4(),
        game_id=game_id,
        colour=colour,
        display_name=display_name,
        access_token_hash=access_token_hash,
        telegram_link_token=telegram_link_token,
    )

    session.add(player)
    session.flush()

    return player


def get_player(
    session: Session,
    player_id: UUID,
) -> Player | None:
    """Return a player by ID, or None if it does not exist."""
    return session.get(Player, player_id)


def get_player_by_token_hash(
    session: Session,
    access_token_hash: str,
) -> Player | None:
    """Return the player identified by an access-token hash."""
    statement = select(Player).where(
        Player.access_token_hash == access_token_hash,
    )

    return session.scalar(statement)


def get_player_by_telegram_link_token(
    session: Session,
    telegram_link_token: str,
) -> Player | None:
    """Return the player identified by a Telegram link token."""
    statement = select(Player).where(
        Player.telegram_link_token == telegram_link_token,
    )
    return session.scalar(statement)


def get_other_player(
    session: Session,
    *,
    game_id: UUID,
    player_id: UUID,
) -> Player | None:
    """Return the other player seat in a two-player game."""
    statement = select(Player).where(
        Player.game_id == game_id,
        Player.id != player_id,
    )
    return session.scalar(statement)


def ensure_telegram_link_token(
    session: Session,
    player: Player,
    *,
    token: str,
) -> str:
    """Persist a Telegram link token when an existing seat lacks one."""
    if player.telegram_link_token is None:
        player.telegram_link_token = token
        session.flush()
    return player.telegram_link_token


def connect_telegram(
    session: Session,
    player: Player,
    *,
    chat_id: str,
) -> None:
    """Associate a Telegram private chat with a player seat."""
    player.telegram_chat_id = chat_id
    if player.telegram_connected_at is None:
        player.telegram_connected_at = datetime.now(timezone.utc)
    session.flush()


def set_notifications_enabled(
    session: Session,
    player: Player,
    *,
    enabled: bool,
) -> None:
    """Update one player's Telegram notification preference."""
    player.notifications_enabled = enabled
    session.flush()


def disconnect_telegram(
    session: Session,
    player: Player,
) -> None:
    """Stop notifications without invalidating existing Telegram board links."""
    player.telegram_chat_id = None
    player.telegram_connected_at = None
    player.notifications_enabled = True
    session.flush()

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
    display_name: str | None = None,
) -> Player:
    """Create a player seat in the current database transaction."""
    player = Player(
        id=uuid4(),
        game_id=game_id,
        colour=colour,
        display_name=display_name,
        access_token_hash=access_token_hash,
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
"""create players table

Revision ID: f17d603f0711
Revises: abcbabd3cfba
Create Date: 2026-07-26 11:47:38.854920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f17d603f0711'
down_revision: Union[str, Sequence[str], None] = 'abcbabd3cfba'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the players table."""
    op.create_table(
        "players",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
        ),
        sa.Column(
            "game_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "colour",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "display_name",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "access_token_hash",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "telegram_link_token",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "telegram_chat_id",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "telegram_connected_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "notifications_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "last_seen_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            name="fk_players_game_id_games",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "colour IN ('white', 'black')",
            name="ck_players_colour",
        ),
        sa.UniqueConstraint(
            "game_id",
            "colour",
            name="uq_players_game_colour",
        ),
        sa.UniqueConstraint(
            "access_token_hash",
            name="uq_players_access_token_hash",
        ),
        sa.UniqueConstraint(
            "telegram_link_token",
            name="uq_players_telegram_link_token",
        ),
    )

    op.create_index(
        "ix_players_game_id",
        "players",
        ["game_id"],
    )


def downgrade() -> None:
    """Remove the players table."""
    op.drop_index(
        "ix_players_game_id",
        table_name="players",
    )
    op.drop_table("players")
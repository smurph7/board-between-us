"""create games table

Revision ID: abcbabd3cfba
Revises: 2c01bda16784
Create Date: 2026-07-26 11:41:55.913789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'abcbabd3cfba'
down_revision: Union[str, Sequence[str], None] = '2c01bda16784'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Create the games table."""
    op.create_table(
        "games",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "board_state",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "current_turn",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "current_turn IN ('white', 'black')",
            name="ck_games_current_turn",
        ),
        sa.CheckConstraint(
            "status IN ('setup', 'active', 'finished')",
            name="ck_games_status",
        ),
        sa.CheckConstraint(
            "version >= 0",
            name="ck_games_version_non_negative",
        ),
    )


def downgrade() -> None:
    """Remove the games table."""
    op.drop_table("games")
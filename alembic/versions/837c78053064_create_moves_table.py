"""create moves table

Revision ID: 837c78053064
Revises: f17d603f0711
Create Date: 2026-07-26 11:49:05.335776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '837c78053064'
down_revision: Union[str, Sequence[str], None] = 'f17d603f0711'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the moves table."""
    op.create_table(
        "moves",
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
            "player_id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "sequence_number",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "move_type",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "piece",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "from_square",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "to_square",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "captured_piece",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "changes",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "board_state_before",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "board_state_after",
            postgresql.JSONB(),
            nullable=False,
        ),
        sa.Column(
            "previous_turn",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "resulting_turn",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "is_undone",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
            name="fk_moves_game_id_games",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["players.id"],
            name="fk_moves_player_id_players",
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "sequence_number > 0",
            name="ck_moves_sequence_number_positive",
        ),
        sa.CheckConstraint(
            """
            move_type IN (
                'move',
                'capture',
                'castle',
                'promotion',
                'undo',
                'correction',
                'game_started'
            )
            """,
            name="ck_moves_move_type",
        ),
        sa.CheckConstraint(
            "previous_turn IN ('white', 'black')",
            name="ck_moves_previous_turn",
        ),
        sa.CheckConstraint(
            "resulting_turn IN ('white', 'black')",
            name="ck_moves_resulting_turn",
        ),
        sa.UniqueConstraint(
            "game_id",
            "sequence_number",
            name="uq_moves_game_sequence_number",
        ),
    )

    op.create_index(
        "ix_moves_player_id",
        "moves",
        ["player_id"],
    )


def downgrade() -> None:
    """Remove the moves table."""
    op.drop_index(
        "ix_moves_player_id",
        table_name="moves",
    )
    op.drop_table("moves")
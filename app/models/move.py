from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text, false, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Move(Base):
    __tablename__ = "moves"

    id: Mapped[UUID] = mapped_column(primary_key=True)

    game_id: Mapped[UUID] = mapped_column(
        ForeignKey("games.id", ondelete="CASCADE"),
        nullable=False,
    )

    player_id: Mapped[UUID] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    move_type: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    piece: Mapped[str | None] = mapped_column(Text, nullable=True)
    from_square: Mapped[str | None] = mapped_column(Text, nullable=True)
    to_square: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_piece: Mapped[str | None] = mapped_column(Text, nullable=True)

    changes: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    board_state_before: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        nullable=False,
    )

    board_state_after: Mapped[dict[str, str]] = mapped_column(
        JSONB,
        nullable=False,
    )

    previous_turn: Mapped[str] = mapped_column(Text, nullable=False)
    resulting_turn: Mapped[str] = mapped_column(Text, nullable=False)

    is_undone: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=false(),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
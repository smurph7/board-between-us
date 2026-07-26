from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.player import Player
from app.services.game_service import (
    create_standard_game,
    load_player_game,
)
from app.services.token_service import hash_access_token


def test_create_standard_game_persists_game_and_players(
    db_session: Session,
) -> None:
    created = create_standard_game(
        db_session,
        name="Service test",
        white_display_name="Sarah",
        black_display_name="Daniel",
    )

    players = list(
        db_session.scalars(
            select(Player).where(
                Player.game_id == created.game.id,
            )
        )
    )
    players_by_colour = {
        player.colour: player
        for player in players
    }

    assert created.game.name == "Service test"
    assert created.game.current_turn == "white"
    assert created.game.status == "active"
    assert created.game.version == 0
    assert len(created.game.board_state) == 32

    assert set(players_by_colour) == {"white", "black"}
    assert players_by_colour["white"].display_name == "Sarah"
    assert players_by_colour["black"].display_name == "Daniel"

    assert created.white_access_token != created.black_access_token

    assert (
        players_by_colour["white"].access_token_hash
        == hash_access_token(created.white_access_token)
    )
    assert (
        players_by_colour["black"].access_token_hash
        == hash_access_token(created.black_access_token)
    )

    assert (
        players_by_colour["white"].access_token_hash
        != created.white_access_token
    )
    assert (
        players_by_colour["black"].access_token_hash
        != created.black_access_token
    )


def test_valid_token_loads_correct_player(
    db_session: Session,
) -> None:
    created = create_standard_game(
        db_session,
        white_display_name="Sarah",
        black_display_name="Daniel",
    )

    result = load_player_game(
        db_session,
        game_id=created.game.id,
        access_token=created.white_access_token,
    )

    assert result is not None
    assert result.game.id == created.game.id
    assert result.player.id == created.white_player.id
    assert result.player.colour == "white"


def test_invalid_token_returns_none(
    db_session: Session,
) -> None:
    created = create_standard_game(db_session)

    result = load_player_game(
        db_session,
        game_id=created.game.id,
        access_token="not-a-real-token",
    )

    assert result is None


def test_token_cannot_be_used_for_another_game(
    db_session: Session,
) -> None:
    first_game = create_standard_game(db_session)
    second_game = create_standard_game(db_session)

    result = load_player_game(
        db_session,
        game_id=second_game.game.id,
        access_token=first_game.white_access_token,
    )

    assert result is None
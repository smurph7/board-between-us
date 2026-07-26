from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.player import Player
from app.services.game_service import (
    create_standard_game,
    create_game_for_players,
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
    
def access_token_from_url(url: str) -> str:
    """Extract the raw access token from a private player URL."""
    return url.rsplit("/", maxsplit=1)[-1]


def test_create_game_for_white_creator_assigns_correct_links(db_session: Session) -> None:
    result = create_game_for_players(
        db_session,
        name="Sunday game",
        creator_display_name="Sarah",
        opponent_display_name="Daniel",
        creator_colour="white",
        app_base_url="https://example.test/",
    )

    players = db_session.scalars(
        select(Player).where(Player.game_id == result.game.id)
    ).all()
    players_by_colour = {player.colour: player for player in players}

    creator_token = access_token_from_url(result.creator_url)
    opponent_token = access_token_from_url(result.opponent_url)

    assert result.creator_colour == "white"
    assert result.game.name == "Sunday game"

    assert players_by_colour["white"].display_name == "Sarah"
    assert players_by_colour["black"].display_name == "Daniel"

    assert hash_access_token(creator_token) == players_by_colour["white"].access_token_hash
    assert hash_access_token(opponent_token) == players_by_colour["black"].access_token_hash

    assert result.creator_url.startswith(
        f"https://example.test/play/{result.game.id}/"
    )


def test_create_game_for_black_creator_assigns_correct_links(db_session: Session) -> None:
    result = create_game_for_players(
        db_session,
        name="Sunday game",
        creator_display_name="Sarah",
        opponent_display_name="Daniel",
        creator_colour="black",
        app_base_url="https://example.test/",
    )

    players = db_session.scalars(
        select(Player).where(Player.game_id == result.game.id)
    ).all()
    players_by_colour = {player.colour: player for player in players}

    creator_token = access_token_from_url(result.creator_url)
    opponent_token = access_token_from_url(result.opponent_url)

    assert result.creator_colour == "black"
    assert result.game.name == "Sunday game"

    assert players_by_colour["black"].display_name == "Sarah"
    assert players_by_colour["white"].display_name == "Daniel"

    assert hash_access_token(creator_token) == players_by_colour["black"].access_token_hash
    assert hash_access_token(opponent_token) == players_by_colour["white"].access_token_hash

    assert result.creator_url.startswith(
        f"https://example.test/play/{result.game.id}/"
    )
import pytest

from app.utils.game_sync import game_version_changed

@pytest.mark.parametrize(
    ("rendered_version", "database_version", "expected"),
    [
        (3, 3, False),
        (3, 4, True),
        (4, 3, True),
    ],
)
def test_game_version_changed(
    rendered_version: int,
    database_version: int,
    expected: bool,
) -> None:
    assert game_version_changed(rendered_version, database_version) is expected

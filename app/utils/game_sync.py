def game_version_changed(
    rendered_version: int,
    database_version: int,
) -> bool:
    """Return whether the rendered game differs from canonical database state."""
    return rendered_version != database_version
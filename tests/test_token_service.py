from app.services.token_service import generate_access_token, hash_access_token


def test_generated_access_tokens_are_unique() -> None:
    first_token = generate_access_token()
    second_token = generate_access_token()

    assert first_token != second_token
    assert len(first_token) >= 40
    assert len(second_token) >= 40


def test_access_token_hash_is_deterministic() -> None:
    token = generate_access_token()

    assert hash_access_token(token) == hash_access_token(token)


def test_access_token_hash_does_not_contain_raw_token() -> None:
    token = generate_access_token()
    token_hash = hash_access_token(token)

    assert token_hash != token
    assert token not in token_hash


def test_access_token_hash_is_sha256_hexadecimal() -> None:
    token_hash = hash_access_token("example-token")

    assert len(token_hash) == 64
    assert set(token_hash) <= set("0123456789abcdef")
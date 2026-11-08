import pytest

from app.services.game_store import game_store


@pytest.fixture(autouse=True)
def reset_game_store():
    """Empty the process-wide game store before and after every test."""
    game_store.clear()
    yield
    game_store.clear()

import pytest

from apps.puzzles import registry


@pytest.fixture
def clean_registry():
    """Run a test with an empty game registry and restore the real one afterwards."""
    saved = dict(registry._games)
    registry._games.clear()
    yield registry
    registry._games.clear()
    registry._games.update(saved)

from pathlib import Path

import pytest


@pytest.fixture
def repo() -> Path:
    """Path to the repo root."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def db_path(tmp_path) -> Path:
    """Isolated test database."""
    return tmp_path / "test.db"

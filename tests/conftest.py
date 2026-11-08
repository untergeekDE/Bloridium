from pathlib import Path

import pytest


@pytest.fixture
def repo() -> Path:
    """Pfad zum Repo-Root."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture
def db_path(tmp_path) -> Path:
    """Isolierte Test-Datenbank."""
    return tmp_path / "test.db"

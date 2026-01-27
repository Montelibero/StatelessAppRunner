import sys
import os
import pytest
from pathlib import Path

# Add app directory to path so tests can import from app modules
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

import db
from main import DEFAULT_SECRET

@pytest.fixture(autouse=True)
def test_db(monkeypatch, tmp_path):
    """
    Global fixture to set up a temporary database for ALL tests.
    """
    # Create a temp file path
    d = tmp_path / "data"
    d.mkdir()
    db_file = d / "test.db"

    # Monkeypatch the DB_PATH in the db module
    monkeypatch.setattr(db, "DB_PATH", str(db_file))

    # Initialize the DB and Sync Key
    db.init_db()
    db.sync_admin_key(DEFAULT_SECRET)

    yield

import pytest
import sys
from pathlib import Path

# Add app directory to path
app_dir = Path(__file__).parent.parent / "app"
sys.path.insert(0, str(app_dir))

import db

@pytest.fixture
def isolated_db(monkeypatch, tmp_path):
    """
    Setup a temporary database for the test.
    """
    d = tmp_path / "data"
    d.mkdir()
    db_file = d / "test_db.db"

    # Monkeypatch the DB_PATH in the db module
    monkeypatch.setattr(db, "DB_PATH", str(db_file))

    # Initialize the DB
    db.init_db()

    return db_file

def test_create_user_success(isolated_db):
    key = "test-key-new"
    comment = "New User"
    user_id = db.create_user(key, comment)
    assert user_id is not None

    user = db.get_user_by_key(key)
    assert user is not None
    assert user["key"] == key
    assert user["comment"] == comment

def test_create_user_duplicate(isolated_db):
    key = "duplicate-key"
    db.create_user(key, "Original")

    with pytest.raises(ValueError, match="Key already exists"):
        db.create_user(key, "Duplicate")

"""
Shared pytest fixtures for all test modules.
Uses a temp SQLite DB so tests never touch the real database.
"""
import os
import sys
import tempfile
import pytest

# Make backend importable without installing it as a package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


@pytest.fixture
def temp_db(monkeypatch, tmp_path):
    """
    Point database_service at a fresh temp DB for the duration of a test.
    Runs init_database() so all tables + migrations are applied.
    """
    db_path = str(tmp_path / 'test.db')

    import services.database_service as db_svc
    monkeypatch.setattr(db_svc, 'DB_PATH', db_path)

    db_svc.init_database()
    return db_path


@pytest.fixture
def flask_client(temp_db, monkeypatch):
    """
    Flask test client wired to the temp DB.
    Mocks out vector_service so no ChromaDB is needed.
    """
    import services.vector_service as vec_svc
    monkeypatch.setattr(vec_svc, 'add_sent_email', lambda **kwargs: None)
    monkeypatch.setattr(vec_svc, 'get_collection_count', lambda: 0)
    monkeypatch.setattr(vec_svc, 'clear_collection', lambda: None)

    import app as flask_app
    flask_app.app.config['TESTING'] = True
    with flask_app.app.test_client() as client:
        yield client

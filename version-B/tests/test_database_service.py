"""
Tests for database_service.py.
All tests use the temp_db fixture from conftest — no real DB is touched.
"""
import pytest


def test_init_creates_tables(temp_db):
    import sqlite3
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    conn.close()
    assert {'emails', 'responses', 'user_preferences', 'user_config'}.issubset(tables)


def test_store_and_retrieve_email(temp_db):
    from services.database_service import store_email, get_email_by_response_id, store_response

    email_id = store_email('sender@example.com', 'Sender Name', 'Test Subject', 'Test body')
    assert isinstance(email_id, int)
    assert email_id > 0

    response_id = store_response(email_id, 'Generated reply', 'test-model', 500)
    result = get_email_by_response_id(response_id)
    assert result['subject'] == 'Test Subject'
    assert result['sender_email'] == 'sender@example.com'
    assert result['generated_response'] == 'Generated reply'


def test_store_feedback(temp_db):
    from services.database_service import store_email, store_response, store_feedback, get_email_by_response_id

    email_id = store_email('a@example.com', 'A', 'Subj', 'Body')
    response_id = store_response(email_id, 'Draft reply', 'model', 300)
    store_feedback(response_id, 'Edited reply', True, 4, 'Minor edits')

    import sqlite3
    conn = sqlite3.connect(temp_db)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM responses WHERE id = ?', (response_id,))
    row = cursor.fetchone()
    conn.close()

    assert row['final_response'] == 'Edited reply'
    assert row['was_edited'] == 1
    assert row['user_rating'] == 4


def test_get_stats_empty(temp_db):
    from services import database_service as db_svc
    from unittest.mock import patch

    with patch('services.vector_service.get_collection_count', return_value=0):
        stats = db_svc.get_stats()

    assert stats['total_generated'] == 0
    assert stats['avg_rating'] == 0
    assert stats['edit_rate'] == 0


def test_get_stats_with_data(temp_db):
    from services.database_service import store_email, store_response, store_feedback
    from services import database_service as db_svc
    from unittest.mock import patch

    email_id = store_email('b@example.com', 'B', 'S', 'Body')
    r1 = store_response(email_id, 'Reply 1', 'model', 200)
    r2 = store_response(email_id, 'Reply 2', 'model', 200)
    store_feedback(r1, 'Reply 1', False, 5, '')
    store_feedback(r2, 'Edited reply', True, 3, 'tweaked')

    with patch('services.vector_service.get_collection_count', return_value=10):
        stats = db_svc.get_stats()

    assert stats['total_generated'] == 2
    assert stats['avg_rating'] == 4.0
    assert stats['edit_rate'] == 0.5


def test_save_and_get_user_config(temp_db):
    from services.database_service import save_user_config, get_user_config

    save_user_config('Jane Doe', 'Manager', 'Regards, Jane', True, 'SharedBox', False, 'gemini')
    config = get_user_config()

    assert config['full_name'] == 'Jane Doe'
    assert config['role'] == 'Manager'
    assert config['ai_provider'] == 'gemini'


def test_save_user_config_upsert(temp_db):
    from services.database_service import save_user_config, get_user_config

    save_user_config('First Name', 'Role A', '', True, '', False, 'ollama')
    save_user_config('Updated Name', 'Role B', '', True, '', False, 'gemini')
    config = get_user_config()

    assert config['full_name'] == 'Updated Name'
    assert config['ai_provider'] == 'gemini'


def test_save_and_get_preferences(temp_db):
    from services.database_service import save_user_preferences, get_user_preferences

    save_user_preferences(['Use formal tone', 'Always sign off with full name'])
    prefs = get_user_preferences()

    assert 'Use formal tone' in prefs
    assert 'Always sign off with full name' in prefs


def test_preferences_deduplication(temp_db):
    from services.database_service import save_user_preferences, get_user_preferences

    save_user_preferences(['Keep it brief'])
    save_user_preferences(['Keep it brief'])
    prefs = get_user_preferences()

    assert prefs.count('Keep it brief') == 1


def test_soft_delete_preference(temp_db):
    from services.database_service import save_user_preferences, get_all_preferences, delete_preference, get_user_preferences

    save_user_preferences(['Pref to delete'])
    prefs = get_all_preferences()
    pref_id = prefs[0]['id']

    result = delete_preference(pref_id)
    assert result is True

    active = get_user_preferences()
    assert 'Pref to delete' not in active


def test_get_deleted_preferences(temp_db):
    from services.database_service import save_user_preferences, get_all_preferences, delete_preference, get_deleted_preferences

    save_user_preferences(['Will be deleted'])
    pref_id = get_all_preferences()[0]['id']
    delete_preference(pref_id)

    deleted = get_deleted_preferences()
    assert any(p['note'] == 'Will be deleted' for p in deleted)


def test_restore_preference(temp_db):
    from services.database_service import save_user_preferences, get_all_preferences, delete_preference, restore_preference, get_user_preferences

    save_user_preferences(['Restore me'])
    pref_id = get_all_preferences()[0]['id']
    delete_preference(pref_id)
    restore_preference(pref_id)

    active = get_user_preferences()
    assert 'Restore me' in active


def test_delete_nonexistent_preference(temp_db):
    from services.database_service import delete_preference

    result = delete_preference(9999)
    assert result is False


def test_get_email_by_response_id_missing(temp_db):
    from services.database_service import get_email_by_response_id

    result = get_email_by_response_id(9999)
    assert result is None

"""
Tests for Flask routes in app.py.
Uses flask_client fixture from conftest — real DB (temp), mocked AI + ChromaDB.
"""
import json
from unittest.mock import patch


def test_health_check(flask_client):
    res = flask_client.get('/api/health')
    assert res.status_code == 200
    data = res.get_json()
    assert data['status'] == 'ok'


def test_get_user_config_empty(flask_client):
    res = flask_client.get('/api/user-config')
    assert res.status_code == 200
    assert res.get_json() == {}


def test_save_and_get_user_config(flask_client):
    payload = {
        'full_name': 'Test User',
        'role': 'Analyst',
        'signature': 'Regards',
        'use_signature': True,
        'shared_mailbox_name': '',
        'auto_generate': False,
        'ai_provider': 'gemini'
    }
    res = flask_client.post('/api/user-config', json=payload)
    assert res.status_code == 200
    assert res.get_json()['success'] is True

    res2 = flask_client.get('/api/user-config')
    config = res2.get_json()
    assert config['full_name'] == 'Test User'
    assert config['ai_provider'] == 'gemini'


def test_generate_response(flask_client):
    mock_result = {
        'generated_response': 'Hello, here is your reply.',
        'model': 'test-model',
        'generation_time_ms': 100,
        'similar_emails_used': 0
    }
    with patch('services.ai_service.generate_email_response', return_value=mock_result):
        res = flask_client.post('/api/generate', json={
            'subject': 'Test subject',
            'sender_name': 'John',
            'sender_email': 'john@example.com',
            'body': 'Can you help?',
            'extra_instructions': '',
            'style': 'standard'
        })

    assert res.status_code == 200
    data = res.get_json()
    assert data['generated_response'] == 'Hello, here is your reply.'
    assert 'response_id' in data


def test_generate_response_provider_error(flask_client):
    with patch('services.ai_service.generate_email_response', side_effect=Exception('connection failed')):
        res = flask_client.post('/api/generate', json={
            'subject': 'S', 'sender_name': 'N', 'sender_email': 'e@x.com', 'body': 'B'
        })

    assert res.status_code == 500
    data = res.get_json()
    assert 'error' in data
    assert data['error_type'] == 'provider_unavailable'


def test_feedback_stored(flask_client):
    mock_result = {
        'generated_response': 'Draft reply',
        'model': 'model',
        'generation_time_ms': 50,
        'similar_emails_used': 0
    }
    with patch('services.ai_service.generate_email_response', return_value=mock_result):
        gen_res = flask_client.post('/api/generate', json={
            'subject': 'S', 'sender_name': 'N', 'sender_email': 'e@x.com', 'body': 'B'
        })
    response_id = gen_res.get_json()['response_id']

    res = flask_client.post('/api/feedback', json={
        'response_id': response_id,
        'final_response': 'Edited reply',
        'was_edited': True,
        'user_rating': 4,
        'edit_notes': 'small change',
        'annotations': [],
        'learning_enabled': False
    })
    assert res.status_code == 200
    assert res.get_json()['success'] is True


def test_feedback_with_annotations(flask_client):
    mock_result = {
        'generated_response': 'Reply',
        'model': 'model',
        'generation_time_ms': 50,
        'similar_emails_used': 0
    }
    with patch('services.ai_service.generate_email_response', return_value=mock_result):
        gen_res = flask_client.post('/api/generate', json={
            'subject': 'S', 'sender_name': 'N', 'sender_email': 'e@x.com', 'body': 'B'
        })
    response_id = gen_res.get_json()['response_id']

    res = flask_client.post('/api/feedback', json={
        'response_id': response_id,
        'final_response': 'Reply',
        'was_edited': False,
        'user_rating': None,
        'edit_notes': '',
        'annotations': ['Always be concise'],
        'learning_enabled': True
    })
    assert res.status_code == 200

    prefs_res = flask_client.get('/api/preferences')
    notes = [p['note'] for p in prefs_res.get_json()]
    assert 'Always be concise' in notes


def test_get_stats(flask_client):
    res = flask_client.get('/api/stats')
    assert res.status_code == 200
    data = res.get_json()
    assert 'total_generated' in data
    assert 'avg_rating' in data


def test_get_preferences_empty(flask_client):
    res = flask_client.get('/api/preferences')
    assert res.status_code == 200
    assert res.get_json() == []


def test_delete_and_restore_preference(flask_client):
    from services.database_service import save_user_preferences, get_all_preferences
    save_user_preferences(['Route pref test'])
    pref_id = get_all_preferences()[0]['id']

    del_res = flask_client.delete(f'/api/preferences/{pref_id}')
    assert del_res.status_code == 200
    assert del_res.get_json()['success'] is True

    deleted_res = flask_client.get('/api/preferences/deleted')
    assert any(p['note'] == 'Route pref test' for p in deleted_res.get_json())

    restore_res = flask_client.post(f'/api/preferences/{pref_id}/restore')
    assert restore_res.status_code == 200
    assert restore_res.get_json()['success'] is True


def test_delete_nonexistent_preference(flask_client):
    res = flask_client.delete('/api/preferences/9999')
    assert res.status_code == 404


def test_learning_stats(flask_client):
    res = flask_client.get('/api/learning-stats')
    assert res.status_code == 200
    data = res.get_json()
    assert 'daily' in data


def test_clear_knowledge_base(flask_client):
    res = flask_client.post('/api/clear-knowledge-base')
    assert res.status_code == 200
    assert res.get_json()['success'] is True

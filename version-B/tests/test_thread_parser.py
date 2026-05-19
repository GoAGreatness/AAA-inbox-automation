"""
Tests for thread_parser.parse_thread().
No fixtures needed — pure function with no side effects.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.thread_parser import parse_thread


def test_empty_body():
    result = parse_thread('')
    assert result == {'reply_body': '', 'original_body': ''}


def test_none_body():
    result = parse_thread(None)
    assert result == {'reply_body': '', 'original_body': ''}


def test_no_quote_marker():
    body = "Thanks for reaching out. I'll get back to you soon."
    result = parse_thread(body)
    assert result['reply_body'] == body.strip()
    assert result['original_body'] == ''


def test_outlook_from_separator():
    body = "Sure, happy to help.\n\nFrom: John Doe <john@example.com>\nSubject: Original"
    result = parse_thread(body)
    assert 'Sure, happy to help.' in result['reply_body']
    assert 'john@example.com' in result['original_body']


def test_wrote_separator():
    body = "Got it, thanks.\n\nOn Mon, 1 Jan 2026 at 10:00, Jane <jane@example.com> wrote:\n> Original message here"
    result = parse_thread(body)
    assert result['reply_body'] == 'Got it, thanks.'
    assert 'Original message here' in result['original_body']


def test_dash_separator():
    body = "My reply here.\n\n-----Original Message-----\nOriginal content"
    result = parse_thread(body)
    assert result['reply_body'] == 'My reply here.'
    assert 'Original content' in result['original_body']


def test_underscore_separator():
    body = "Reply text.\n\n_____\nOriginal below"
    result = parse_thread(body)
    assert result['reply_body'] == 'Reply text.'
    assert result['original_body'] != ''


def test_reply_stripped_of_whitespace():
    body = "   My reply.   \n\nFrom: someone@example.com\nOriginal"
    result = parse_thread(body)
    assert result['reply_body'] == 'My reply.'

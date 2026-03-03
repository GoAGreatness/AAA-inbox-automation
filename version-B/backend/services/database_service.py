"""
Database Service - Handles all SQLite operations for storing emails,
responses, and feedback.

Uses the Repository Pattern - separates database logic from business logic,
so if we ever switch databases, only this file changes.
"""
import sqlite3
import os
from datetime import datetime

# Database file path
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'database.db')


def get_connection():
    """Create and return a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Returns rows as dictionaries
    return conn


def init_database():
    """
    Initialize database tables if they don't exist.
    Called once when the backend starts.
    This is a Migration - setting up or updating database structure.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Emails table - stores incoming emails we've generated responses for
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_email TEXT,
            sender_name TEXT,
            subject TEXT,
            body TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Responses table - stores AI-generated and final (edited) responses
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email_id INTEGER,
            generated_response TEXT,
            final_response TEXT,
            was_edited BOOLEAN DEFAULT 0,
            user_rating INTEGER,
            edit_notes TEXT,
            model_used TEXT,
            generation_time_ms INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (email_id) REFERENCES emails(id)
        )
    ''')

    # Sent emails table - stores historical sent replies for RAG context
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sent_emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_email TEXT,
            sender_name TEXT,
            subject TEXT,
            original_body TEXT,
            reply_body TEXT,
            imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Templates table - common response patterns
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            template_text TEXT,
            usage_count INTEGER DEFAULT 0
        )
    ''')

    # User preferences table - stores annotations extracted from edited responses
    # e.g. [[always apologize for late replies]] → stored as a preference note
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            note TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # User config table - stores user identity for AI context
    # Single row (id=1) updated in place
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_config (
            id INTEGER PRIMARY KEY DEFAULT 1,
            full_name TEXT,
            role TEXT,
            signature TEXT,
            use_signature BOOLEAN DEFAULT 1,
            shared_mailbox_name TEXT,
            auto_generate BOOLEAN DEFAULT 0,
            configured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully!")


def store_email(sender_email, sender_name, subject, body):
    """Store an incoming email. Returns the email ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO emails (sender_email, sender_name, subject, body) VALUES (?, ?, ?, ?)',
        (sender_email, sender_name, subject, body)
    )

    email_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return email_id


def store_response(email_id, generated_response, model_used, generation_time_ms):
    """Store a generated response. Returns the response ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO responses (email_id, generated_response, model_used, generation_time_ms) VALUES (?, ?, ?, ?)',
        (email_id, generated_response, model_used, generation_time_ms)
    )

    response_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return response_id


def store_feedback(response_id, final_response, was_edited, user_rating, edit_notes):
    """Update a response with user feedback."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'UPDATE responses SET final_response=?, was_edited=?, user_rating=?, edit_notes=? WHERE id=?',
        (final_response, was_edited, user_rating, edit_notes, response_id)
    )

    conn.commit()
    conn.close()


def store_sent_email(sender_email, sender_name, subject, original_body, reply_body):
    """Store a historical sent email for RAG context. Returns the email ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'INSERT INTO sent_emails (sender_email, sender_name, subject, original_body, reply_body) VALUES (?, ?, ?, ?, ?)',
        (sender_email, sender_name, subject, original_body, reply_body)
    )

    email_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return email_id


def get_email_by_response_id(response_id):
    """Get the original email linked to a response. Used for auto-learning."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT e.* FROM emails e JOIN responses r ON e.id = r.email_id WHERE r.id = ?',
        (response_id,)
    )

    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def get_stats():
    """Get usage statistics from the database."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) as total FROM responses')
    total = cursor.fetchone()['total']

    cursor.execute('SELECT AVG(user_rating) as avg FROM responses WHERE user_rating IS NOT NULL')
    avg_rating = cursor.fetchone()['avg'] or 0

    cursor.execute('SELECT COUNT(*) as edited FROM responses WHERE was_edited = 1')
    edited = cursor.fetchone()['edited']

    edit_rate = edited / total if total > 0 else 0

    cursor.execute('SELECT COUNT(*) as sent FROM sent_emails')
    sent_count = cursor.fetchone()['sent']

    conn.close()

    return {
        'total_generated': total,
        'avg_rating': round(avg_rating, 1),
        'edit_rate': round(edit_rate, 2),
        'historical_emails': sent_count
    }


def get_user_config():
    """Get saved user config. Returns None if not yet configured."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM user_config WHERE id = 1')
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_user_config(full_name, role, signature, use_signature, shared_mailbox_name='', auto_generate=False):
    """Save or update user config (upsert - insert or replace)."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_config (id, full_name, role, signature, use_signature, shared_mailbox_name, auto_generate, configured_at)
        VALUES (1, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            full_name=excluded.full_name,
            role=excluded.role,
            signature=excluded.signature,
            use_signature=excluded.use_signature,
            shared_mailbox_name=excluded.shared_mailbox_name,
            auto_generate=excluded.auto_generate,
            configured_at=excluded.configured_at
    ''', (full_name, role, signature, use_signature, shared_mailbox_name, auto_generate))
    conn.commit()
    conn.close()


def save_user_preferences(notes):
    """Save a list of annotation notes. Ignores duplicates (UNIQUE constraint)."""
    conn = get_connection()
    cursor = conn.cursor()
    for note in notes:
        note = note.strip()
        if note:
            cursor.execute(
                'INSERT OR IGNORE INTO user_preferences (note) VALUES (?)', (note,)
            )
    conn.commit()
    conn.close()


def get_user_preferences():
    """Get all stored user preference notes."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT note FROM user_preferences ORDER BY created_at ASC')
    rows = cursor.fetchall()
    conn.close()
    return [row['note'] for row in rows]


def get_sent_emails(limit=50):
    """Get historical sent emails for RAG context."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        'SELECT * FROM sent_emails ORDER BY imported_at DESC LIMIT ?',
        (limit,)
    )

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

"""
Email Import Script - Parses .msg files and loads them into
SQLite database and ChromaDB vector store for RAG.

Run from version-B directory:
    python scripts/import_emails.py
"""
import os
import sys
import extract_msg

# Add backend to path so we can import services
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.database_service import init_database, store_sent_email
from services.vector_service import add_sent_email, get_collection_count
from services.thread_parser import parse_thread

# Path to imported emails
IMPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'email-imports')


def parse_msg_file(filepath):
    """Parse a single .msg file and extract email data."""
    try:
        msg = extract_msg.Message(filepath)

        data = {
            'sender_email': msg.to or '',
            'sender_name': msg.sender or '',
            'subject': msg.subject or '',
            'body': msg.body or '',
        }

        msg.close()
        return data

    except Exception as e:
        print(f"  ERROR parsing {os.path.basename(filepath)}: {e}")
        return None


def import_all_emails():
    """Import all .msg files from the email-imports folder."""
    # Initialize database
    init_database()

    # Check for .msg files
    msg_files = [f for f in os.listdir(IMPORT_PATH) if f.endswith('.msg')]

    if not msg_files:
        print("No .msg files found in email-imports folder.")
        return

    print(f"Found {len(msg_files)} .msg files to import.")
    print(f"Current vector store count: {get_collection_count()}")
    print("-" * 50)

    success = 0
    skipped = 0
    failed = 0

    for i, filename in enumerate(msg_files, 1):
        filepath = os.path.join(IMPORT_PATH, filename)
        print(f"[{i}/{len(msg_files)}] Processing: {filename[:60]}...")

        data = parse_msg_file(filepath)

        if not data:
            failed += 1
            continue

        if not data['body'].strip():
            print(f"  SKIPPED - empty body")
            skipped += 1
            continue

        # Parse thread to separate reply from quoted original
        parsed = parse_thread(data['body'])

        # Store in SQLite
        email_id = store_sent_email(
            sender_email=data['sender_email'],
            sender_name=data['sender_name'],
            subject=data['subject'],
            original_body=parsed['original_body'],
            reply_body=parsed['reply_body']
        )

        # Store in ChromaDB for semantic search
        add_sent_email(
            email_id=email_id,
            subject=data['subject'],
            original_body=parsed['original_body'],
            reply_body=parsed['reply_body']
        )

        success += 1

    print("-" * 50)
    print(f"Import complete!")
    print(f"  Imported: {success}")
    print(f"  Skipped:  {skipped}")
    print(f"  Failed:   {failed}")
    print(f"  Vector store total: {get_collection_count()}")


if __name__ == '__main__':
    import_all_emails()

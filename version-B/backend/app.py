"""
Main Flask application for email response generation backend.
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize database on startup
from services.database_service import init_database, store_email, store_response, store_feedback as db_store_feedback, get_stats as db_get_stats, get_email_by_response_id, get_user_config, save_user_config
from services.vector_service import add_sent_email, get_collection_count
init_database()

# Configure CORS - allow all origins for development
# Outlook add-in runs in embedded browser with different origin
CORS(app, origins="*", supports_credentials=False)

# Configuration
app.config['DEBUG'] = os.getenv('DEBUG', 'True') == 'True'


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'ok',
        'message': 'Backend is running',
        'ai_provider': os.getenv('AI_PROVIDER', 'ollama')
    })


@app.route('/api/generate', methods=['POST'])
def generate_response():
    """Generate AI response for an email."""
    data = request.get_json()

    # Extract email data
    subject = data.get('subject', '')
    sender_email = data.get('sender_email', '')
    sender_name = data.get('sender_name', '')
    body = data.get('body', '')

    try:
        from services.ai_service import generate_email_response

        # Store the incoming email in database
        email_id = store_email(sender_email, sender_name, subject, body)

        user_config = get_user_config()
        result = generate_email_response(subject, sender_name, sender_email, body, user_config)

        # Store the generated response in database
        response_id = store_response(email_id, result['generated_response'], result['model'], result['generation_time_ms'])

        response = {
            'response_id': response_id,
            'generated_response': result['generated_response'],
            'model': result['model'],
            'generation_time_ms': result['generation_time_ms'],
            'similar_emails_used': result.get('similar_emails_used', 0)
        }
    except Exception as e:
        # Fallback if Ollama is not running
        response = {
            'response_id': 'fallback',
            'generated_response': f"[Ollama unavailable: {str(e)}]\n\nDear {sender_name},\n\nThank you for your email about '{subject}'.\n\nBest regards,\nThe Team",
            'generation_time_ms': 0,
            'error': str(e)
        }

    return jsonify(response)


@app.route('/api/feedback', methods=['POST'])
def store_feedback():
    """
    Store feedback and auto-learn from approved responses.
    This is the Feedback Loop - approved responses get added to the
    vector store so future generations learn from them.
    """
    data = request.get_json()

    response_id = data.get('response_id')
    final_response = data.get('final_response', '')
    was_edited = data.get('was_edited', False)
    user_rating = data.get('user_rating')
    edit_notes = data.get('edit_notes', '')

    # Store feedback in database
    db_store_feedback(response_id, final_response, was_edited, user_rating, edit_notes)

    # Auto-learn: add approved response to vector store
    # This means future queries will find this response as a similar example
    try:
        email_data = get_email_by_response_id(response_id)
        if email_data and final_response:
            vector_id = f"approved-{response_id}"
            add_sent_email(
                email_id=vector_id,
                subject=email_data['subject'],
                original_body=email_data['body'],
                reply_body=final_response
            )
    except Exception as e:
        print(f"Auto-learn error (non-blocking): {e}")

    return jsonify({
        'success': True,
        'message': 'Feedback stored and response added to knowledge base'
    })


@app.route('/api/user-config', methods=['GET'])
def get_config():
    """Get current user config. Used by webapp to check if setup is needed."""
    config = get_user_config()
    return jsonify(config if config else {})


@app.route('/api/user-config', methods=['POST'])
def save_config():
    """Save user config (name, role, signature)."""
    data = request.get_json()
    save_user_config(
        full_name=data.get('full_name', ''),
        role=data.get('role', ''),
        signature=data.get('signature', ''),
        use_signature=data.get('use_signature', True),
        shared_mailbox_name=data.get('shared_mailbox_name', ''),
        auto_generate=data.get('auto_generate', False)
    )
    return jsonify({'success': True, 'message': 'Configuration saved'})


@app.route('/api/import-sent', methods=['POST'])
def import_sent_emails():
    """
    Receives sent emails from VBA macro and indexes them in ChromaDB.
    Uses MD5 hash of subject+body as ID to prevent duplicate imports.
    """
    import hashlib
    data = request.get_json()
    emails = data.get('emails', [])

    imported = 0
    skipped = 0

    for i, email in enumerate(emails):
        subject = email.get('subject', '')
        body = email.get('body', '')

        if not body.strip():
            skipped += 1
            continue

        try:
            email_id = f"vba-{hashlib.md5((subject + body[:100]).encode()).hexdigest()[:12]}"
            add_sent_email(
                email_id=email_id,
                subject=subject,
                original_body='',
                reply_body=body
            )
            imported += 1
        except Exception as e:
            skipped += 1

    print(f"VBA import: {imported} imported, {skipped} skipped. Total: {get_collection_count()}")
    return jsonify({
        'success': True,
        'imported': imported,
        'skipped': skipped,
        'vector_store_total': get_collection_count()
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get usage statistics including learning progress."""
    stats = db_get_stats()
    stats['vector_store_count'] = get_collection_count()
    return jsonify(stats)


if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))

    # SSL certificate paths
    ssl_cert = os.path.join('backend', 'data', 'ssl', 'cert.pem')
    ssl_key = os.path.join('backend', 'data', 'ssl', 'key.pem')

    print(f"Starting backend on https://localhost:{port}")
    print("Using self-signed SSL certificate")

    app.run(
        host='localhost',
        port=port,
        debug=app.config['DEBUG'],
        ssl_context=(ssl_cert, ssl_key)
    )

"""
Main Flask application for email response generation backend.
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import threading
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize database on startup
from services.database_service import init_database, store_email, store_response, store_feedback as db_store_feedback, get_stats as db_get_stats, get_email_by_response_id, get_user_config, save_user_config, save_user_preferences, get_user_preferences, get_all_preferences, delete_preference, get_deleted_preferences, restore_preference, get_learning_stats
from services.vector_service import add_sent_email, get_collection_count, clear_collection
from services.thread_parser import parse_thread
init_database()

# Configure CORS - allow all origins for development
# Outlook add-in runs in embedded browser with different origin
CORS(app, origins="*", supports_credentials=False)

# Configuration
app.config['DEBUG'] = os.getenv('DEBUG', 'True') == 'True'

# Webapp static files — served by Flask for deployment (serve.py used for local dev)
WEBAPP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'outlook-addin', 'src', 'webapp'))


@app.route('/')
def serve_index():
    return send_from_directory(WEBAPP_DIR, 'index.html')


@app.route('/dashboard')
def serve_dashboard():
    return send_from_directory(WEBAPP_DIR, 'dashboard.html')


@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(WEBAPP_DIR, filename)


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
    extra_instructions = data.get('extra_instructions', '')
    style = data.get('style', 'standard')

    user_config = get_user_config()
    user_preferences = get_user_preferences()

    try:
        from services.ai_service import generate_email_response

        # Store the incoming email in database
        email_id = store_email(sender_email, sender_name, subject, body)

        result = generate_email_response(subject, sender_name, sender_email, body, user_config, user_preferences,
                                         extra_instructions=extra_instructions, style=style)

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
        import requests as req_lib
        status_code = None
        if isinstance(e, req_lib.exceptions.HTTPError) and e.response is not None:
            status_code = e.response.status_code
        elif isinstance(e, req_lib.exceptions.Timeout):
            status_code = 408
        elif isinstance(e, req_lib.exceptions.ConnectionError):
            status_code = 503

        # Read provider from saved config, falling back to env var
        provider = (user_config.get('ai_provider') if user_config else None) or os.getenv('AI_PROVIDER', 'ollama')

        return jsonify({
            'error': str(e),
            'error_type': 'provider_unavailable',
            'status_code': status_code,
            'provider': provider
        }), 500

    return jsonify(response)


def _process_feedback_background(response_id, final_response, was_edited, user_rating, user_config):
    """
    Heavy feedback processing runs in a background thread so the Copy button
    returns instantly. Covers ChromaDB indexing + LLM edit diff analysis.
    Pattern: async fire-and-forget worker thread.
    """
    start = time.time()

    # --- ChromaDB indexing (rating gate) ---
    rated_well = user_rating is not None and user_rating >= 4
    implicit_approval = user_rating is None and not was_edited
    if rated_well or implicit_approval:
        try:
            t0 = time.time()
            email_data = get_email_by_response_id(response_id)
            if email_data and final_response:
                vector_id = f"approved-{response_id}"
                add_sent_email(
                    email_id=vector_id,
                    subject=email_data['subject'],
                    original_body=email_data['body'],
                    reply_body=final_response
                )
            print(f"[feedback] ChromaDB indexing: {int((time.time() - t0) * 1000)}ms")
        except Exception as e:
            print(f"[feedback] ChromaDB indexing error: {e}")

    # --- Edit diff analysis (LLM call) ---
    if was_edited and final_response:
        try:
            t0 = time.time()
            from services.ai_service import analyze_edit_diff
            email_data = get_email_by_response_id(response_id)
            generated_response = email_data.get('generated_response') if email_data else None
            learned = analyze_edit_diff(generated_response, final_response, user_config)
            if learned:
                save_user_preferences(learned)
            print(f"[feedback] Edit diff analysis: {int((time.time() - t0) * 1000)}ms — learned {len(learned) if learned else 0} preference(s)")
        except Exception as e:
            print(f"[feedback] Edit diff analysis error: {e}")

    print(f"[feedback] Total background processing: {int((time.time() - start) * 1000)}ms")


@app.route('/api/feedback', methods=['POST'])
def store_feedback():
    """
    Store feedback and kick off background processing.
    Fast DB writes happen synchronously; heavy work (ChromaDB + LLM) runs
    in a background thread so the response returns immediately.
    """
    data = request.get_json()

    response_id = data.get('response_id')
    final_response = data.get('final_response', '')
    was_edited = data.get('was_edited', False)
    user_rating = data.get('user_rating')
    edit_notes = data.get('edit_notes', '')
    annotations = data.get('annotations', [])
    learning_enabled = data.get('learning_enabled', True)

    # Store feedback in database (always — needed for stats regardless of learning toggle)
    db_store_feedback(response_id, final_response, was_edited, user_rating, edit_notes)

    # Save any [[annotation]] notes extracted by the frontend (always — user explicitly added these)
    if annotations:
        save_user_preferences(annotations)

    # All learning (edit diff + ChromaDB indexing) skipped if user toggled off
    if not learning_enabled:
        print(f"[feedback] Learning disabled by user — skipping edit diff + ChromaDB indexing")
        return jsonify({'success': True, 'message': 'Feedback stored'})

    # Edit diff analysis: if the user edited the response, ask the LLM what style patterns it can extract
    if was_edited and final_response:
        try:
            from services.ai_service import analyze_edit_diff
            email_data = get_email_by_response_id(response_id)
            generated_response = email_data.get('generated_response') if email_data else None
            user_config = get_user_config()
            learned = analyze_edit_diff(generated_response, final_response, user_config)
            if learned:
                save_user_preferences(learned)
                print(f"Edit diff analysis: learned {len(learned)} preference(s)")
        except Exception as e:
            print(f"Edit diff analysis error (non-blocking): {e}")

    # Auto-learn: add approved response to vector store only if quality threshold met.
    rated_well = user_rating is not None and user_rating >= 4
    implicit_approval = user_rating is None and not was_edited
    if rated_well or implicit_approval:
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

    return jsonify({'success': True, 'message': 'Feedback stored'})


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
        auto_generate=data.get('auto_generate', False),
        ai_provider=data.get('ai_provider', 'ollama')
    )
    return jsonify({'success': True, 'message': 'Configuration saved'})


@app.route('/api/import-sent', methods=['POST'])
def import_sent_emails():
    """
    Receives sent emails from VBA macro and indexes them in ChromaDB.
    Uses MD5 hash of subject+body as ID to prevent duplicate imports.
    """
    import hashlib
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON payload'}), 400
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
            parsed = parse_thread(body)
            email_id = f"vba-{hashlib.md5((subject + body[:100]).encode()).hexdigest()[:12]}"
            add_sent_email(
                email_id=email_id,
                subject=subject,
                original_body=parsed['original_body'],
                reply_body=parsed['reply_body']
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


@app.route('/api/preferences', methods=['GET'])
def get_preferences():
    """Get all stored user preferences with IDs for the dashboard."""
    prefs = get_all_preferences()
    return jsonify(prefs)


@app.route('/api/preferences/<int:preference_id>', methods=['DELETE'])
def remove_preference(preference_id):
    """Soft delete a single user preference by ID."""
    success = delete_preference(preference_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Preference not found'}), 404


@app.route('/api/preferences/deleted', methods=['GET'])
def get_deleted():
    """Get all soft-deleted preferences for the recycle bin."""
    prefs = get_deleted_preferences()
    return jsonify(prefs)


@app.route('/api/preferences/<int:preference_id>/restore', methods=['POST'])
def restore_pref(preference_id):
    """Restore a soft-deleted preference back to active."""
    success = restore_preference(preference_id)
    if success:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': 'Preference not found or not deleted'}), 404


@app.route('/api/learning-stats', methods=['GET'])
def learning_stats():
    """Get time-series stats for dashboard charts (rating trend, daily generation counts)."""
    stats = get_learning_stats()
    return jsonify(stats)


@app.route('/api/clear-knowledge-base', methods=['POST'])
def clear_knowledge_base():
    """Delete all indexed emails from ChromaDB. Irreversible."""
    try:
        clear_collection()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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

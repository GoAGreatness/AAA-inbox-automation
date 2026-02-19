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
from services.database_service import init_database, store_email, store_response, store_feedback as db_store_feedback, get_stats as db_get_stats
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

        result = generate_email_response(subject, sender_name, sender_email, body)

        # Store the generated response in database
        response_id = store_response(email_id, result['generated_response'], result['model'], result['generation_time_ms'])

        response = {
            'response_id': response_id,
            'generated_response': result['generated_response'],
            'model': result['model'],
            'generation_time_ms': result['generation_time_ms']
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
    """Store feedback on generated response."""
    data = request.get_json()

    response_id = data.get('response_id')
    final_response = data.get('final_response', '')
    was_edited = data.get('was_edited', False)
    user_rating = data.get('user_rating')
    edit_notes = data.get('edit_notes', '')

    db_store_feedback(response_id, final_response, was_edited, user_rating, edit_notes)

    return jsonify({
        'success': True,
        'message': 'Feedback stored'
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get usage statistics."""
    stats = db_get_stats()
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

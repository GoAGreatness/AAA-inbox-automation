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

# Configure CORS
cors_origins = os.getenv('CORS_ORIGINS', 'https://localhost:3000').split(',')
CORS(app, origins=cors_origins)

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

        result = generate_email_response(subject, sender_name, sender_email, body)

        response = {
            'response_id': f"gen-{int(__import__('time').time())}",
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

    # TODO: Implement feedback storage
    return jsonify({
        'success': True,
        'message': 'Feedback stored'
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get usage statistics."""
    # TODO: Implement stats from database
    return jsonify({
        'total_generated': 0,
        'avg_rating': 0,
        'edit_rate': 0
    })


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

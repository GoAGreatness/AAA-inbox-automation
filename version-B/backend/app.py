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

    # TODO: Implement AI generation
    # For now, return a mock response
    response = {
        'response_id': 'mock-123',
        'generated_response': f"Dear {sender_name},\n\nThank you for your email about '{subject}'.\n\n[AI-generated response will appear here]\n\nBest regards,\nThe Team",
        'confidence': 0.85,
        'generation_time_ms': 100
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

    # For now, run without HTTPS (we'll add SSL later)
    print(f"Starting backend on http://localhost:{port}")
    print("Note: Add-in will require HTTPS later")

    app.run(
        host='localhost',
        port=port,
        debug=app.config['DEBUG']
    )

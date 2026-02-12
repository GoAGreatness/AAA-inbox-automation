"""
AI Service - Handles communication with Ollama for response generation.
"""
import ollama
import time
import os


def generate_email_response(subject, sender_name, sender_email, body):
    """
    Send email data to Ollama and get an AI-generated response.
    Returns dict with generated response and metadata.
    """
    model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

    prompt = f"""You are a professional email assistant helping respond to emails for a shared inbox.

Write a professional, helpful response to this email:

From: {sender_name} <{sender_email}>
Subject: {subject}
Body: {body}

Instructions:
1. Address the sender by name
2. Be professional and helpful
3. Answer any questions in the email
4. Keep it concise (2-3 paragraphs)
5. End with a professional sign-off
6. Do NOT include a subject line, just the response body

Response:"""

    start_time = time.time()

    result = ollama.chat(
        model=model,
        messages=[{'role': 'user', 'content': prompt}]
    )

    generation_time = int((time.time() - start_time) * 1000)

    return {
        'generated_response': result['message']['content'],
        'model': model,
        'generation_time_ms': generation_time
    }

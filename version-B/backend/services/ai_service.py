"""
AI Service - Handles communication with Ollama for response generation.
Uses RAG (Retrieval Augmented Generation) to find similar past emails
and feed them as context to improve response quality.
"""
import ollama
import time
import os
from services.vector_service import find_similar_emails


def generate_email_response(subject, sender_name, sender_email, body):
    """
    Send email data to Ollama and get an AI-generated response.
    Searches for similar past emails to use as context.
    Returns dict with generated response and metadata.
    """
    model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

    # RAG: Find similar past emails for context
    similar = find_similar_emails(subject, body)
    context = _build_context(similar)

    prompt = f"""You are a professional email assistant helping respond to emails for a shared inbox.

{context}

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
7. If similar past responses are provided above, match their tone and style

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
        'generation_time_ms': generation_time,
        'similar_emails_used': len(similar)
    }


def _build_context(similar_emails):
    """Build RAG context string from similar past emails."""
    if not similar_emails:
        return "No similar past emails found. Generate a general professional response."

    context = f"Here are {len(similar_emails)} similar past emails and how they were replied to. Match this style:\n\n"

    for i, email in enumerate(similar_emails, 1):
        context += f"--- Past Example {i} ---\n"
        context += f"Subject: {email['subject']}\n"
        context += f"Reply sent: {email['reply']}\n\n"

    return context

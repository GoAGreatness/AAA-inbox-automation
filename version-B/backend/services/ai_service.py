"""
AI Service - Handles communication with Ollama for response generation.
Uses RAG (Retrieval Augmented Generation) to find similar past emails
and feed them as context to improve response quality.
"""
import ollama
import time
import os
from services.vector_service import find_similar_emails


def generate_email_response(subject, sender_name, sender_email, body, user_config=None, user_preferences=None):
    """
    Send email data to Ollama and get an AI-generated response.
    Searches for similar past emails to use as context.
    Uses user_config (name, role, signature) to personalise the response.
    Returns dict with generated response and metadata.
    """
    model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

    # RAG: Find similar past emails for context
    similar = find_similar_emails(subject, body)
    context = _build_context(similar)

    # Build user identity section from config
    if user_config and user_config.get('full_name'):
        user_name = user_config['full_name']
        identity = f"You are {user_name}, responding to this email on behalf of yourself."
    else:
        identity = "You are a professional staff member responding to this email."

    # Build signature instruction
    use_sig = user_config and user_config.get('use_signature')
    has_custom_sig = user_config and user_config.get('signature', '').strip()

    if use_sig and has_custom_sig:
        signature_instruction = f"8. End the email with EXACTLY this signature, do not modify it:\n{user_config['signature']}"
    elif use_sig and user_config and user_config.get('full_name'):
        sig = user_config['full_name']
        if user_config.get('role'):
            sig += f"\n{user_config['role']}"
        signature_instruction = f"8. Sign off as:\n{sig}"
    else:
        signature_instruction = "8. Do NOT include any signature or sign-off at the end"

    # Build user preferences section
    if user_preferences:
        prefs_text = "\n".join(f"- {p}" for p in user_preferences)
        preferences_section = f"\nUser style preferences (always follow these):\n{prefs_text}\n"
    else:
        preferences_section = ""

    prompt = f"""You are a professional email assistant. {identity}
{preferences_section}
{context}

Write a professional, helpful response to this email IN FIRST PERSON (as yourself, not as an assistant):

From: {sender_name} <{sender_email}>
Subject: {subject}
Body: {body}

Instructions:
1. Write as yourself in first person (use "I", not "we" unless appropriate)
2. Address the sender by name
3. Be professional and helpful
4. Answer any questions in the email
5. Keep it concise (2-3 paragraphs)
6. Do NOT include a subject line, just the response body
7. If similar past responses are provided above, match their tone and style
{signature_instruction}

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

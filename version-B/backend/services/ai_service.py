"""
AI Service - Handles communication with Ollama, GoA LLM cluster, or Google Gemini.
Uses RAG (Retrieval Augmented Generation) to find similar past emails
and feed them as context to improve response quality.
"""
import ollama
import requests
import time
import os
from services.vector_service import find_similar_emails


RAG_MIN = 5
RAG_MAX = 20


def _determine_rag_depth(subject, body, provider, user_config):
    """
    Ask the LLM how many similar past emails it needs to answer this email well.
    Returns an integer clamped between RAG_MIN and RAG_MAX.
    """
    prompt = f"""You are deciding how many similar past email examples you need to write a comprehensive reply.

Incoming email:
Subject: {subject}
Body: {body}

Consider: length, number of questions, topic complexity, and specificity.
Reply with ONLY a single integer between {RAG_MIN} and {RAG_MAX}. No explanation."""

    try:
        if provider == 'goa':
            raw, _ = _call_goa(prompt)
        elif provider == 'gemini':
            raw, _ = _call_gemini(prompt)
        else:
            raw, _ = _call_ollama(prompt)

        n = int(''.join(filter(str.isdigit, raw.strip().split()[0])))
        return max(RAG_MIN, min(RAG_MAX, n))
    except Exception:
        return 15  # fallback to default


STYLE_INSTRUCTIONS = {
    'standard':     'Write a balanced, professional response of 2-3 paragraphs.',
    'concise':      'Write a brief, direct response. One paragraph maximum. No fluff.',
    'detailed':     'Write a thorough response that addresses every point and question fully. Be comprehensive.',
    'step-by-step': 'Structure your response using numbered steps or bullet points where appropriate.'
}


def generate_email_response(subject, sender_name, sender_email, body, user_config=None, user_preferences=None,
                             extra_instructions='', style='standard'):
    """
    Generate an AI response using Ollama, GoA LLM cluster, or Google Gemini.
    Provider is determined by the AI_PROVIDER env variable or user config.
    """
    # Determine provider — user config takes priority over env var
    provider = os.getenv('AI_PROVIDER', 'gemini')
    if user_config and user_config.get('ai_provider'):
        provider = user_config['ai_provider']

    # RAG: Ask LLM how many similar emails it needs, then fetch that many
    rag_depth = _determine_rag_depth(subject, body, provider, user_config)
    similar = find_similar_emails(subject, body, n_results=rag_depth)
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

    # Writing style instruction
    style_instruction = STYLE_INSTRUCTIONS.get(style, STYLE_INSTRUCTIONS['standard'])

    # Extra user instructions
    extra_section = f"\nAdditional instructions from user: {extra_instructions}" if extra_instructions else ""

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
5. {style_instruction}
6. Do NOT include a subject line, just the response body
7. If similar past responses are provided above, match their tone and style
{signature_instruction}{extra_section}

Response:"""

    start_time = time.time()

    if provider == 'goa':
        response_text, model_name = _call_goa(prompt)
    elif provider == 'gemini':
        response_text, model_name = _call_gemini(prompt)
    else:
        response_text, model_name = _call_ollama(prompt)

    generation_time = int((time.time() - start_time) * 1000)

    return {
        'generated_response': response_text,
        'model': model_name,
        'generation_time_ms': generation_time,
        'similar_emails_used': len(similar)
    }


def _call_ollama(prompt):
    """Call local Ollama model via OpenAI-compatible endpoint."""
    ollama_url = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    model = os.getenv('OLLAMA_MODEL', 'llama3.2:3b')

    body = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}]
    }

    response = requests.post(
        f"{ollama_url}/v1/chat/completions",
        json=body,
        timeout=120
    )

    if not response.ok:
        print(f"Ollama error {response.status_code}: {response.text}")

    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content'], model


def _call_goa(prompt):
    """Call GoA LLM cluster via OpenAI-compatible API."""
    endpoint = os.getenv('GOA_MODEL_ENDPOINT', '')
    api_path = os.getenv('GOA_API_PATH', '/v1/chat/completions')
    model = os.getenv('GOA_MODEL', 'openai/gpt-oss-120b')
    api_key = os.getenv('GOA_API_KEY', '')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    body = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'max_tokens': 1024
    }

    # TODO: Replace verify=False once GoA CA certificate is obtained and trusted
    response = requests.post(
        f"{endpoint}{api_path}",
        headers=headers,
        json=body,
        verify=False,
        timeout=60
    )
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content'], model


def _call_gemini(prompt):
    """Call Google Gemini via OpenAI-compatible API."""
    api_key = os.getenv('GEMINI_API_KEY', '')
    model = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    body = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}]
    }
    response = requests.post(
        'https://generativelanguage.googleapis.com/v1beta/openai/chat/completions',
        headers=headers,
        json=body,
        timeout=60
    )
    if not response.ok:
        print(f"Gemini API error {response.status_code}: {response.text}")
    response.raise_for_status()
    data = response.json()
    return data['choices'][0]['message']['content'], model


def analyze_edit_diff(generated_response, final_response, user_config=None):
    """
    Compare the AI-generated response against the user's edited version.
    Ask the LLM to extract reusable style preferences from the changes.
    Returns a list of preference strings (may be empty).
    """
    if not generated_response or not final_response:
        return []
    if generated_response.strip() == final_response.strip():
        return []

    provider = os.getenv('AI_PROVIDER', 'gemini')
    if user_config and user_config.get('ai_provider'):
        provider = user_config['ai_provider']

    prompt = f"""You are analyzing the difference between an AI-generated email response and the version the user actually sent.

AI-generated version:
{generated_response}

User's final version:
{final_response}

Identify up to 5 specific, reusable writing style preferences that explain what the user changed. Focus on style, tone, and structure — not content corrections specific to this email.

Examples of good preferences:
- "always start with a direct answer, not pleasantries"
- "avoid using the phrase 'I hope this email finds you well'"
- "use bullet points when listing multiple items"
- "keep responses to one paragraph unless the email has multiple questions"

Reply with ONLY a JSON array of short preference strings. No explanation. If no clear style patterns exist, return an empty array [].

Preferences:"""

    try:
        if provider == 'goa':
            raw, _ = _call_goa(prompt)
        elif provider == 'gemini':
            raw, _ = _call_gemini(prompt)
        else:
            raw, _ = _call_ollama(prompt)

        # Extract JSON array from response
        import json, re
        match = re.search(r'\[.*?\]', raw, re.DOTALL)
        if match:
            preferences = json.loads(match.group())
            return [p.strip() for p in preferences if isinstance(p, str) and p.strip()]
    except Exception as e:
        print(f"Edit diff analysis error (non-blocking): {e}")

    return []


def _build_context(similar_emails):
    """Build RAG context string from similar past emails."""
    if not similar_emails:
        return "No similar past emails found. Generate a general professional response."

    context = f"Here are {len(similar_emails)} similar past emails and how they were replied to. Match this style:\n\n"

    for i, email in enumerate(similar_emails, 1):
        context += f"--- Past Example {i} ---\n"
        context += f"Subject: {email['subject']}\n"
        original = email.get('original_body', '').strip()
        if original:
            context += f"Original email received: {original}\n"
        context += f"Reply sent: {email['reply']}\n\n"

    return context

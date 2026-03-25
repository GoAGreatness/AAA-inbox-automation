"""
Thread Parser - Splits an email body into the user's reply and the original message.

Outlook emails typically include the original message quoted below the reply,
separated by markers like "From:", "On [date] ... wrote:", or "> " lines.
This parser extracts both parts so the AI can understand the full exchange.
"""
import re


# Common quote markers used by Outlook and other email clients
QUOTE_PATTERNS = [
    # Outlook-style: "From: Name <email>"
    r'\n[-_]*\s*From:\s+.+',
    # Gmail/Outlook: "On Mon, Jan 1, 2026 ... wrote:"
    r'\nOn\s+.{5,80}wrote:\s*\n',
    # Forwarded message header
    r'\n[-_]*\s*Forwarded [Mm]essage\s*[-_]*',
    # Line of dashes/underscores (common Outlook separator)
    r'\n_{5,}',
    r'\n-{5,}',
    # "-----Original Message-----"
    r'\n[-]+\s*Original Message\s*[-]+',
]

COMPILED = [re.compile(p, re.IGNORECASE) for p in QUOTE_PATTERNS]


def parse_thread(body):
    """
    Split email body into (reply, original).
    Returns a dict with 'reply_body' and 'original_body'.
    If no quote marker is found, the entire body is treated as the reply.
    """
    if not body:
        return {'reply_body': '', 'original_body': ''}

    earliest_pos = len(body)

    for pattern in COMPILED:
        match = pattern.search(body)
        if match and match.start() < earliest_pos:
            earliest_pos = match.start()

    if earliest_pos == len(body):
        # No quote marker found — entire body is the reply
        return {
            'reply_body': body.strip(),
            'original_body': ''
        }

    reply = body[:earliest_pos].strip()
    original = body[earliest_pos:].strip()

    # Clean up leading quote markers/arrows from original
    original = re.sub(r'^[>\s]+', '', original, flags=re.MULTILINE)
    original = original.strip()

    return {
        'reply_body': reply,
        'original_body': original
    }

"""
Vector Service - Handles ChromaDB operations for semantic search.

Uses embeddings (numerical representations of text) to find similar
emails based on meaning, not just keywords.
This enables RAG (Retrieval Augmented Generation) - feeding relevant
past examples to the AI so it generates better responses.
"""
import chromadb
from chromadb.utils import embedding_functions
import os

# ChromaDB storage path
CHROMA_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'chroma_db')

# Initialize ChromaDB client (PersistentClient - data survives restarts)
client = chromadb.PersistentClient(path=CHROMA_PATH)

# Use default embedding function (all-MiniLM-L6-v2 model)
# This converts text into 384-dimensional vectors
embedding_fn = embedding_functions.DefaultEmbeddingFunction()

# Create/get collection for sent emails
sent_emails_collection = client.get_or_create_collection(
    name="sent_emails",
    embedding_function=embedding_fn
)


def add_sent_email(email_id, subject, original_body, reply_body):
    """
    Add a sent email to the vector store.
    Combines subject + original email + reply into one searchable document.
    """
    document = f"Subject: {subject}\nOriginal Email: {original_body}\nReply: {reply_body}"

    sent_emails_collection.add(
        documents=[document],
        ids=[str(email_id)],
        metadatas=[{
            "subject": subject,
            "reply_body": reply_body
        }]
    )


def find_similar_emails(subject, body, n_results=3):
    """
    Find similar past emails using semantic search.
    Returns the most similar sent emails based on meaning.
    """
    query = f"Subject: {subject}\nBody: {body}"

    # Check if collection has any documents
    if sent_emails_collection.count() == 0:
        return []

    results = sent_emails_collection.query(
        query_texts=[query],
        n_results=min(n_results, sent_emails_collection.count())
    )

    similar = []
    for i in range(len(results['ids'][0])):
        similar.append({
            'id': results['ids'][0][i],
            'document': results['documents'][0][i],
            'reply': results['metadatas'][0][i].get('reply_body', ''),
            'subject': results['metadatas'][0][i].get('subject', ''),
            'distance': results['distances'][0][i]
        })

    return similar


def get_collection_count():
    """Return how many emails are in the vector store."""
    return sent_emails_collection.count()

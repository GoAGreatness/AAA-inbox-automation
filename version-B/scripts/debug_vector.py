"""Debug ChromaDB to see what's stored."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.vector_service import sent_emails_collection, get_collection_count

print(f"Total documents: {get_collection_count()}")
print("-" * 50)

# Peek at what's stored
if get_collection_count() > 0:
    results = sent_emails_collection.peek(5)
    for i, doc_id in enumerate(results['ids']):
        print(f"ID: {doc_id}")
        print(f"Subject: {results['metadatas'][i].get('subject', 'N/A')}")
        print(f"Doc preview: {results['documents'][i][:100]}")
        print()

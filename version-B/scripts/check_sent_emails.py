"""
Inspect imported sent emails stored in ChromaDB.
Run from version-B root: python scripts/check_sent_emails.py
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.vector_service import sent_emails_collection

total = sent_emails_collection.count()
print(f"\nTotal sent emails in ChromaDB: {total}")

if total == 0:
    print("No emails found. Run the ImportSentEmails macro first.\n")
    sys.exit(0)

# Fetch all emails
results = sent_emails_collection.get(include=['documents', 'metadatas'])

ids = results['ids']
documents = results['documents']
metadatas = results['metadatas']

print(f"\n{'#':<5} {'ID':<10} {'Subject'}")
print("-" * 80)
for i, (eid, meta) in enumerate(zip(ids, metadatas)):
    subject = meta.get('subject', '(no subject)')
    print(f"{i+1:<5} {eid:<10} {subject}")

print()
choice = input("Enter # or ID to see full email (or press Enter to skip): ").strip()

if choice:
    # Allow selecting by row number or raw ID
    selected_doc = None
    selected_meta = None
    if choice.isdigit() and int(choice) <= len(ids):
        idx = int(choice) - 1
        selected_doc = documents[idx]
        selected_meta = metadatas[idx]
        selected_id = ids[idx]
    else:
        # Try matching by ID
        for i, eid in enumerate(ids):
            if eid == choice:
                selected_doc = documents[i]
                selected_meta = metadatas[i]
                selected_id = eid
                break

    if selected_doc:
        print(f"\nID:      {selected_id}")
        print(f"Subject: {selected_meta.get('subject', '(none)')}")
        print(f"\n--- Full Document ---\n{selected_doc}")
    else:
        print("Not found.")

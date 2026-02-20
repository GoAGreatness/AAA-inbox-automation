"""Reset imported email data (SQLite + ChromaDB) for a clean re-import."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from services.database_service import get_connection
from services.vector_service import client

# Clear sent_emails table in SQLite
conn = get_connection()
conn.execute('DELETE FROM sent_emails')
conn.commit()
conn.close()
print("SQLite sent_emails table cleared.")

# Delete and recreate ChromaDB collection
client.delete_collection("sent_emails")
print("ChromaDB collection deleted. Will recreate on next import.")
print("Ready for re-import!")

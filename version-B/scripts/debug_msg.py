"""Quick debug script to test parsing one .msg file."""
import os
import extract_msg

IMPORT_PATH = os.path.join(os.path.dirname(__file__), '..', 'backend', 'data', 'email-imports')

# Get first .msg file
msg_files = [f for f in os.listdir(IMPORT_PATH) if f.endswith('.msg')]
filepath = os.path.join(IMPORT_PATH, msg_files[0])

print(f"Testing: {msg_files[0]}")
print("-" * 50)

msg = extract_msg.Message(filepath)

# Print all available attributes
for attr in ['sender', 'senderName', 'sender_name', 'subject', 'body', 'date', 'to', 'cc']:
    try:
        val = getattr(msg, attr, 'NOT FOUND')
        if val and val != 'NOT FOUND':
            preview = str(val)[:100]
            print(f"{attr}: {preview}")
        else:
            print(f"{attr}: {val}")
    except Exception as e:
        print(f"{attr}: ERROR - {e}")

msg.close()

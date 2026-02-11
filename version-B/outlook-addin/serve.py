"""
Simple HTTPS server for Outlook Add-in development
Serves files from current directory on https://localhost:3000
"""
import http.server
import ssl
import os

# Server configuration
PORT = 3000
CERT_PATH = '../backend/data/ssl/cert.pem'
KEY_PATH = '../backend/data/ssl/key.pem'

# Create server
server_address = ('localhost', PORT)
httpd = http.server.HTTPServer(server_address, http.server.SimpleHTTPRequestHandler)

# Add SSL
ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
ssl_context.load_cert_chain(CERT_PATH, KEY_PATH)
httpd.socket = ssl_context.wrap_socket(httpd.socket, server_side=True)

print(f"🚀 Add-in server running on https://localhost:{PORT}")
print(f"📁 Serving files from: {os.getcwd()}")
print("Press Ctrl+C to stop")

# Start server
httpd.serve_forever()

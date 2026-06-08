"""
Minimal web server for the Docker lab target container.
Used to demonstrate: docker run, port publish, inspect.
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import os

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        msg = b"Hello from Meridian Docker Lab\n"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(msg)))
        self.end_headers()
        self.wfile.write(msg)

    def log_message(self, *args):
        pass  # quiet

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

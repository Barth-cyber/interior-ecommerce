import http.server
import socketserver
from urllib.parse import urlparse

PORT = 8080
HANDLER = http.server.SimpleHTTPRequestHandler


class InteriorHandler(HANDLER):
    """Custom handler that serves interior.html for root and directory paths."""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Redirect root and bare directory paths to interior.html
        if path == "/" or path == "":
            self.path = "/interior.html"

        return super().do_GET()


if __name__ == "__main__":
    with socketserver.TCPServer(("0.0.0.0", PORT), InteriorHandler) as httpd:
        print(f"Serving on http://0.0.0.0:{PORT}")
        httpd.serve_forever()

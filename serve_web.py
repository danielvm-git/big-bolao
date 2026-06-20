"""Static SPA server for web/dist/ — BigBase web process."""
import http.server, os, socketserver, sys

PORT = int(os.environ.get('PORT', 3000))
DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'dist')

print(f'Serving {DIRECTORY} on :{PORT}', flush=True)
print(f'index.html exists: {os.path.exists(os.path.join(DIRECTORY, "index.html"))}', flush=True)


class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        path = self.path.split('?')[0].lstrip('/')
        full = os.path.join(DIRECTORY, path)
        if not os.path.exists(full) or os.path.isdir(full):
            self.path = '/index.html'
        super().do_GET()

    def log_message(self, fmt, *args):
        pass  # silence access logs


socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(('0.0.0.0', PORT), SPAHandler) as httpd:
    httpd.serve_forever()

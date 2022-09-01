import http.server
import socketserver

PORT = 8000

class CVHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs, directory="./static")

    def do_GET(self):
        if self.path == '/':
            self.path = './resume.html'
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

def start_hosting():
    handler = CVHttpRequestHandler
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print("Server started at localhost:" + str(PORT))
        httpd.serve_forever()
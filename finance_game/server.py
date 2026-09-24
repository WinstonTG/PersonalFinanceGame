"""Serve the app and accept budget documents on a local classroom host."""
import argparse
import json
import sqlite3
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .documents import save_document


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, database, **kwargs):
        self.database = database
        super().__init__(*args, **kwargs)

    def respond(self, status, payload):
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/deployment.json':
            self.respond(200, {'submissions': True})
            return
        super().do_GET()

    def do_POST(self):
        if self.path != '/api/documents':
            self.respond(404, {'error': 'Not found'})
            return
        if self.headers.get('Content-Type', '').split(';')[0] != 'application/json':
            self.respond(415, {'error': 'Send a JSON budget document.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 65536:
                raise ValueError('Document must be between 1 and 65536 bytes.')
            document = json.loads(self.rfile.read(length))
            receipt = save_document(self.database, document)
        except (ValueError, UnicodeError) as error:
            self.respond(400, {'error': str(error)})
            return
        except sqlite3.Error:
            self.respond(503, {'error': 'Could not save your document. Please try again.'})
            return
        self.respond(201, receipt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8001)
    parser.add_argument('--bind', default='127.0.0.1')
    parser.add_argument('--database', default='submissions.sqlite3')
    parser.add_argument('--export', action='store_true', help='Print received documents as JSON; does not start server')
    args = parser.parse_args()
    if args.export:
        if not Path(args.database).is_file():
            parser.error('No submissions database exists yet.')
        with sqlite3.connect(args.database) as connection:
            rows = connection.execute('SELECT receipt, created, document FROM documents ORDER BY created').fetchall()
        print(json.dumps([{'receipt': r, 'submittedAt': t, 'document': json.loads(d)} for r, t, d in rows], indent=2))
        return
    web = Path(__file__).resolve().parents[1] / 'web'
    handler = partial(Handler, directory=str(web), database=args.database)
    with ThreadingHTTPServer((args.bind, args.port), handler) as server:
        print(f'Budget app: http://{args.bind}:{args.port}/budget.html', flush=True)
        server.serve_forever()


if __name__ == '__main__':
    main()

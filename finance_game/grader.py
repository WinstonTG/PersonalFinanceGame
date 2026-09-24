"""Private, local PDF grader. Run: python -m finance_game.grader"""
import argparse
from functools import partial
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import secrets
import sqlite3
import threading
from urllib.parse import parse_qs, urlsplit
import uuid
import webbrowser

from .grading import GradingSession, RULES_VERSION
from .pdf_budget import read_budget_pdf


class Store:
    def __init__(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.lock = threading.Lock()
        settings = directory / 'settings.json'
        if not settings.exists():
            fd = os.open(settings, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, 'w') as file:
                json.dump({'key': secrets.token_urlsafe(32), 'seed': secrets.randbelow(2147483646)+1}, file)
        config = json.loads(settings.read_text())
        self.key, self.seed = config['key'], config['seed']
        self.database = directory / 'grades.sqlite3'
        with sqlite3.connect(self.database) as connection:
            connection.execute('CREATE TABLE IF NOT EXISTS grades (id TEXT PRIMARY KEY, snapshot TEXT NOT NULL)')
        os.chmod(self.database, 0o600)

    def save(self, identifier, snapshot):
        with sqlite3.connect(self.database) as connection:
            connection.execute('INSERT OR REPLACE INTO grades VALUES (?,?)', (identifier, json.dumps(snapshot)))

    def load(self, identifier):
        with sqlite3.connect(self.database) as connection:
            row = connection.execute('SELECT snapshot FROM grades WHERE id=?', (identifier,)).fetchone()
        if not row:
            raise ValueError('Grading session not found.')
        return json.loads(row[0])

    def listing(self):
        with sqlite3.connect(self.database) as connection:
            rows = connection.execute('SELECT id,snapshot FROM grades ORDER BY rowid DESC').fetchall()
        return [{'id': identifier, 'name': (s := json.loads(raw))['document']['name'],
                 'title': s['document']['title'], 'completedMonths': s['completedMonths'],
                 'outdated': s.get('rulesVersion') != RULES_VERSION,
                 'score': s['final']['score'] if s['final'] and s.get('rulesVersion') == RULES_VERSION else None} for identifier, raw in rows]


class GraderHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, store, **kwargs):
        self.store = store
        super().__init__(*args, **kwargs)

    def log_message(self, *_args):
        pass  # Do not log access keys or student names.

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        super().end_headers()

    def json_response(self, status, value):
        data = json.dumps(value).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def authorized(self):
        if self.headers.get('Host') not in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'):
            return False
        cookie = SimpleCookie()
        try:
            cookie.load(self.headers.get('Cookie', ''))
            value = cookie['grader_access'].value if 'grader_access' in cookie else ''
            return secrets.compare_digest(value, self.store.key)
        except Exception:
            return False

    def do_GET(self):
        url = urlsplit(self.path)
        params = parse_qs(url.query)
        if url.path == '/login':
            key = params.get('key', [''])[0]
            if not secrets.compare_digest(key, self.store.key):
                self.json_response(401, {'error': 'Invalid grader access key.'})
                return
            self.send_response(303)
            self.send_header('Set-Cookie', f'grader_access={self.store.key}; HttpOnly; SameSite=Strict; Path=/')
            self.send_header('Location', '/')
            self.end_headers()
            return
        if not self.authorized():
            self.json_response(401, {'error': 'Private grader. Start python -m finance_game.grader on the grader computer to open an authenticated window.'})
            return
        try:
            if url.path == '/api/sessions':
                self.json_response(200, self.store.listing())
            elif url.path in ('/api/session', '/api/report'):
                snapshot = self.store.load(params.get('id', [''])[0])
                if url.path == '/api/report' and not snapshot['final']:
                    raise ValueError('Finish all 12 months before exporting the final report.')
                self.json_response(200, snapshot)
            elif url.path in ('/', '/index.html', '/grader.js', '/grader.css'):
                super().do_GET()
            else:
                self.json_response(404, {'error': 'Not found.'})
        except ValueError as error:
            self.json_response(400, {'error': str(error)})

    def do_POST(self):
        if not self.authorized() or self.headers.get('X-Grader-Request') != '1':
            self.json_response(401, {'error': 'Grader access required.'})
            return
        try:
            length = int(self.headers.get('Content-Length', '0'))
            if not 0 < length <= 5 * 1024 * 1024:
                raise ValueError('Upload must be between 1 byte and 5 MB.')
            data = self.rfile.read(length)
            with self.store.lock:
                if self.path == '/api/import':
                    document = read_budget_pdf(data)
                    identifier = str(uuid.uuid4())
                    snapshot = GradingSession(document, self.store.seed).snapshot()
                elif self.path == '/api/next':
                    payload = json.loads(data)
                    identifier = payload['id']
                    old = self.store.load(identifier)
                    if old.get('rulesVersion') != RULES_VERSION:
                        raise ValueError('This grade used older rules. Reimport the PDF to grade all months with the current fixed-rent rules.')
                    if payload.get('expectedMonth') != old['completedMonths']:
                        raise ValueError('This session has advanced. Select it again to refresh.')
                    session = GradingSession(old['document'], self.store.seed)
                    for i in range(old['completedMonths']):
                        session.advance(i)
                    snapshot = session.advance(old['completedMonths'])
                else:
                    raise ValueError('Unknown action.')
                self.store.save(identifier, snapshot)
            self.json_response(200, {'id': identifier, **snapshot})
        except (ValueError, KeyError, TypeError, UnicodeError) as error:
            self.json_response(400, {'error': str(error)})
        except sqlite3.Error:
            self.json_response(503, {'error': 'Could not save grading progress. Please retry.'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=8002)
    parser.add_argument('--data-dir', type=Path, default=Path.home() / '.personal-finance-grader')
    parser.add_argument('--no-open', action='store_true')
    args = parser.parse_args()
    store = Store(args.data_dir)
    handler = partial(GraderHandler, store=store, directory=str(Path(__file__).resolve().parents[1] / 'grader_web'))
    with ThreadingHTTPServer(('127.0.0.1', args.port), handler) as server:
        url = f'http://127.0.0.1:{server.server_port}/login?key={store.key}'
        print(f'Private grader listening on http://127.0.0.1:{server.server_port}', flush=True)
        print(f'Access link stored in {args.data_dir / "access.html"}', flush=True)
        access = args.data_dir / 'access.html'
        fd = os.open(access, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, 'w') as file:
            file.write(f'<!doctype html><title>Private grader access</title><a href="{url}">Open private grader</a>')
        if not args.no_open:
            webbrowser.open(url)
        server.serve_forever()


if __name__ == '__main__':
    main()

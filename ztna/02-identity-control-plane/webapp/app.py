#!/usr/bin/env python3
"""Lab 02 — Authorization Code flow callback app.

A deliberately small, readable OIDC confidential client. It lets you watch where
the password goes in the Authorization Code flow:
  - it redirects your BROWSER to Keycloak to log in (it never sees your password),
  - it CATCHES the redirect back and shows the one-time `code` it received,
  - it hands you the exact `curl` to redeem that code on the back channel, where
    the client_secret proves the app.

Run:  python3 webapp/app.py   (or `make webapp`), then open http://localhost:3000
Stop: Ctrl-C
"""
import html
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlencode, urlparse, parse_qs

KEYCLOAK_URL  = "http://localhost:8080"
REALM         = "corp"
CLIENT_ID     = "corp-app"
CLIENT_SECRET = "corp-app-secret"   # confidential client: the app proves itself with this
REDIRECT_URI  = "http://localhost:3000/callback"
PORT          = 3000

AUTH_URL  = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/auth"
TOKEN_URL = f"{KEYCLOAK_URL}/realms/{REALM}/protocol/openid-connect/token"


def build_auth_url(state):
    """Leg 1: the URL the app redirects the browser to. No credentials here — just
    who the app is (client_id), where to return (redirect_uri), what it wants
    (scope), and a CSRF token (state)."""
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "openid",
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


def build_exchange_curl(code):
    """Leg 4: the back-channel exchange, where client_secret proves the app. The
    browser never makes this call."""
    return (
        f"curl -s -X POST {TOKEN_URL} \\\n"
        f"  -d grant_type=authorization_code \\\n"
        f"  -d client_id={CLIENT_ID} \\\n"
        f"  -d client_secret={CLIENT_SECRET} \\\n"
        f"  -d redirect_uri={REDIRECT_URI} \\\n"
        f"  -d code={code} | python3 -m json.tool"
    )


def _page(title, body):
    return (f"<!doctype html><html><head><meta charset='utf-8'><title>{title}</title></head>"
            f"<body style=\"font-family:system-ui;max-width:44rem;margin:3rem auto;line-height:1.5\">"
            f"<h1>{title}</h1>{body}</body></html>")


def render_landing(state):
    url = build_auth_url(state)
    return _page(
        "Lab 02 — Authorization Code flow",
        f"<p>This app never sees your password. Clicking below sends your "
        f"<b>browser</b> to Keycloak to log in; the app only gets a one-time "
        f"<code>code</code> back.</p>"
        f"<p><a href=\"{url}\" style=\"display:inline-block;padding:.6rem 1rem;"
        f"background:#0b5;color:#fff;text-decoration:none;border-radius:6px\">"
        f"Log in with Keycloak</a></p>"
        f"<p style=\"color:#666\">The app will redirect your browser to:<br>"
        f"<code>{url}</code></p>")


def render_callback(query, expected_state):
    """Leg 3: what the app renders after Keycloak redirects back. `query` is the
    dict from parse_qs (values are lists). Handle error / missing-code / state
    mismatch before showing the code."""
    def one(key):
        vals = query.get(key)
        return vals[0] if vals else None

    if expected_state is None or one("state") != expected_state:
        return _page("State did not match — possible CSRF",
                     "<p>The <code>state</code> the app sent is not the one that "
                     "came back, so the app refuses to proceed. That is the CSRF "
                     "guard doing its job. Start again from "
                     "<a href='/'>the login page</a>.</p>")
    if one("error"):
        return _page("Keycloak returned an error",
                     f"<p><b>{html.escape(one('error'))}</b>: "
                     f"{html.escape(one('error_description') or '')}</p>"
                     f"<p>Start again from <a href='/'>the login page</a>.</p>")
    if not one("code"):
        return _page("No code in the callback",
                     "<p>This URL carried no <code>code</code>. Start at "
                     "<a href='/'>the login page</a>.</p>")

    code = one("code")
    curl = build_exchange_curl(html.escape(code))
    return _page(
        "The app received a code",
        f"<p>Keycloak sent your browser back here with a one-time authorization "
        f"<code>code</code>. Notice what the app got: <b>only a code</b> — your "
        f"password went to Keycloak, never here.</p>"
        f"<p><b>code</b> (single-use, expires ~60s): <code>{html.escape(code)}</code></p>"
        f"<p><b>state</b> (verified against what the app sent): "
        f"<code>{html.escape(one('state'))}</code></p>"
        f"<h3>Now redeem it yourself — Leg 4, the back channel</h3>"
        f"<p>Run this in your terminal. The <code>client_secret</code> is what "
        f"proves the app; the browser never makes this call.</p>"
        f"<pre style=\"background:#f4f4f4;padding:1rem;overflow-x:auto\">{curl}</pre>")


class Handler(BaseHTTPRequestHandler):
    state = None  # single-user lab: remember the last state we handed out

    def _send_html(self, html):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/callback":
            self._send_html(render_callback(parse_qs(parsed.query), Handler.state))
        elif parsed.path in ("/", ""):
            Handler.state = secrets.token_urlsafe(16)
            self._send_html(render_landing(Handler.state))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, *args):
        pass  # keep the lab console quiet


if __name__ == "__main__":
    print(f"Callback app on http://localhost:{PORT}  (Ctrl-C to stop)")
    HTTPServer(("localhost", PORT), Handler).serve_forever()

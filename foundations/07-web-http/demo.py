#!/usr/bin/env python3
"""
Web HTTP Lab — demonstrate HTTP mechanics programmatically.

Exercises each curl concept using Python's urllib so the demo
requires no extra tools inside the container.

Steps:
  1. GET request — read method, status, headers
  2. POST with form data — read echoed body
  3. Redirect — observe 301 Location header + auto-follow
  4. Cookie — set via /set-cookie, send back on /cookie-echo
  5. Role-check — show danger of trusting a client header

Usage: python3 demo.py
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
import http.cookiejar

BASE = "http://echo-server:8080"
DIVIDER = "─" * 64


def section(title: str) -> None:
    print(f"\n{DIVIDER}")
    print(f"[Step] {title}")
    print(DIVIDER)


def get(url: str, headers: dict | None = None,
        follow_redirects: bool = True,
        cookie_jar: http.cookiejar.CookieJar | None = None) -> tuple[int, dict, str]:
    req = urllib.request.Request(url, headers=headers or {})
    opener = urllib.request.build_opener()
    if not follow_redirects:
        opener = urllib.request.build_opener(
            urllib.request.HTTPRedirectHandler.__new__(urllib.request.HTTPRedirectHandler)
        )
        # Monkey-patch to not follow
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *args, **kwargs):
                return None
        opener = urllib.request.build_opener(NoRedirect())
    if cookie_jar is not None:
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(cookie_jar)
        )
    try:
        with opener.open(req, timeout=5) as r:
            body = r.read().decode()
            return r.status, dict(r.headers), body
    except urllib.error.HTTPError as e:
        body = e.read().decode() if e.fp else ""
        return e.code, dict(e.headers), body


def post_form(url: str, data: dict) -> tuple[int, dict, str]:
    import urllib.parse
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=encoded,
                                  headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, dict(r.headers), r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, {}, e.read().decode()


def pretty(body: str) -> str:
    try:
        return json.dumps(json.loads(body), indent=4)
    except Exception:
        return body


def demo_get() -> None:
    section("1 — GET request: method, status code, response headers")
    print()
    status, headers, body = get(f"{BASE}/")
    data = json.loads(body)
    print(f"  HTTP {status}  {data['method']} {data['url']}")
    print()
    print("  Security-relevant response headers:")
    interesting = ["Content-Type", "Server", "X-Frame-Options",
                   "Content-Security-Policy", "Strict-Transport-Security"]
    for h in interesting:
        val = headers.get(h, "— (not set)")
        note = "  ← missing in this dev server" if val == "— (not set)" else ""
        print(f"    {h}: {val}{note}")
    print()
    print("  curl equivalent:  curl -v http://echo-server:8080/")


def demo_post() -> None:
    section("2 — POST with form data: server echoes the body back")
    print()
    status, _, body = post_form(f"{BASE}/", {"username": "jsmith", "role": "admin"})
    data = json.loads(body)
    print(f"  HTTP {status}")
    print(f"  Form data echoed: {json.dumps(data.get('form', {}), indent=4)}")
    print()
    print("  curl equivalent:")
    print("    curl -X POST http://echo-server:8080/ \\")
    print("         -d 'username=jsmith&role=admin'")
    print()
    print("  The server trusts form fields at face value unless it validates them.")
    print("  Sending role=admin as a form field is a client-side assertion.")


def demo_redirect() -> None:
    section("3 — Redirect: observe 301 Location, then follow")
    print()

    # Step A: without following
    status_a, headers_a, _ = get(f"{BASE}/redirect-me", follow_redirects=False)
    location = headers_a.get("Location", "—")
    print(f"  Without following:  HTTP {status_a}  Location: {location}")

    # Step B: following
    status_b, _, body_b = get(f"{BASE}/redirect-me", follow_redirects=True)
    data_b = json.loads(body_b)
    print(f"  After following:    HTTP {status_b}  landed at {data_b.get('url','?')}")
    print()
    print("  curl equivalent:")
    print("    curl -v http://echo-server:8080/redirect-me         # see 301")
    print("    curl -L http://echo-server:8080/redirect-me         # follow it")


def demo_cookies() -> None:
    section("4 — Cookies: set via /set-cookie, carry to /cookie-echo")
    print()

    jar = http.cookiejar.CookieJar()

    # Request 1: get the cookie
    status_a, headers_a, body_a = get(f"{BASE}/set-cookie", cookie_jar=jar)
    data_a = json.loads(body_a)
    print(f"  Request 1 — GET /set-cookie  HTTP {status_a}")
    set_cookie_header = headers_a.get("Set-Cookie", "—")
    print(f"    Set-Cookie: {set_cookie_header}")

    # Request 2: send it back
    status_b, _, body_b = get(f"{BASE}/cookie-echo", cookie_jar=jar)
    data_b = json.loads(body_b)
    print(f"\n  Request 2 — GET /cookie-echo  HTTP {status_b}")
    print(f"    Cookies received by server: {json.dumps(data_b.get('cookies_received', {}))}")
    print(f"    Note: {data_b.get('note', '')}")
    print()
    print("  curl equivalent:")
    print("    curl -c /tmp/jar.txt http://echo-server:8080/set-cookie")
    print("    curl -b /tmp/jar.txt http://echo-server:8080/cookie-echo")


def demo_role_header() -> None:
    section("5 — Danger: trusting a client-controlled header (X-Role)")
    print()

    # Normal user
    status_a, _, body_a = get(f"{BASE}/role-check")
    data_a = json.loads(body_a)
    print(f"  Without X-Role header:      role={data_a['role']!r}  → {data_a['data']!r}")

    # Attacker sets X-Role: admin
    status_b, _, body_b = get(f"{BASE}/role-check", headers={"X-Role": "admin"})
    data_b = json.loads(body_b)
    print(f"  With X-Role: admin header:  role={data_b['role']!r}  → {data_b['data']!r}")
    print()
    print(f"  Warning: {data_b.get('warning', '')}")
    print()
    print("  curl equivalent:")
    print("    curl http://echo-server:8080/role-check")
    print("    curl -H 'X-Role: admin' http://echo-server:8080/role-check")
    print()
    print("  Why role=admin is a problem: the server trusted a value the client")
    print("  supplied, not a value it generated and verified. This is the root")
    print("  cause of the IDOR in Track 01, module 07.")


def main() -> None:
    print("=" * 64)
    print("Meridian Financial — Web HTTP Lab Demo")
    print("=" * 64)
    print()
    print("Demonstrates HTTP mechanics using a local echo server.")
    print("Each step shows what curl does and why it matters for security.")

    try:
        demo_get()
        demo_post()
        demo_redirect()
        demo_cookies()
        demo_role_header()
    except Exception as e:
        print(f"\n  [Error] {e}")
        print("  Make sure the server is running: make up")
        raise SystemExit(1)

    print(f"\n{'=' * 64}")
    print("Deliverable: http-notes.md with an annotated request/response pair")
    print("and one sentence on why trusting client-supplied role=admin is a problem.")
    print(f"{'=' * 64}\n")


if __name__ == "__main__":
    main()
